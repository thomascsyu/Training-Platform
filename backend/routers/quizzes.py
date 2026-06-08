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


router = APIRouter(tags=["quizzes"])

@router.post("/quizzes")
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

@router.get("/quizzes/{quiz_id}")
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

@router.post("/quizzes/{quiz_id}/submit")
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

        existing_cert = await db.certificates.find_one({
            "course_id": quiz["course_id"],
            "user_id": user["id"],
        })
        if not existing_cert:
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
                "certificate_id": str(uuid.uuid4())[:8].upper(),
            }
            await db.certificates.insert_one(cert_doc)
            await send_certificate_email(
                user["email"],
                user["name"],
                course.get("title") if course else "Course",
                cert_doc["certificate_id"],
                score,
            )
        else:
            await db.certificates.update_one(
                {"_id": existing_cert["_id"]},
                {"$set": {"score": score, "issued_at": datetime.now(timezone.utc).isoformat()}},
            )
    else:
        course_title = course.get("title") if course else "Course"
        await send_progress_email(
            user["email"],
            user["name"],
            course_title,
            score,
            quiz["course_id"],
        )

    return {"score": score, "passed": passed, "passing_score": passing_score, "correct": correct, "total": len(questions)}
