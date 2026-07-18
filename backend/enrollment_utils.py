import asyncio
from datetime import datetime, timezone
from typing import Iterable, Optional

from database import db
from email_service import send_enrollment_email

# Roles that should be treated as students for company training assignments.
STUDENT_ROLES = {"student", "client_manager"}


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
    users = [u for u in users if u]
    if not users:
        return []

    user_ids = [str(u["_id"]) for u in users]
    existing = await db.enrollments.find(
        {"course_id": course_id, "user_id": {"$in": user_ids}},
        {"user_id": 1},
    ).to_list(len(user_ids))
    already_enrolled = {e["user_id"] for e in existing}

    new_users = [u for u in users if str(u["_id"]) not in already_enrolled]
    if not new_users:
        return []

    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for user in new_users:
        doc = {
            "course_id": course_id,
            "user_id": str(user["_id"]),
            "completed": False,
            "score": 0,
            "created_at": now,
        }
        if enrolled_by:
            doc["enrolled_by"] = enrolled_by
        if source:
            doc["source"] = source
        docs.append(doc)

    await db.enrollments.insert_many(docs)
    await asyncio.gather(*[
        send_enrollment_email(
            user.get("email"), user.get("name"), course.get("title"), course_id
        )
        for user in new_users
    ])

    return [str(u["_id"]) for u in new_users]


async def enroll_company_students_in_course(
    course: dict,
    course_id: str,
    company_ids: list[str],
    enrolled_by: Optional[str] = None,
) -> list[str]:
    if not company_ids:
        return []

    users = await db.users.find({
        "role": {"$in": list(STUDENT_ROLES)},
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
    if user.get("role") not in STUDENT_ROLES or not company_id:
        return []

    courses = await db.courses.find({"company_ids": company_id}).to_list(1000)
    if not courses:
        return []

    user_id = str(user["_id"])
    course_ids = [str(c["_id"]) for c in courses]
    existing = await db.enrollments.find(
        {"course_id": {"$in": course_ids}, "user_id": user_id},
        {"course_id": 1},
    ).to_list(len(course_ids))
    already_enrolled = {e["course_id"] for e in existing}

    new_courses = [c for c in courses if str(c["_id"]) not in already_enrolled]
    if not new_courses:
        return []

    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "course_id": str(c["_id"]),
            "user_id": user_id,
            "completed": False,
            "score": 0,
            "created_at": now,
            "source": "company_assignment",
        }
        for c in new_courses
    ]
    await db.enrollments.insert_many(docs)
    await asyncio.gather(*[
        send_enrollment_email(user.get("email"), user.get("name"), c.get("title"), str(c["_id"]))
        for c in new_courses
    ])

    return [str(c["_id"]) for c in new_courses]
