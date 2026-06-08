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


router = APIRouter(tags=["chat"])

@router.post("/chat")
async def chat_with_ai(data: ChatMessageCreate, request: Request):
    user = await get_current_user(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    # Get course context
    course = await db.courses.find_one({"_id": ObjectId(data.course_id)})
    course_context = f"Course: {course.get('title', 'Unknown')}\nDescription: {course.get('description', '')}" if course else ""
    
    # Get recent chat history
    history = await db.chat_messages.find({
        "course_id": data.course_id,
        "user_id": user["id"]
    }).sort("created_at", -1).limit(10).to_list(10)
    history.reverse()
    
    messages = [
        {"role": "system", "content": f"You are a helpful course assistant. {course_context}\n\nHelp students understand the course material and answer their questions."}
    ]
    for h in history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": data.message})
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        ai_response = response.choices[0].message.content
        
        # Save messages
        await db.chat_messages.insert_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "role": "user",
            "content": data.message,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        await db.chat_messages.insert_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "role": "assistant",
            "content": ai_response,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"response": ai_response}
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail="AI service error")

@router.get("/chat/{course_id}/history")
async def get_chat_history(course_id: str, request: Request):
    user = await get_current_user(request)
    history = await db.chat_messages.find({
        "course_id": course_id,
        "user_id": user["id"]
    }).sort("created_at", 1).to_list(100)
    return [{"role": h.get("role"), "content": h.get("content"), "created_at": h.get("created_at")} for h in history]
