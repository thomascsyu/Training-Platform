from bson import ObjectId
from fastapi import APIRouter, Request

from auth_utils import get_current_user, require_roles
from database import db
from progress_utils import get_bulk_lesson_progress

router = APIRouter(tags=["stats"])


@router.get("/stats/admin")
async def get_admin_stats(request: Request):
    await require_roles("admin")(request)

    total_courses = await db.courses.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_enrollments = await db.enrollments.count_documents({})
    completed_courses = await db.enrollments.count_documents({"completed": True})

    return {
        "total_courses": total_courses,
        "total_students": total_students,
        "total_enrollments": total_enrollments,
        "completed_courses": completed_courses,
    }


@router.get("/stats/admin/analytics")
async def get_admin_analytics(request: Request):
    await require_roles("admin")(request)

    total_courses = await db.courses.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_enrollments = await db.enrollments.count_documents({})
    completed_enrollments = await db.enrollments.count_documents({"completed": True})
    total_certificates = await db.certificates.count_documents({})
    total_lesson_completions = await db.lesson_progress.count_documents({"completed": True})

    completion_rate = (
        round((completed_enrollments / total_enrollments) * 100, 1)
        if total_enrollments > 0
        else 0
    )

    top_courses = []
    async for row in db.enrollments.aggregate([
        {"$group": {"_id": "$course_id", "enrollments": {"$sum": 1}, "completed": {"$sum": {"$cond": ["$completed", 1, 0]}}}},
        {"$sort": {"enrollments": -1}},
        {"$limit": 5},
    ]):
        course = await db.courses.find_one({"_id": ObjectId(row["_id"])}, {"title": 1})
        if course:
            top_courses.append({
                "course_id": row["_id"],
                "course_title": course.get("title"),
                "enrollments": row["enrollments"],
                "completed": row["completed"],
                "completion_rate": round((row["completed"] / row["enrollments"]) * 100, 1) if row["enrollments"] else 0,
            })

    quiz_stats = {"total_attempts": 0, "passed": 0, "failed": 0}
    async for row in db.quiz_attempts.aggregate([
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "passed": {"$sum": {"$cond": ["$passed", 1, 0]}},
        }},
    ]):
        quiz_stats["total_attempts"] = row["total"]
        quiz_stats["passed"] = row["passed"]
        quiz_stats["failed"] = row["total"] - row["passed"]

    avg_lesson_progress = 0
    enrollments = await db.enrollments.find({}, {"user_id": 1, "course_id": 1}).to_list(5000)
    if enrollments:
        progress_sum = 0
        for e in enrollments:
            bulk = await get_bulk_lesson_progress([e["user_id"]], e["course_id"])
            progress_sum += bulk.get(e["user_id"], {}).get("progress_percent", 0)
        avg_lesson_progress = round(progress_sum / len(enrollments), 1)

    return {
        "overview": {
            "total_courses": total_courses,
            "total_students": total_students,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "completion_rate": completion_rate,
            "total_certificates": total_certificates,
            "total_lesson_completions": total_lesson_completions,
            "avg_lesson_progress_percent": avg_lesson_progress,
        },
        "quiz_stats": quiz_stats,
        "top_courses": top_courses,
    }


@router.get("/stats/student")
async def get_student_stats(request: Request):
    user = await get_current_user(request)

    enrollments = await db.enrollments.count_documents({"user_id": user["id"]})
    completed = await db.enrollments.count_documents({"user_id": user["id"], "completed": True})
    certificates = await db.certificates.count_documents({"user_id": user["id"]})
    lessons_completed = await db.lesson_progress.count_documents(
        {"user_id": user["id"], "completed": True}
    )

    return {
        "enrolled_courses": enrollments,
        "completed_courses": completed,
        "certificates": certificates,
        "lessons_completed": lessons_completed,
    }
