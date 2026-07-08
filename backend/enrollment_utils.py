from datetime import datetime, timezone
from typing import Iterable, Optional

from database import db
from email_service import send_enrollment_email


async def enroll_user_in_course(
    course: dict,
    course_id: str,
    user: dict,
    enrolled_by: Optional[str] = None,
    source: Optional[str] = None,
) -> bool:
    if not user:
        return False

    existing = await db.enrollments.find_one({
        "course_id": course_id,
        "user_id": str(user["_id"]),
    })
    if existing:
        return False

    enrollment_doc = {
        "course_id": course_id,
        "user_id": str(user["_id"]),
        "completed": False,
        "score": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if enrolled_by:
        enrollment_doc["enrolled_by"] = enrolled_by
    if source:
        enrollment_doc["source"] = source

    await db.enrollments.insert_one(enrollment_doc)
    await send_enrollment_email(
        user.get("email"),
        user.get("name"),
        course.get("title"),
        course_id,
    )
    return True


async def enroll_users_in_course(
    course: dict,
    course_id: str,
    users: Iterable[dict],
    enrolled_by: Optional[str] = None,
    source: Optional[str] = None,
) -> list[str]:
    enrolled = []
    for user in users:
        if await enroll_user_in_course(course, course_id, user, enrolled_by, source):
            enrolled.append(str(user["_id"]))
    return enrolled


async def enroll_company_students_in_course(
    course: dict,
    course_id: str,
    company_ids: list[str],
    enrolled_by: Optional[str] = None,
) -> list[str]:
    if not company_ids:
        return []

    users = await db.users.find({
        "role": "student",
        "company_id": {"$in": company_ids},
    }).to_list(10000)
    return await enroll_users_in_course(
        course,
        course_id,
        users,
        enrolled_by=enrolled_by,
        source="company_assignment",
    )


async def enroll_user_in_assigned_company_courses(user: dict) -> list[str]:
    company_id = user.get("company_id")
    if user.get("role") != "student" or not company_id:
        return []

    courses = await db.courses.find({"company_ids": company_id}).to_list(1000)
    enrolled_course_ids = []
    for course in courses:
        course_id = str(course["_id"])
        if await enroll_user_in_course(
            course,
            course_id,
            user,
            source="company_assignment",
        ):
            enrolled_course_ids.append(course_id)
    return enrolled_course_ids
