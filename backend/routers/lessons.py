from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user, require_roles
from database import db
from db_utils import parse_object_id
from models import LessonCreate, LessonUpdate
from progress_utils import require_enrollment

router = APIRouter(tags=["lessons"])


@router.post("/lessons")
async def create_lesson(data: LessonCreate, request: Request):
    await require_roles("admin")(request)
    lesson_doc = {
        "course_id": data.course_id,
        "title": data.title,
        "description": data.description,
        "video_url": data.video_url,
        "video_type": data.video_type,
        "order": data.order,
        "materials": data.materials,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.lessons.insert_one(lesson_doc)
    return {
        "id": str(result.inserted_id),
        **{k: v for k, v in lesson_doc.items() if k != "_id"},
    }


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, request: Request):
    user = await get_current_user(request)
    lesson = await db.lessons.find_one({"_id": parse_object_id(lesson_id, "lesson")})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user["role"] == "student":
        await require_enrollment(user["id"], lesson["course_id"])
    return {
        "id": str(lesson["_id"]),
        **{k: v for k, v in lesson.items() if k != "_id"},
    }


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, data: LessonUpdate, request: Request):
    await require_roles("admin")(request)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await db.lessons.update_one(
        {"_id": parse_object_id(lesson_id, "lesson")},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson updated"}


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, request: Request):
    await require_roles("admin")(request)
    result = await db.lessons.delete_one(
        {"_id": parse_object_id(lesson_id, "lesson")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted"}
