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


router = APIRouter(tags=["forums"])

@router.post("/forums/posts")
async def create_forum_post(data: ForumPostCreate, request: Request):
    user = await get_current_user(request)
    post_doc = {
        "course_id": data.course_id,
        "content": data.content,
        "parent_id": data.parent_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.forum_posts.insert_one(post_doc)
    return {"id": str(result.inserted_id), **{k: v for k, v in post_doc.items() if k != "_id"}}

@router.get("/forums/{course_id}")
async def get_forum_posts(course_id: str, request: Request):
    user = await get_current_user(request)
    posts = await db.forum_posts.find({"course_id": course_id, "parent_id": None}).sort("created_at", -1).to_list(100)
    
    result = []
    for p in posts:
        replies = await db.forum_posts.find({"parent_id": str(p["_id"])}).sort("created_at", 1).to_list(50)
        result.append({
            "id": str(p["_id"]),
            **{k: v for k, v in p.items() if k != "_id"},
            "replies": [{"id": str(r["_id"]), **{k: v for k, v in r.items() if k != "_id"}} for r in replies]
        })
    return result

@router.delete("/forums/posts/{post_id}")
async def delete_forum_post(post_id: str, request: Request):
    user = await get_current_user(request)
    post = await db.forum_posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.forum_posts.delete_one({"_id": ObjectId(post_id)})
    await db.forum_posts.delete_many({"parent_id": post_id})
    return {"message": "Post deleted"}
