import uuid
from datetime import datetime, timezone

from certificate_utils import apply_template_to_certificate, resolve_certificate_template
from database import db
from db_utils import parse_object_id
from email_service import send_certificate_email


async def get_completion_state(user_id: str, course_id: str) -> dict:
    total_lessons = await db.lessons.count_documents({"course_id": course_id})
    completed_lessons = await db.lesson_progress.count_documents(
        {"course_id": course_id, "user_id": user_id, "completed": True}
    )
    attempt = await db.quiz_attempts.find_one(
        {"course_id": course_id, "user_id": user_id, "passed": True},
        sort=[("score", -1), ("created_at", -1)],
    )
    lessons_complete = total_lessons == 0 or completed_lessons >= total_lessons
    quiz_passed = attempt is not None
    return {
        "course_id": course_id,
        "user_id": user_id,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "lessons_complete": lessons_complete,
        "quiz_passed": quiz_passed,
        "best_quiz_score": attempt.get("score") if attempt else None,
        "eligible_for_completion": lessons_complete and quiz_passed,
    }


async def finalize_completion_if_eligible(user_id: str, course_id: str) -> dict:
    state = await get_completion_state(user_id, course_id)
    if not state["eligible_for_completion"]:
        return state

    now = datetime.now(timezone.utc).isoformat()
    score = state.get("best_quiz_score") or 0
    await db.enrollments.update_one(
        {"course_id": course_id, "user_id": user_id},
        {
            "$set": {
                "completed": True,
                "completed_at": now,
                "score": score,
            }
        },
    )

    user = await db.users.find_one({"_id": parse_object_id(user_id, "user")})
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    course_title = course.get("title") if course else "Course"

    existing_cert = await db.certificates.find_one({"course_id": course_id, "user_id": user_id})
    if not existing_cert:
        cert_doc = {
            "course_id": course_id,
            "user_id": user_id,
            "user_name": user.get("name") if user else "Learner",
            "course_title": course_title,
            "score": score,
            "issued_at": now,
            "certificate_id": str(uuid.uuid4())[:8].upper(),
        }
        template = await resolve_certificate_template(db)
        apply_template_to_certificate(cert_doc, template)
        await db.certificates.insert_one(cert_doc)
        if user and user.get("email"):
            await send_certificate_email(
                user["email"],
                user.get("name", "Learner"),
                course_title,
                cert_doc["certificate_id"],
                score,
            )
    else:
        await db.certificates.update_one(
            {"_id": existing_cert["_id"]},
            {"$set": {"score": score, "issued_at": now}},
        )

    return state
