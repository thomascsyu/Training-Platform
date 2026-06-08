import uuid
from datetime import datetime, timezone
from typing import Optional

import stripe
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

import jwt
from config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DEEPSEEK_API_KEY,
    JWT_ALGORITHM,
    JWT_SECRET,
    LANGUAGE_NAMES,
    REQUIRE_STRIPE_WEBHOOK_SECRET,
    STRIPE_API_KEY,
    STRIPE_WEBHOOK_SECRET,
    SUPPORTED_LANGUAGES,
    logger,
)
from database import db
from models import (
    CertificateCustomize,
    ChatMessageCreate,
    CourseCreate,
    CourseUpdate,
    EnrollmentCreate,
    ForumPostCreate,
    LessonCreate,
    LessonUpdate,
    PaymentCreate,
    QuizAttemptCreate,
    QuizCreate,
    TranslateCourseRequest,
    TranslateQuizRequest,
    TranslateRequest,
    UserCreate,
    UserLogin,
)
from auth_utils import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_optional_user,
    hash_password,
    require_roles,
    set_auth_cookies,
    verify_password,
)
from course_utils import delete_course_related_data
from email_service import (
    send_certificate_email,
    send_enrollment_email,
    send_progress_email,
)

deepseek_client = None


router = APIRouter(tags=["lessons"])

@router.post("/lessons")
async def create_lesson(data: LessonCreate, request: Request):
    user = await require_roles("admin")(request)
    lesson_doc = {
        "course_id": data.course_id,
        "title": data.title,
        "description": data.description,
        "video_url": data.video_url,
        "video_type": data.video_type,
        "order": data.order,
        "materials": data.materials,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.lessons.insert_one(lesson_doc)
    return {"id": str(result.inserted_id), **{k: v for k, v in lesson_doc.items() if k != "_id"}}

@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, request: Request):
    lesson = await db.lessons.find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"id": str(lesson["_id"]), **{k: v for k, v in lesson.items() if k != "_id"}}

@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, data: LessonUpdate, request: Request):
    user = await require_roles("admin")(request)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await db.lessons.update_one({"_id": ObjectId(lesson_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson updated"}

@router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, request: Request):
    user = await require_roles("admin")(request)
    result = await db.lessons.delete_one({"_id": ObjectId(lesson_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted"}
