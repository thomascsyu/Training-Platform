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


router = APIRouter(tags=["groups"])

@router.get("/groups/overview")
async def get_groups_overview(request: Request):
    """Get overview of all courses with group progress - for Client Manager"""
    await require_roles("admin", "client_manager")(request)

    courses = await db.courses.find(
        {}, {"_id": 1, "title": 1, "language": 1, "thumbnail_url": 1}
    ).to_list(100)

    enrollment_stats = {}
    async for stat in db.enrollments.aggregate([
        {
            "$group": {
                "_id": "$course_id",
                "total_enrolled": {"$sum": 1},
                "completed": {"$sum": {"$cond": ["$completed", 1, 0]}},
                "score_sum": {
                    "$sum": {"$cond": ["$completed", {"$ifNull": ["$score", 0]}, 0]}
                },
            }
        }
    ]):
        enrollment_stats[stat["_id"]] = stat

    result = []
    for course in courses:
        course_id = str(course["_id"])
        stats = enrollment_stats.get(course_id, {})
        total_enrolled = stats.get("total_enrolled", 0)
        completed = stats.get("completed", 0)
        in_progress = total_enrolled - completed
        avg_score = (
            round(stats.get("score_sum", 0) / completed, 1) if completed > 0 else 0
        )
        completion_rate = (
            round((completed / total_enrolled * 100), 1) if total_enrolled > 0 else 0
        )
        result.append({
            "course_id": course_id,
            "course_title": course.get("title"),
            "language": course.get("language", "en"),
            "thumbnail_url": course.get("thumbnail_url"),
            "total_enrolled": total_enrolled,
            "completed": completed,
            "in_progress": in_progress,
            "completion_rate": completion_rate,
            "average_score": avg_score,
        })

    return result

@router.get("/groups/course/{course_id}/progress")
async def get_course_group_progress(course_id: str, request: Request):
    """Get detailed progress of all students in a course - for Client Manager"""
    user = await require_roles("admin", "client_manager")(request)
    
    course = await db.courses.find_one({"_id": ObjectId(course_id)})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    enrollments = await db.enrollments.find({"course_id": course_id}).to_list(1000)
    
    # Batch fetch users to avoid N+1 queries
    user_ids = [ObjectId(e["user_id"]) for e in enrollments]
    users = await db.users.find({"_id": {"$in": user_ids}}, {"_id": 1, "name": 1, "email": 1}).to_list(1000)
    user_map = {str(u["_id"]): u for u in users}
    
    # Batch fetch quiz attempts for all users in this course
    all_quiz_attempts = await db.quiz_attempts.find({"course_id": course_id}).sort("created_at", -1).to_list(10000)
    quiz_attempts_by_user = {}
    for qa in all_quiz_attempts:
        uid = qa["user_id"]
        if uid not in quiz_attempts_by_user:
            quiz_attempts_by_user[uid] = []
        if len(quiz_attempts_by_user[uid]) < 10:  # Keep max 10 per user
            quiz_attempts_by_user[uid].append(qa)
    
    students = []
    for e in enrollments:
        student = user_map.get(e["user_id"])
        if student:
            quiz_attempts = quiz_attempts_by_user.get(e["user_id"], [])
            
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

@router.get("/groups/student/{user_id}/progress")
async def get_student_progress(user_id: str, request: Request):
    """Get detailed progress of a specific student across all courses - for Client Manager"""
    await require_roles("admin", "client_manager")(request)

    student = await db.users.find_one(
        {"_id": ObjectId(user_id)}, {"_id": 1, "name": 1, "email": 1}
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    enrollments = await db.enrollments.find({"user_id": user_id}).to_list(100)
    if not enrollments:
        return {
            "user_id": user_id,
            "user_name": student.get("name"),
            "user_email": student.get("email"),
            "summary": {
                "total_enrolled": 0,
                "completed": 0,
                "in_progress": 0,
                "completion_rate": 0,
                "average_score": 0,
            },
            "courses": [],
        }

    course_ids = [ObjectId(e["course_id"]) for e in enrollments]
    course_docs = await db.courses.find({"_id": {"$in": course_ids}}).to_list(100)
    course_map = {str(c["_id"]): c for c in course_docs}

    quiz_attempts = await db.quiz_attempts.find({"user_id": user_id}).to_list(1000)
    attempts_by_course = {}
    for qa in quiz_attempts:
        cid = qa["course_id"]
        attempts_by_course[cid] = attempts_by_course.get(cid, 0) + 1

    certs = await db.certificates.find({"user_id": user_id}).to_list(100)
    cert_map = {c["course_id"]: c for c in certs}

    courses = []
    for e in enrollments:
        course = course_map.get(e["course_id"])
        if not course:
            continue
        certificate = None
        if e.get("completed"):
            cert = cert_map.get(e["course_id"])
            if cert:
                certificate = {
                    "certificate_id": cert.get("certificate_id"),
                    "issued_at": cert.get("issued_at"),
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
            "quiz_attempts": attempts_by_course.get(e["course_id"], 0),
            "certificate": certificate,
        })

    total_courses = len(courses)
    completed_courses = sum(1 for c in courses if c["completed"])
    avg_score = (
        round(sum(c["score"] for c in courses if c["completed"]) / completed_courses, 1)
        if completed_courses > 0
        else 0
    )

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
