from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import secrets
import httpx
from openai import OpenAI
import stripe

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"

# Deepseek Config
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
deepseek_client = None
if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# Stripe Config
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

# Brevo Email Config
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@learnhub.com")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "LearnHub")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

app = FastAPI(title="LearnHub - Course Platform")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ PYDANTIC MODELS ============

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "student"  # admin, client_manager, student

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

# Supported languages
SUPPORTED_LANGUAGES = ["en", "zh-TW", "zh-CN", "ja", "ko"]
LANGUAGE_NAMES = {
    "en": "English",
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어"
}

class CourseCreate(BaseModel):
    title: str
    description: str
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str = "youtube"  # youtube or vimeo
    price: float = 0.0
    is_free: bool = True
    is_private: bool = False
    passing_score: int = 70
    materials: List[Dict[str, str]] = []  # [{name, url}]
    language: str = "en"  # en, zh-TW, zh-CN, ja, ko
    category: Optional[str] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = None
    price: Optional[float] = None
    is_free: Optional[bool] = None
    is_private: Optional[bool] = None
    passing_score: Optional[int] = None
    materials: Optional[List[Dict[str, str]]] = None
    language: Optional[str] = None
    category: Optional[str] = None

class LessonCreate(BaseModel):
    course_id: str
    title: str
    description: str
    video_url: Optional[str] = None
    video_type: str = "youtube"
    order: int = 0
    materials: List[Dict[str, str]] = []

class QuizCreate(BaseModel):
    course_id: str
    title: str
    questions: List[Dict[str, Any]]  # [{question, options[], correct_answer}]

class QuizAttemptCreate(BaseModel):
    quiz_id: str
    answers: List[int]  # index of selected options

class EnrollmentCreate(BaseModel):
    course_id: str
    user_ids: List[str] = []  # For bulk enrollment by client manager

class ForumPostCreate(BaseModel):
    course_id: str
    content: str
    parent_id: Optional[str] = None

class ChatMessageCreate(BaseModel):
    course_id: str
    message: str

class CertificateCustomize(BaseModel):
    course_id: str
    template: str = "default"
    primary_color: str = "#002FA7"
    secondary_color: str = "#0A0B10"

class PaymentCreate(BaseModel):
    course_id: str
    origin_url: str

# ============ HELPER FUNCTIONS ============

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id, 
        "email": email, 
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id, 
        "exp": datetime.now(timezone.utc) + timedelta(days=7), 
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_roles(*roles):
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# ============ BREVO EMAIL SERVICE ============

async def send_brevo_email(to_email: str, to_name: str, subject: str, html_content: str, text_content: str = None):
    """Send email using Brevo API"""
    if not BREVO_API_KEY:
        logger.warning("Brevo API key not configured, skipping email")
        return None
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content
    }
    
    if text_content:
        payload["textContent"] = text_content
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return response.json()
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return None

async def send_enrollment_email(user_email: str, user_name: str, course_title: str, course_id: str):
    """Send course enrollment notification email"""
    subject = f"Welcome to {course_title}! - LearnHub"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🎓 You're Enrolled!</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    Congratulations! You have been successfully enrolled in:
                </p>
                <div style="background-color: #F4F5F7; padding: 20px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #002FA7;">
                    <h2 style="color: #0A0B10; margin: 0 0 10px 0; font-size: 18px;">{course_title}</h2>
                </div>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    Start your learning journey now! Access your course materials, take quizzes, and earn your certificate.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/courses/{course_id}" 
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: 500; display: inline-block;">
                        Start Learning
                    </a>
                </div>
                <p style="color: #94A3B8; font-size: 12px; text-align: center;">
                    If you have any questions, feel free to reach out to our support team.
                </p>
            </div>
            <div style="background-color: #0A0B10; padding: 20px; text-align: center;">
                <p style="color: #64748B; font-size: 12px; margin: 0;">© 2026 LearnHub. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)

async def send_progress_email(user_email: str, user_name: str, course_title: str, progress: int, course_id: str):
    """Send course progress update email"""
    subject = f"Progress Update: {progress}% Complete - {course_title}"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">📊 Progress Update</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    Great progress on <strong>{course_title}</strong>!
                </p>
                <div style="background-color: #F4F5F7; padding: 20px; border-radius: 4px; margin: 20px 0;">
                    <p style="color: #0A0B10; font-size: 14px; margin: 0 0 10px 0;">Your Progress:</p>
                    <div style="background-color: #E2E8F0; height: 24px; border-radius: 12px; overflow: hidden;">
                        <div style="background-color: #002FA7; height: 100%; width: {progress}%; display: flex; align-items: center; justify-content: center;">
                            <span style="color: white; font-size: 12px; font-weight: bold;">{progress}%</span>
                        </div>
                    </div>
                </div>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    Keep going! You're doing amazing work.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/courses/{course_id}" 
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: 500; display: inline-block;">
                        Continue Learning
                    </a>
                </div>
            </div>
            <div style="background-color: #0A0B10; padding: 20px; text-align: center;">
                <p style="color: #64748B; font-size: 12px; margin: 0;">© 2026 LearnHub. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)

async def send_certificate_email(user_email: str, user_name: str, course_title: str, certificate_id: str, score: int):
    """Send certificate completion notification email"""
    subject = f"🎓 Congratulations! Certificate for {course_title}"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(135deg, #002FA7 0%, #0A0B10 100%); padding: 40px; text-align: center;">
                <div style="font-size: 60px; margin-bottom: 10px;">🎓</div>
                <h1 style="color: white; margin: 0; font-size: 28px;">Congratulations!</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">You've earned a certificate</p>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Dear {user_name},</p>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6;">
                    You have successfully completed <strong>{course_title}</strong> with a score of <strong>{score}%</strong>!
                </p>
                <div style="background: linear-gradient(135deg, rgba(0,47,167,0.1) 0%, rgba(10,11,16,0.1) 100%); padding: 25px; border-radius: 4px; margin: 20px 0; text-align: center; border: 2px solid #002FA7;">
                    <p style="color: #64748B; font-size: 12px; margin: 0 0 5px 0; text-transform: uppercase; letter-spacing: 2px;">Certificate of Completion</p>
                    <h2 style="color: #0A0B10; margin: 0 0 10px 0; font-size: 20px;">{course_title}</h2>
                    <p style="color: #002FA7; font-size: 18px; margin: 0; font-weight: 500;">{user_name}</p>
                    <p style="color: #94A3B8; font-size: 12px; margin: 15px 0 0 0;">Certificate ID: {certificate_id}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/certificates" 
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; font-weight: 500; display: inline-block;">
                        View Your Certificate
                    </a>
                </div>
                <p style="color: #64748B; font-size: 14px; line-height: 1.6; text-align: center;">
                    Share your achievement on LinkedIn, Twitter, or Facebook!
                </p>
            </div>
            <div style="background-color: #0A0B10; padding: 20px; text-align: center;">
                <p style="color: #64748B; font-size: 12px; margin: 0;">© 2026 LearnHub. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)

# ============ AUTH ENDPOINTS ============

@api_router.post("/auth/register")
async def register(data: UserCreate, response: Request):
    from starlette.responses import JSONResponse
    email = data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(data.password)
    user_doc = {
        "email": email,
        "password_hash": hashed,
        "name": data.name,
        "role": data.role if data.role in ["student", "client_manager"] else "student",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email, user_doc["role"])
    refresh_token = create_refresh_token(user_id)
    
    resp = JSONResponse(content={
        "id": user_id,
        "email": email,
        "name": data.name,
        "role": user_doc["role"]
    })
    resp.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    resp.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return resp

@api_router.post("/auth/login")
async def login(data: UserLogin):
    from starlette.responses import JSONResponse
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email, user["role"])
    refresh_token = create_refresh_token(user_id)
    
    resp = JSONResponse(content={
        "id": user_id,
        "email": email,
        "name": user["name"],
        "role": user["role"]
    })
    resp.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    resp.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return resp

@api_router.post("/auth/logout")
async def logout():
    from starlette.responses import JSONResponse
    resp = JSONResponse(content={"message": "Logged out"})
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")
    return resp

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

# ============ COURSE ENDPOINTS ============

@api_router.post("/courses")
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

@api_router.get("/languages")
async def get_languages():
    """Get supported languages"""
    return {"languages": SUPPORTED_LANGUAGES, "names": LANGUAGE_NAMES}

@api_router.get("/courses")
async def get_courses(
    request: Request, 
    include_private: bool = False,
    language: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    try:
        user = await get_current_user(request)
        is_authenticated = True
    except:
        user = None
        is_authenticated = False
    
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

@api_router.get("/courses/{course_id}")
async def get_course(course_id: str, request: Request):
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if private course
    if course.get("is_private"):
        try:
            user = await get_current_user(request)
            # Check enrollment or admin/client_manager
            if user["role"] == "student":
                enrollment = await db.enrollments.find_one({
                    "course_id": course_id,
                    "user_id": user["id"]
                })
                if not enrollment:
                    raise HTTPException(status_code=403, detail="Not enrolled in this course")
        except HTTPException:
            raise
        except:
            raise HTTPException(status_code=403, detail="Private course - authentication required")
    
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

@api_router.put("/courses/{course_id}")
async def update_course(course_id: str, data: CourseUpdate, request: Request):
    user = await require_roles("admin")(request)
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.courses.update_one({"_id": ObjectId(course_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course updated"}

@api_router.delete("/courses/{course_id}")
async def delete_course(course_id: str, request: Request):
    user = await require_roles("admin")(request)
    result = await db.courses.delete_one({"_id": ObjectId(course_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    # Delete related data
    await db.lessons.delete_many({"course_id": course_id})
    await db.quizzes.delete_many({"course_id": course_id})
    await db.enrollments.delete_many({"course_id": course_id})
    return {"message": "Course deleted"}

# ============ LESSON ENDPOINTS ============

@api_router.post("/lessons")
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

@api_router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str, request: Request):
    lesson = await db.lessons.find_one({"_id": ObjectId(lesson_id)})
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"id": str(lesson["_id"]), **{k: v for k, v in lesson.items() if k != "_id"}}

@api_router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: str, data: dict, request: Request):
    user = await require_roles("admin")(request)
    result = await db.lessons.update_one({"_id": ObjectId(lesson_id)}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson updated"}

@api_router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, request: Request):
    user = await require_roles("admin")(request)
    result = await db.lessons.delete_one({"_id": ObjectId(lesson_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": "Lesson deleted"}

# ============ QUIZ ENDPOINTS ============

@api_router.post("/quizzes")
async def create_quiz(data: QuizCreate, request: Request):
    user = await require_roles("admin")(request)
    quiz_doc = {
        "course_id": data.course_id,
        "title": data.title,
        "questions": data.questions,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.quizzes.insert_one(quiz_doc)
    return {"id": str(result.inserted_id), **{k: v for k, v in quiz_doc.items() if k != "_id"}}

@api_router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Don't send correct answers to students
    quiz_data = {"id": str(quiz["_id"]), **{k: v for k, v in quiz.items() if k != "_id"}}
    if user["role"] == "student":
        for q in quiz_data.get("questions", []):
            q.pop("correct_answer", None)
    return quiz_data

@api_router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, data: QuizAttemptCreate, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Calculate score
    questions = quiz.get("questions", [])
    correct = 0
    for i, q in enumerate(questions):
        if i < len(data.answers) and data.answers[i] == q.get("correct_answer"):
            correct += 1
    
    score = int((correct / len(questions)) * 100) if questions else 0
    
    # Get course passing score
    course = await db.courses.find_one({"_id": ObjectId(quiz["course_id"])})
    passing_score = course.get("passing_score", 70) if course else 70
    passed = score >= passing_score
    
    # Save attempt
    attempt_doc = {
        "quiz_id": quiz_id,
        "course_id": quiz["course_id"],
        "user_id": user["id"],
        "answers": data.answers,
        "score": score,
        "passed": passed,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.quiz_attempts.insert_one(attempt_doc)
    
    # Update enrollment progress if passed
    if passed:
        await db.enrollments.update_one(
            {"course_id": quiz["course_id"], "user_id": user["id"]},
            {"$set": {"completed": True, "completed_at": datetime.now(timezone.utc).isoformat(), "score": score}}
        )
        
        # Generate certificate and send email
        cert_doc = {
            "course_id": quiz["course_id"],
            "user_id": user["id"],
            "user_name": user["name"],
            "course_title": course.get("title") if course else "Course",
            "score": score,
            "template": "default",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "certificate_id": str(uuid.uuid4())[:8].upper()
        }
        await db.certificates.insert_one(cert_doc)
        
        # Send certificate email
        await send_certificate_email(
            user["email"],
            user["name"],
            course.get("title") if course else "Course",
            cert_doc["certificate_id"],
            score
        )
    
    return {"score": score, "passed": passed, "passing_score": passing_score, "correct": correct, "total": len(questions)}

# ============ ENROLLMENT ENDPOINTS ============

@api_router.post("/enrollments")
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

@api_router.get("/enrollments/my")
async def get_my_enrollments(request: Request):
    user = await get_current_user(request)
    enrollments = await db.enrollments.find({"user_id": user["id"]}).to_list(100)
    
    result = []
    for e in enrollments:
        course = await db.courses.find_one({"_id": ObjectId(e["course_id"])}, {"_id": 1, "title": 1, "thumbnail_url": 1})
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

@api_router.get("/enrollments/course/{course_id}")
async def get_course_enrollments(course_id: str, request: Request):
    user = await require_roles("admin", "client_manager")(request)
    enrollments = await db.enrollments.find({"course_id": course_id}).to_list(1000)
    
    result = []
    for e in enrollments:
        student = await db.users.find_one({"_id": ObjectId(e["user_id"])}, {"_id": 1, "name": 1, "email": 1})
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

# ============ GROUP PROGRESS TRACKING (Client Manager) ============

@api_router.get("/groups/overview")
async def get_groups_overview(request: Request):
    """Get overview of all courses with group progress - for Client Manager"""
    user = await require_roles("admin", "client_manager")(request)
    
    # Get all courses
    courses = await db.courses.find({}, {"_id": 1, "title": 1, "language": 1, "thumbnail_url": 1}).to_list(100)
    
    result = []
    for course in courses:
        course_id = str(course["_id"])
        
        # Get enrollment stats
        total_enrolled = await db.enrollments.count_documents({"course_id": course_id})
        completed = await db.enrollments.count_documents({"course_id": course_id, "completed": True})
        in_progress = total_enrolled - completed
        
        # Calculate average score of completed students
        completed_enrollments = await db.enrollments.find({"course_id": course_id, "completed": True}, {"score": 1}).to_list(1000)
        avg_score = 0
        if completed_enrollments:
            scores = [e.get("score", 0) for e in completed_enrollments]
            avg_score = round(sum(scores) / len(scores), 1)
        
        # Calculate completion rate
        completion_rate = round((completed / total_enrolled * 100), 1) if total_enrolled > 0 else 0
        
        result.append({
            "course_id": course_id,
            "course_title": course.get("title"),
            "language": course.get("language", "en"),
            "thumbnail_url": course.get("thumbnail_url"),
            "total_enrolled": total_enrolled,
            "completed": completed,
            "in_progress": in_progress,
            "completion_rate": completion_rate,
            "average_score": avg_score
        })
    
    return result

@api_router.get("/groups/course/{course_id}/progress")
async def get_course_group_progress(course_id: str, request: Request):
    """Get detailed progress of all students in a course - for Client Manager"""
    user = await require_roles("admin", "client_manager")(request)
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollments = await db.enrollments.find({"course_id": course_id}).to_list(1000)
    
    students = []
    for e in enrollments:
        student = await db.users.find_one({"_id": ObjectId(e["user_id"])}, {"_id": 1, "name": 1, "email": 1})
        if student:
            # Get quiz attempts for this student in this course
            quiz_attempts = await db.quiz_attempts.find({
                "course_id": course_id,
                "user_id": e["user_id"]
            }).sort("created_at", -1).to_list(10)
            
            last_activity = e.get("completed_at") or e.get("created_at")
            if quiz_attempts:
                last_activity = quiz_attempts[0].get("created_at", last_activity)
            
            students.append({
                "user_id": e["user_id"],
                "user_name": student.get("name"),
                "user_email": student.get("email"),
                "enrolled_at": e.get("created_at"),
                "completed": e.get("completed", False),
                "completed_at": e.get("completed_at"),
                "score": e.get("score", 0),
                "quiz_attempts": len(quiz_attempts),
                "last_activity": last_activity,
                "status": "completed" if e.get("completed") else "in_progress"
            })
    
    # Sort by completion status (completed first, then by score)
    students.sort(key=lambda x: (not x["completed"], -x["score"]))
    
    # Calculate summary stats
    total = len(students)
    completed_count = sum(1 for s in students if s["completed"])
    avg_score = round(sum(s["score"] for s in students if s["completed"]) / completed_count, 1) if completed_count > 0 else 0
    
    return {
        "course_id": course_id,
        "course_title": course.get("title"),
        "language": course.get("language", "en"),
        "passing_score": course.get("passing_score", 70),
        "summary": {
            "total_enrolled": total,
            "completed": completed_count,
            "in_progress": total - completed_count,
            "completion_rate": round((completed_count / total * 100), 1) if total > 0 else 0,
            "average_score": avg_score
        },
        "students": students
    }

@api_router.get("/groups/student/{user_id}/progress")
async def get_student_progress(user_id: str, request: Request):
    """Get detailed progress of a specific student across all courses - for Client Manager"""
    user = await require_roles("admin", "client_manager")(request)
    
    student = await db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "name": 1, "email": 1})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    enrollments = await db.enrollments.find({"user_id": user_id}).to_list(100)
    
    courses = []
    for e in enrollments:
        course = await db.courses.find_one({"_id": ObjectId(e["course_id"])})
        if course:
            # Get quiz attempts
            quiz_attempts = await db.quiz_attempts.find({
                "course_id": e["course_id"],
                "user_id": user_id
            }).sort("created_at", -1).to_list(10)
            
            # Get certificate if completed
            certificate = None
            if e.get("completed"):
                cert = await db.certificates.find_one({"course_id": e["course_id"], "user_id": user_id})
                if cert:
                    certificate = {
                        "certificate_id": cert.get("certificate_id"),
                        "issued_at": cert.get("issued_at")
                    }
            
            courses.append({
                "course_id": e["course_id"],
                "course_title": course.get("title"),
                "language": course.get("language", "en"),
                "enrolled_at": e.get("created_at"),
                "completed": e.get("completed", False),
                "completed_at": e.get("completed_at"),
                "score": e.get("score", 0),
                "passing_score": course.get("passing_score", 70),
                "quiz_attempts": len(quiz_attempts),
                "certificate": certificate
            })
    
    # Calculate overall stats
    total_courses = len(courses)
    completed_courses = sum(1 for c in courses if c["completed"])
    avg_score = round(sum(c["score"] for c in courses if c["completed"]) / completed_courses, 1) if completed_courses > 0 else 0
    
    return {
        "user_id": user_id,
        "user_name": student.get("name"),
        "user_email": student.get("email"),
        "summary": {
            "total_enrolled": total_courses,
            "completed": completed_courses,
            "in_progress": total_courses - completed_courses,
            "completion_rate": round((completed_courses / total_courses * 100), 1) if total_courses > 0 else 0,
            "average_score": avg_score
        },
        "courses": courses
    }

# ============ CERTIFICATE ENDPOINTS ============

@api_router.get("/certificates/my")
async def get_my_certificates(request: Request):
    user = await get_current_user(request)
    # Find completed enrollments
    enrollments = await db.enrollments.find({"user_id": user["id"], "completed": True}).to_list(100)
    
    certificates = []
    for e in enrollments:
        course = await db.courses.find_one({"_id": ObjectId(e["course_id"])})
        if course:
            # Get or create certificate
            cert = await db.certificates.find_one({"course_id": e["course_id"], "user_id": user["id"]})
            if not cert:
                cert_doc = {
                    "course_id": e["course_id"],
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "course_title": course.get("title"),
                    "score": e.get("score", 0),
                    "template": "default",
                    "primary_color": "#002FA7",
                    "secondary_color": "#0A0B10",
                    "issued_at": datetime.now(timezone.utc).isoformat(),
                    "certificate_id": str(uuid.uuid4())[:8].upper()
                }
                result = await db.certificates.insert_one(cert_doc)
                cert = {**cert_doc, "_id": result.inserted_id}
            
            certificates.append({
                "id": str(cert["_id"]),
                "certificate_id": cert.get("certificate_id"),
                "course_id": cert["course_id"],
                "course_title": cert.get("course_title"),
                "user_name": cert.get("user_name"),
                "score": cert.get("score"),
                "template": cert.get("template"),
                "primary_color": cert.get("primary_color"),
                "secondary_color": cert.get("secondary_color"),
                "issued_at": cert.get("issued_at")
            })
    return certificates

@api_router.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str):
    cert = await db.certificates.find_one({"_id": ObjectId(certificate_id)})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return {
        "id": str(cert["_id"]),
        "certificate_id": cert.get("certificate_id"),
        "course_id": cert["course_id"],
        "course_title": cert.get("course_title"),
        "user_name": cert.get("user_name"),
        "score": cert.get("score"),
        "template": cert.get("template"),
        "primary_color": cert.get("primary_color"),
        "secondary_color": cert.get("secondary_color"),
        "issued_at": cert.get("issued_at")
    }

@api_router.put("/certificates/{certificate_id}/customize")
async def customize_certificate(certificate_id: str, data: CertificateCustomize, request: Request):
    user = await require_roles("admin")(request)
    result = await db.certificates.update_many(
        {"course_id": data.course_id},
        {"$set": {"template": data.template, "primary_color": data.primary_color, "secondary_color": data.secondary_color}}
    )
    return {"message": f"Updated {result.modified_count} certificates"}

# ============ FORUM ENDPOINTS ============

@api_router.post("/forums/posts")
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

@api_router.get("/forums/{course_id}")
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

@api_router.delete("/forums/posts/{post_id}")
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

# ============ AI CHATBOT ENDPOINTS ============

@api_router.post("/chat")
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

@api_router.get("/chat/{course_id}/history")
async def get_chat_history(course_id: str, request: Request):
    user = await get_current_user(request)
    history = await db.chat_messages.find({
        "course_id": course_id,
        "user_id": user["id"]
    }).sort("created_at", 1).to_list(100)
    return [{"role": h.get("role"), "content": h.get("content"), "created_at": h.get("created_at")} for h in history]

# ============ AUTO-TRANSLATION ENDPOINTS ============

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class TranslateCourseRequest(BaseModel):
    course_id: str
    target_languages: List[str]  # List of language codes to translate to

class TranslateQuizRequest(BaseModel):
    quiz_id: str
    target_languages: List[str]

@api_router.post("/translate/text")
async def translate_text(data: TranslateRequest, request: Request):
    """Translate a single text using Deepseek AI"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    # Validate languages
    if data.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {data.target_language}")
    
    source_name = LANGUAGE_NAMES.get(data.source_language, data.source_language)
    target_name = LANGUAGE_NAMES.get(data.target_language, data.target_language)
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Only output the translation, nothing else. Preserve formatting, line breaks, and any special characters."
                },
                {
                    "role": "user",
                    "content": data.text
                }
            ],
            temperature=0.3
        )
        translated = response.choices[0].message.content.strip()
        return {"translated_text": translated, "source": data.source_language, "target": data.target_language}
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")

@api_router.post("/translate/course/{course_id}")
async def translate_course(course_id: str, data: TranslateCourseRequest, request: Request):
    """Auto-translate course title and description to multiple languages"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Validate target languages
    for lang in data.target_languages:
        if lang not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    
    source_lang = course.get("language", "en")
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    
    translations = {}
    
    for target_lang in data.target_languages:
        if target_lang == source_lang:
            continue
            
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        try:
            # Translate title
            title_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in educational content. Translate the following course title from {source_name} to {target_name}. Only output the translation, nothing else."
                    },
                    {"role": "user", "content": course.get("title", "")}
                ],
                temperature=0.3
            )
            translated_title = title_response.choices[0].message.content.strip()
            
            # Translate description
            desc_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in educational content. Translate the following course description from {source_name} to {target_name}. Preserve formatting and paragraph breaks. Only output the translation, nothing else."
                    },
                    {"role": "user", "content": course.get("description", "")}
                ],
                temperature=0.3
            )
            translated_desc = desc_response.choices[0].message.content.strip()
            
            translations[target_lang] = {
                "title": translated_title,
                "description": translated_desc,
                "language_name": target_name
            }
            
        except Exception as e:
            logger.error(f"Translation error for {target_lang}: {e}")
            translations[target_lang] = {"error": str(e)}
    
    # Store translations in the course document
    await db.courses.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"translations": translations, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "course_id": course_id,
        "source_language": source_lang,
        "translations": translations
    }

@api_router.post("/translate/quiz/{quiz_id}")
async def translate_quiz(quiz_id: str, data: TranslateQuizRequest, request: Request):
    """Auto-translate quiz questions and options to multiple languages"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    quiz = await db.quizzes.find_one({"_id": ObjectId(quiz_id)})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get course language
    course = await db.courses.find_one({"_id": ObjectId(quiz.get("course_id"))})
    source_lang = course.get("language", "en") if course else "en"
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    
    translations = {}
    
    for target_lang in data.target_languages:
        if target_lang == source_lang or target_lang not in SUPPORTED_LANGUAGES:
            continue
            
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        try:
            # Translate title
            title_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                    },
                    {"role": "user", "content": quiz.get("title", "")}
                ],
                temperature=0.3
            )
            translated_title = title_response.choices[0].message.content.strip()
            
            # Translate questions
            translated_questions = []
            for q in quiz.get("questions", []):
                # Translate question text
                q_response = deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": f"Translate this quiz question from {source_name} to {target_name}. Only output the translation."
                        },
                        {"role": "user", "content": q.get("question", "")}
                    ],
                    temperature=0.3
                )
                translated_q = q_response.choices[0].message.content.strip()
                
                # Translate options
                translated_opts = []
                for opt in q.get("options", []):
                    opt_response = deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {
                                "role": "system",
                                "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                            },
                            {"role": "user", "content": opt}
                        ],
                        temperature=0.3
                    )
                    translated_opts.append(opt_response.choices[0].message.content.strip())
                
                translated_questions.append({
                    "question": translated_q,
                    "options": translated_opts,
                    "correct_answer": q.get("correct_answer")  # Index stays the same
                })
            
            translations[target_lang] = {
                "title": translated_title,
                "questions": translated_questions,
                "language_name": target_name
            }
            
        except Exception as e:
            logger.error(f"Quiz translation error for {target_lang}: {e}")
            translations[target_lang] = {"error": str(e)}
    
    # Store translations in the quiz document
    await db.quizzes.update_one(
        {"_id": ObjectId(quiz_id)},
        {"$set": {"translations": translations}}
    )
    
    return {
        "quiz_id": quiz_id,
        "source_language": source_lang,
        "translations": translations
    }

@api_router.post("/courses/{course_id}/create-translation")
async def create_translated_course(course_id: str, target_language: str, request: Request):
    """Create a new course as a translation of an existing course"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target_language}")
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    source_lang = course.get("language", "en")
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_language, target_language)
    
    # Check if translation already exists in stored translations
    stored_translations = course.get("translations", {})
    if target_language in stored_translations and "title" in stored_translations[target_language]:
        translated_title = stored_translations[target_language]["title"]
        translated_desc = stored_translations[target_language]["description"]
    else:
        # Translate title
        title_response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate this course title from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": course.get("title", "")}
            ],
            temperature=0.3
        )
        translated_title = title_response.choices[0].message.content.strip()
        
        # Translate description
        desc_response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate this course description from {source_name} to {target_name}. Preserve formatting. Only output the translation."
                },
                {"role": "user", "content": course.get("description", "")}
            ],
            temperature=0.3
        )
        translated_desc = desc_response.choices[0].message.content.strip()
    
    # Create new course
    new_course = {
        "title": translated_title,
        "description": translated_desc,
        "thumbnail_url": course.get("thumbnail_url"),
        "video_url": course.get("video_url"),
        "video_type": course.get("video_type"),
        "price": course.get("price", 0),
        "is_free": course.get("is_free", True),
        "is_private": course.get("is_private", False),
        "passing_score": course.get("passing_score", 70),
        "materials": course.get("materials", []),
        "language": target_language,
        "category": course.get("category"),
        "source_course_id": course_id,  # Reference to original course
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.courses.insert_one(new_course)
    new_course_id = str(result.inserted_id)
    
    # Also translate lessons if any
    lessons = await db.lessons.find({"course_id": course_id}).to_list(100)
    for lesson in lessons:
        lesson_title_resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": lesson.get("title", "")}
            ],
            temperature=0.3
        )
        lesson_desc_resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": lesson.get("description", "")}
            ],
            temperature=0.3
        )
        
        await db.lessons.insert_one({
            "course_id": new_course_id,
            "title": lesson_title_resp.choices[0].message.content.strip(),
            "description": lesson_desc_resp.choices[0].message.content.strip(),
            "video_url": lesson.get("video_url"),
            "video_type": lesson.get("video_type"),
            "order": lesson.get("order"),
            "materials": lesson.get("materials", []),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "new_course_id": new_course_id,
        "title": translated_title,
        "language": target_language,
        "language_name": target_name
    }

# ============ PAYMENT ENDPOINTS ============

@api_router.post("/payments/checkout")
async def create_checkout(data: PaymentCreate, request: Request):
    user = await get_current_user(request)
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    course = await db.courses.find_one({"_id": ObjectId(data.course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.get("is_free"):
        raise HTTPException(status_code=400, detail="This is a free course")
    
    price = float(course.get("price", 0))
    if price <= 0:
        raise HTTPException(status_code=400, detail="Invalid course price")
    
    success_url = f"{data.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/courses/{data.course_id}"
    
    try:
        # Create Stripe Checkout Session using standard SDK
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.get("title", "Course"),
                        'description': course.get("description", "")[:500] if course.get("description") else None,
                    },
                    'unit_amount': int(price * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "course_id": data.course_id,
                "user_id": user["id"],
                "course_title": course.get("title", "")
            }
        )
        
        # Create payment transaction record
        await db.payment_transactions.insert_one({
            "session_id": session.id,
            "course_id": data.course_id,
            "user_id": user["id"],
            "amount": price,
            "currency": "usd",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment service error")

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    user = await get_current_user(request)
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return cached status
    if transaction.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid"}
    
    try:
        # Get session status from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status  # 'paid', 'unpaid', 'no_payment_required'
        
        # Update transaction status
        if payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            # Auto-enroll user
            existing = await db.enrollments.find_one({"course_id": transaction["course_id"], "user_id": transaction["user_id"]})
            if not existing:
                await db.enrollments.insert_one({
                    "course_id": transaction["course_id"],
                    "user_id": transaction["user_id"],
                    "completed": False,
                    "score": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Send enrollment email
                enrolled_user = await db.users.find_one({"_id": ObjectId(transaction["user_id"])})
                course = await db.courses.find_one({"_id": ObjectId(transaction["course_id"])})
                if enrolled_user and course:
                    await send_enrollment_email(
                        enrolled_user.get("email"),
                        enrolled_user.get("name"),
                        course.get("title"),
                        transaction["course_id"]
                    )
        
        return {"status": session.status, "payment_status": payment_status}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment service error")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    try:
        # Verify webhook signature if secret is configured
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            # Parse without verification (for development)
            import json
            event = stripe.Event.construct_from(json.loads(body), stripe.api_key)
        
        # Handle checkout.session.completed event
        if event.type == "checkout.session.completed":
            session = event.data.object
            session_id = session.id
            payment_status = session.payment_status
            
            if payment_status == "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Auto-enroll user
                transaction = await db.payment_transactions.find_one({"session_id": session_id})
                if transaction:
                    existing = await db.enrollments.find_one({
                        "course_id": transaction["course_id"],
                        "user_id": transaction["user_id"]
                    })
                    if not existing:
                        await db.enrollments.insert_one({
                            "course_id": transaction["course_id"],
                            "user_id": transaction["user_id"],
                            "completed": False,
                            "score": 0,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        # Send enrollment email
                        enrolled_user = await db.users.find_one({"_id": ObjectId(transaction["user_id"])})
                        course = await db.courses.find_one({"_id": ObjectId(transaction["course_id"])})
                        if enrolled_user and course:
                            await send_enrollment_email(
                                enrolled_user.get("email"),
                                enrolled_user.get("name"),
                                course.get("title"),
                                transaction["course_id"]
                            )
        
        return {"status": "ok"}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

# ============ USER MANAGEMENT (Admin/Client Manager) ============

@api_router.get("/users")
async def get_users(request: Request, role: Optional[str] = None):
    user = await require_roles("admin", "client_manager")(request)
    query = {}
    if role:
        query["role"] = role
    users = await db.users.find(query, {"_id": 1, "email": 1, "name": 1, "role": 1, "created_at": 1}).to_list(1000)
    return [{"id": str(u["_id"]), **{k: v for k, v in u.items() if k != "_id"}} for u in users]

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, request: Request):
    admin = await require_roles("admin")(request)
    if role not in ["admin", "client_manager", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}

# ============ DASHBOARD STATS ============

@api_router.get("/stats/admin")
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

@api_router.get("/stats/student")
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

# ============ ROOT ENDPOINT ============

@api_router.get("/")
async def root():
    return {"message": "LearnHub API", "version": "1.0.0"}

# Include router and middleware
app.include_router(api_router)

# CORS Configuration - uses CORS_ORIGINS from .env
CORS_ORIGINS_STR = os.environ.get("CORS_ORIGINS", "*")
if CORS_ORIGINS_STR == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if CORS_ORIGINS_STR != "*" else False,  # credentials not allowed with "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.enrollments.create_index([("course_id", 1), ("user_id", 1)])
    await db.chat_messages.create_index([("course_id", 1), ("user_id", 1)])
    
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@learnhub.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
