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


router = APIRouter(tags=["enrollments"])

@router.post("/enrollments")
async def create_enrollment(data: EnrollmentCreate, request: Request):
    user = await get_current_user(request)
    
    course = await db.courses.find_one({"_id": ObjectId(data.course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Admin doing bulk enrollment (moved from client_manager to admin)
    if user["role"] == "admin" and data.user_ids:
        enrolled = []
        for uid in data.user_ids:
            existing = await db.enrollments.find_one({"course_id": data.course_id, "user_id": uid})
            if not existing:
                await db.enrollments.insert_one({
                    "course_id": data.course_id,
                    "user_id": uid,
                    "enrolled_by": user["id"],
                    "completed": False,
                    "score": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                enrolled.append(uid)
                
                # Send enrollment email to each user
                enrolled_user = await db.users.find_one({"_id": ObjectId(uid)})
                if enrolled_user:
                    await send_enrollment_email(
                        enrolled_user.get("email"),
                        enrolled_user.get("name"),
                        course.get("title"),
                        data.course_id
                    )
        return {"message": f"Enrolled {len(enrolled)} users", "enrolled": enrolled}
    
    # Self enrollment
    existing = await db.enrollments.find_one({"course_id": data.course_id, "user_id": user["id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
    
    # Check if paid course
    if not course.get("is_free") and course.get("price", 0) > 0:
        # Check if payment completed
        payment = await db.payment_transactions.find_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "payment_status": "paid"
        })
        if not payment:
            raise HTTPException(status_code=402, detail="Payment required")
    
    await db.enrollments.insert_one({
        "course_id": data.course_id,
        "user_id": user["id"],
        "completed": False,
        "score": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send enrollment email
    await send_enrollment_email(user["email"], user["name"], course.get("title"), data.course_id)
    
    return {"message": "Enrolled successfully"}

@router.get("/enrollments/my")
async def get_my_enrollments(request: Request):
    user = await get_current_user(request)
    enrollments = await db.enrollments.find({"user_id": user["id"]}).to_list(100)
    
    # Batch fetch courses to avoid N+1 queries
    course_ids = [ObjectId(e["course_id"]) for e in enrollments]
    courses = await db.courses.find(
        {"_id": {"$in": course_ids}}, 
        {"_id": 1, "title": 1, "thumbnail_url": 1}
    ).to_list(100)
    course_map = {str(c["_id"]): c for c in courses}
    
    result = []
    for e in enrollments:
        course = course_map.get(e["course_id"])
        if course:
            result.append({
                "id": str(e.get("_id", "")),
                "course_id": e["course_id"],
                "course_title": course.get("title"),
                "course_thumbnail": course.get("thumbnail_url"),
                "completed": e.get("completed", False),
                "score": e.get("score", 0),
                "created_at": e.get("created_at")
            })
    return result

@router.get("/enrollments/course/{course_id}")
async def get_course_enrollments(course_id: str, request: Request):
    user = await require_roles("admin", "client_manager")(request)
    enrollments = await db.enrollments.find({"course_id": course_id}).to_list(1000)
    
    # Batch fetch users to avoid N+1 queries
    user_ids = [ObjectId(e["user_id"]) for e in enrollments]
    users = await db.users.find(
        {"_id": {"$in": user_ids}}, 
        {"_id": 1, "name": 1, "email": 1}
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
                "completed_at": e.get("completed_at")
            })
    return result
