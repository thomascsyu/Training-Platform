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


router = APIRouter(tags=["courses"])

@router.post("/courses")
async def create_course(data: CourseCreate, request: Request):
    user = await require_roles("admin")(request)
    # Validate language
    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {SUPPORTED_LANGUAGES}")
    
    course_doc = {
        "title": data.title,
        "description": data.description,
        "thumbnail_url": data.thumbnail_url,
        "video_url": data.video_url,
        "video_type": data.video_type,
        "price": data.price,
        "is_free": data.is_free,
        "is_private": data.is_private,
        "passing_score": data.passing_score,
        "materials": data.materials,
        "language": data.language,
        "category": data.category,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.courses.insert_one(course_doc)
    return {"id": str(result.inserted_id), **{k: v for k, v in course_doc.items() if k != "_id"}}

@router.get("/languages")
async def get_languages():
    """Get supported languages"""
    return {"languages": SUPPORTED_LANGUAGES, "names": LANGUAGE_NAMES}

@router.get("/courses")
async def get_courses(
    request: Request, 
    include_private: bool = False,
    language: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    user = await get_optional_user(request)
    is_authenticated = user is not None
    
    query = {}
    if not is_authenticated or (user and user["role"] == "student"):
        query["is_private"] = False
    elif include_private and user and user["role"] in ["admin", "client_manager"]:
        pass  # Show all courses
    else:
        query["is_private"] = False
    
    # Language filter
    if language and language in SUPPORTED_LANGUAGES:
        query["language"] = language
    
    # Category filter
    if category:
        query["category"] = category
    
    # Search filter
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    courses = await db.courses.find(query, {"_id": 1, "title": 1, "description": 1, "thumbnail_url": 1, "price": 1, "is_free": 1, "is_private": 1, "language": 1, "category": 1, "created_at": 1}).to_list(100)
    return [{"id": str(c["_id"]), **{k: v for k, v in c.items() if k != "_id"}} for c in courses]

@router.get("/courses/{course_id}")
async def get_course(course_id: str, request: Request):
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if private course
    if course.get("is_private"):
        user = await get_optional_user(request)
        if not user:
            raise HTTPException(status_code=403, detail="Private course - authentication required")
        if user["role"] == "student":
            enrollment = await db.enrollments.find_one({
                "course_id": course_id,
                "user_id": user["id"],
            })
            if not enrollment:
                raise HTTPException(status_code=403, detail="Not enrolled in this course")
    
    # Get lessons
    lessons = await db.lessons.find({"course_id": course_id}, {"_id": 1, "title": 1, "description": 1, "video_url": 1, "video_type": 1, "order": 1, "materials": 1}).sort("order", 1).to_list(100)
    
    # Get quizzes
    quizzes = await db.quizzes.find({"course_id": course_id}, {"_id": 1, "title": 1}).to_list(100)
    
    return {
        "id": str(course["_id"]),
        **{k: v for k, v in course.items() if k != "_id"},
        "lessons": [{"id": str(l["_id"]), **{k: v for k, v in l.items() if k != "_id"}} for l in lessons],
        "quizzes": [{"id": str(q["_id"]), **{k: v for k, v in q.items() if k != "_id"}} for q in quizzes]
    }

@router.put("/courses/{course_id}")
async def update_course(course_id: str, data: CourseUpdate, request: Request):
    user = await require_roles("admin")(request)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course updated"}

@router.delete("/courses/{course_id}")
async def delete_course(course_id: str, request: Request):
    user = await require_roles("admin")(request)
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    await delete_course_related_data(course_id)
    return {"message": "Course deleted"}
