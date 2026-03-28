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
from openai import OpenAI
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

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
    
    return {"score": score, "passed": passed, "passing_score": passing_score, "correct": correct, "total": len(questions)}

# ============ ENROLLMENT ENDPOINTS ============

@api_router.post("/enrollments")
async def create_enrollment(data: EnrollmentCreate, request: Request):
    user = await get_current_user(request)
    
    course = await db.courses.find_one({"_id": ObjectId(data.course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # If client_manager doing bulk enrollment
    if user["role"] == "client_manager" and data.user_ids:
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
                "created_at": e.get("created_at")
            })
    return result

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
    
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/courses/{data.course_id}"
    
    checkout_request = CheckoutSessionRequest(
        amount=price,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "course_id": data.course_id,
            "user_id": user["id"],
            "course_title": course.get("title", "")
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "course_id": data.course_id,
        "user_id": user["id"],
        "amount": price,
        "currency": "usd",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

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
    
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction status
    if status.payment_status == "paid":
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
    
    return {"status": status.status, "payment_status": status.payment_status}

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        event = await stripe_checkout.handle_webhook(body, signature)
        
        if event.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": event.session_id},
                {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Auto-enroll user
            transaction = await db.payment_transactions.find_one({"session_id": event.session_id})
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
        
        return {"status": "ok"}
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

# Get frontend URL for CORS
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://feature-builder-19.preview.emergentagent.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
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
