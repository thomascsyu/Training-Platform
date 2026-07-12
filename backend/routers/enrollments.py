from datetime import datetime, timezone

import stripe
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user, require_admin_or_manager
from config import STRIPE_API_KEY, logger
from database import db
from db_utils import parse_object_id
from enrollment_utils import enroll_user_in_course, enroll_users_in_course
from models import EnrollmentCreate
from progress_utils import get_user_lesson_progress_by_courses

router = APIRouter(tags=["enrollments"])


@router.post("/enrollments")
async def create_enrollment(data: EnrollmentCreate, request: Request):
    user = await get_current_user(request)

    course = await db.courses.find_one(
        {"_id": parse_object_id(data.course_id, "course")}
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if user["role"] == "admin" and data.user_ids:
        enrolled_users = []
        for uid in data.user_ids:
            enrolled_user = await db.users.find_one(
                {"_id": parse_object_id(uid, "user")}
            )
            if enrolled_user:
                enrolled_users.append(enrolled_user)
        enrolled = await enroll_users_in_course(
            course,
            data.course_id,
            enrolled_users,
            enrolled_by=user["id"],
        )
        return {"message": f"Enrolled {len(enrolled)} users", "enrolled": enrolled}

    existing = await db.enrollments.find_one({
        "course_id": data.course_id,
        "user_id": user["id"],
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")

    current_user = await db.users.find_one({"_id": ObjectId(user["id"])})
    if course.get("company_ids"):
        if not current_user or current_user.get("company_id") not in course["company_ids"]:
            raise HTTPException(status_code=403, detail="Course is not assigned to your company")

    if not course.get("is_free") and course.get("price", 0) > 0:
        payment = await db.payment_transactions.find_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "payment_status": "paid",
        })
        if not payment:
            raise HTTPException(status_code=402, detail="Payment required")

    await enroll_user_in_course(
        course,
        data.course_id,
        current_user,
    )

    return {"message": "Enrolled successfully"}


@router.get("/enrollments/my")
async def get_my_enrollments(request: Request):
    user = await get_current_user(request)
    enrollments = await db.enrollments.find({"user_id": user["id"]}).to_list(100)

    course_ids = [e["course_id"] for e in enrollments]
    courses = await db.courses.find(
        {"_id": {"$in": [parse_object_id(cid, "course") for cid in course_ids]}},
        {"_id": 1, "title": 1, "thumbnail_url": 1},
    ).to_list(100)
    course_map = {str(c["_id"]): c for c in courses}

    progress_map = await get_user_lesson_progress_by_courses(user["id"], course_ids)

    result = []
    for e in enrollments:
        course = course_map.get(e["course_id"])
        if course:
            progress = progress_map.get(e["course_id"], {})
            result.append({
                "id": str(e.get("_id", "")),
                "course_id": e["course_id"],
                "course_title": course.get("title"),
                "course_thumbnail": course.get("thumbnail_url"),
                "completed": e.get("completed", False),
                "score": e.get("score", 0),
                "created_at": e.get("created_at"),
                "lessons_total": progress.get("total_lessons", 0),
                "lessons_completed": progress.get("completed_lessons", 0),
                "progress_percent": progress.get("progress_percent", 0),
            })
    return result


@router.get("/enrollments/course/{course_id}")
async def get_course_enrollments(course_id: str, request: Request):
    user = await require_admin_or_manager(request)
    parse_object_id(course_id, "course")

    if user["role"] == "client_manager":
        course = await db.courses.find_one(
            {"_id": parse_object_id(course_id, "course")},
            {"_id": 1, "company_ids": 1},
        )
        if not course or user["company_id"] not in course.get("company_ids", []):
            raise HTTPException(status_code=403, detail="Not authorized to view this course")

    enrollments = await db.enrollments.find({"course_id": course_id}).to_list(1000)

    if user["role"] == "client_manager":
        company_id = user["company_id"]
        user_ids = list({e["user_id"] for e in enrollments})
        if user_ids:
            company_users = await db.users.find(
                {
                    "_id": {"$in": [ObjectId(uid) for uid in user_ids]},
                    "company_id": company_id,
                },
                {"_id": 1, "name": 1, "email": 1},
            ).to_list(1000)
            user_map = {str(u["_id"]): u for u in company_users}
        else:
            user_map = {}
    else:
        user_ids = [ObjectId(e["user_id"]) for e in enrollments]
        users = await db.users.find(
            {"_id": {"$in": user_ids}},
            {"_id": 1, "name": 1, "email": 1},
        ).to_list(1000)
        user_map = {str(u["_id"]): u for u in users}

    result = []
    for e in enrollments:
        student = user_map.get(e["user_id"])
        if student:
            result.append({
                "user_id": e["user_id"],
                "user_name": student.get("name"),
                "user_email": student.get("email"),
                "completed": e.get("completed", False),
                "score": e.get("score", 0),
                "created_at": e.get("created_at"),
                "completed_at": e.get("completed_at"),
            })
    return result


@router.delete("/enrollments/{course_id}")
async def delete_enrollment(
    course_id: str,
    request: Request,
    user_id: str | None = None,
    refund: bool = False,
):
    actor = await get_current_user(request)
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    target_user_id = actor["id"]
    if user_id and user_id != actor["id"]:
        if actor["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can unenroll other users")
        parse_object_id(user_id, "user")
        target_user_id = user_id

    if actor["role"] == "student" and target_user_id == actor["id"] and not course.get("is_free", True):
        raise HTTPException(
            status_code=403,
            detail="Paid course unenrollment requires admin support",
        )

    enrollment = await db.enrollments.find_one({"course_id": course_id, "user_id": target_user_id})
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    refund_info = None
    if refund:
        if actor["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can issue refunds")
        if not STRIPE_API_KEY:
            raise HTTPException(status_code=503, detail="Payment service not configured")
        transaction = await db.payment_transactions.find_one(
            {
                "course_id": course_id,
                "user_id": target_user_id,
                "payment_status": "paid",
            },
            sort=[("created_at", -1)],
        )
        if not transaction:
            raise HTTPException(status_code=404, detail="No paid transaction found to refund")
        try:
            session = stripe.checkout.Session.retrieve(transaction["session_id"])
            payment_intent = getattr(session, "payment_intent", None)
            if not payment_intent:
                raise HTTPException(status_code=400, detail="No refundable payment intent found")
            refund_resp = stripe.Refund.create(payment_intent=payment_intent)
            refunded_at = datetime.now(timezone.utc).isoformat()
            await db.payment_transactions.update_one(
                {"_id": transaction["_id"]},
                {
                    "$set": {
                        "payment_status": "refunded",
                        "refunded_at": refunded_at,
                        "updated_at": refunded_at,
                        "refund_id": refund_resp.id,
                    }
                },
            )
            refund_info = {"status": "refunded", "refund_id": refund_resp.id}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Refund failed for course=%s user=%s: %s", course_id, target_user_id, exc)
            raise HTTPException(status_code=502, detail="Refund failed") from exc

    user_posts = await db.forum_posts.find(
        {"course_id": course_id, "user_id": target_user_id},
        {"_id": 1},
    ).to_list(1000)
    post_ids = [str(post["_id"]) for post in user_posts]
    if post_ids:
        await db.forum_posts.delete_many({"course_id": course_id, "parent_id": {"$in": post_ids}})
    await db.forum_posts.delete_many({"course_id": course_id, "user_id": target_user_id})
    await db.chat_messages.delete_many({"course_id": course_id, "user_id": target_user_id})
    await db.lesson_progress.delete_many({"course_id": course_id, "user_id": target_user_id})
    await db.quiz_attempts.delete_many({"course_id": course_id, "user_id": target_user_id})
    await db.certificates.delete_many({"course_id": course_id, "user_id": target_user_id})
    await db.enrollments.delete_one({"_id": enrollment["_id"]})

    return {
        "message": "Enrollment removed",
        "course_id": course_id,
        "user_id": target_user_id,
        "refund": refund_info,
    }
