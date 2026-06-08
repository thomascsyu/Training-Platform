from datetime import datetime, timezone

from bson import ObjectId

from database import db


async def get_course_lesson_progress(user_id: str, course_id: str) -> dict:
    """Return lesson-level progress summary for a user in a course."""
    lessons = await db.lessons.find({"course_id": course_id}).sort("order", 1).to_list(200)
    progress_docs = await db.lesson_progress.find(
        {"user_id": user_id, "course_id": course_id}
    ).to_list(200)
    progress_map = {p["lesson_id"]: p for p in progress_docs}

    lesson_items = []
    completed_count = 0
    total_watch = 0

    for lesson in lessons:
        lesson_id = str(lesson["_id"])
        prog = progress_map.get(lesson_id, {})
        completed = prog.get("completed", False)
        watch_percent = prog.get("watch_percent", 0)
        if completed:
            completed_count += 1
        total_watch += watch_percent
        lesson_items.append({
            "lesson_id": lesson_id,
            "title": lesson.get("title"),
            "order": lesson.get("order", 0),
            "completed": completed,
            "watch_percent": watch_percent,
            "last_position_sec": prog.get("last_position_sec", 0),
            "completed_at": prog.get("completed_at"),
            "updated_at": prog.get("updated_at"),
        })

    total = len(lessons)
    progress_percent = round((completed_count / total) * 100) if total > 0 else 0
    avg_watch = round(total_watch / total) if total > 0 else 0

    return {
        "course_id": course_id,
        "total_lessons": total,
        "completed_lessons": completed_count,
        "progress_percent": progress_percent,
        "average_watch_percent": avg_watch,
        "lessons": lesson_items,
    }


async def get_bulk_lesson_progress(user_ids: list[str], course_id: str) -> dict[str, dict]:
    """Return progress_percent per user for a course (batch)."""
    if not user_ids:
        return {}

    total_lessons = await db.lessons.count_documents({"course_id": course_id})
    if total_lessons == 0:
        return {uid: {"lessons_completed": 0, "total_lessons": 0, "progress_percent": 0} for uid in user_ids}

    pipeline = [
        {"$match": {"course_id": course_id, "user_id": {"$in": user_ids}, "completed": True}},
        {"$group": {"_id": "$user_id", "completed": {"$sum": 1}}},
    ]
    completed_by_user = {}
    async for row in db.lesson_progress.aggregate(pipeline):
        completed_by_user[row["_id"]] = row["completed"]

    result = {}
    for uid in user_ids:
        completed = completed_by_user.get(uid, 0)
        result[uid] = {
            "lessons_completed": completed,
            "total_lessons": total_lessons,
            "progress_percent": round((completed / total_lessons) * 100),
        }
    return result


async def get_user_lesson_progress_by_courses(
    user_id: str, course_ids: list[str]
) -> dict[str, dict]:
    """Return lesson progress summary per course for a single user (batch)."""
    if not course_ids:
        return {}

    total_by_course: dict[str, int] = {}
    async for row in db.lessons.aggregate([
        {"$match": {"course_id": {"$in": course_ids}}},
        {"$group": {"_id": "$course_id", "total": {"$sum": 1}}},
    ]):
        total_by_course[row["_id"]] = row["total"]

    completed_by_course: dict[str, int] = {}
    async for row in db.lesson_progress.aggregate([
        {
            "$match": {
                "user_id": user_id,
                "course_id": {"$in": course_ids},
                "completed": True,
            }
        },
        {"$group": {"_id": "$course_id", "completed": {"$sum": 1}}},
    ]):
        completed_by_course[row["_id"]] = row["completed"]

    result = {}
    for cid in course_ids:
        total = total_by_course.get(cid, 0)
        completed = completed_by_course.get(cid, 0)
        result[cid] = {
            "total_lessons": total,
            "completed_lessons": completed,
            "progress_percent": round((completed / total) * 100) if total > 0 else 0,
        }
    return result


async def require_enrollment(user_id: str, course_id: str):
    enrollment = await db.enrollments.find_one({"course_id": course_id, "user_id": user_id})
    if not enrollment:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
    return enrollment


async def upsert_lesson_progress(
    user_id: str,
    course_id: str,
    lesson_id: str,
    *,
    completed: bool | None = None,
    watch_percent: int | None = None,
    last_position_sec: int | None = None,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.lesson_progress.find_one({
        "user_id": user_id,
        "course_id": course_id,
        "lesson_id": lesson_id,
    })

    update: dict = {"updated_at": now}
    if watch_percent is not None:
        update["watch_percent"] = max(0, min(100, watch_percent))
    if last_position_sec is not None:
        update["last_position_sec"] = max(0, last_position_sec)
    if completed is True:
        update["completed"] = True
        update["completed_at"] = now
        if "watch_percent" not in update:
            update["watch_percent"] = 100

    if existing:
        await db.lesson_progress.update_one({"_id": existing["_id"]}, {"$set": update})
    else:
        doc = {
            "user_id": user_id,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "completed": completed or False,
            "watch_percent": update.get("watch_percent", 0),
            "last_position_sec": update.get("last_position_sec", 0),
            "created_at": now,
            **update,
        }
        if doc["completed"] and "completed_at" not in doc:
            doc["completed_at"] = now
        await db.lesson_progress.insert_one(doc)

    return (await db.lesson_progress.find_one({
        "user_id": user_id,
        "course_id": course_id,
        "lesson_id": lesson_id,
    })) or {}
