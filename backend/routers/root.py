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


router = APIRouter(tags=["root"])

@router.get("/")
async def root():
    return {"message": "LearnHub API", "version": "1.0.0"}
