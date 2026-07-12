from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user
from completion_utils import finalize_completion_if_eligible
from database import db
from db_utils import parse_object_id
from models import LessonProgressUpdate
from progress_utils import (
    get_course_lesson_progress,
    require_enrollment,
    upsert_lesson_progress,
)

router = APIRouter(tags=["progress"])


@router.get("/progress/course/{course_id}")
async def get_course_progress(course_id: str, request: Request):
    user = await get_current_user(request)
    await require_enrollment(user["id"], course_id)
    return await get_course_lesson_progress(user["id"], course_id)


@router.patch("/progress/lessons/{lesson_id}")
async def update_lesson_progress(
    lesson_id: str, data: LessonProgressUpdate, request: Request
):
    user = await get_current_user(request)
    lesson = await db.lessons.find_one({"_id": parse_object_id(lesson_id, "lesson")})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course_id = lesson["course_id"]
    await require_enrollment(user["id"], course_id)

    await upsert_lesson_progress(
        user["id"],
        course_id,
        lesson_id,
        watch_percent=data.watch_percent,
        last_position_sec=data.last_position_sec,
        completed=True if data.completed else None,
    )
    await finalize_completion_if_eligible(user["id"], course_id)
    return await get_course_lesson_progress(user["id"], course_id)


@router.post("/progress/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, request: Request):
    user = await get_current_user(request)
    lesson = await db.lessons.find_one({"_id": parse_object_id(lesson_id, "lesson")})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course_id = lesson["course_id"]
    await require_enrollment(user["id"], course_id)

    await upsert_lesson_progress(
        user["id"], course_id, lesson_id, completed=True, watch_percent=100
    )
    await finalize_completion_if_eligible(user["id"], course_id)
    return await get_course_lesson_progress(user["id"], course_id)
