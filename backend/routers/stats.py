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


router = APIRouter(tags=["stats"])

@router.get("/stats/admin")
async def get_admin_stats(request: Request):
    user = await require_roles("admin")(request)
    
    total_courses = await db.courses.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_enrollments = await db.enrollments.count_documents({})
    completed_courses = await db.enrollments.count_documents({"completed": True})
    
    return {
        "total_courses": total_courses,
        "total_students": total_students,
        "total_enrollments": total_enrollments,
        "completed_courses": completed_courses
    }

@router.get("/stats/student")
async def get_student_stats(request: Request):
    user = await get_current_user(request)
    
    enrollments = await db.enrollments.count_documents({"user_id": user["id"]})
    completed = await db.enrollments.count_documents({"user_id": user["id"], "completed": True})
    certificates = await db.certificates.count_documents({"user_id": user["id"]})
    
    return {
        "enrolled_courses": enrollments,
        "completed_courses": completed,
        "certificates": certificates
    }
