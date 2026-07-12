from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request

from auth_utils import get_current_user, require_roles
from database import db

router = APIRouter(tags=["stats"])


@router.get("/stats/admin")
async def get_admin_stats(request: Request):
    await require_roles("admin")(request)

    total_courses = await db.courses.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_enrollments = await db.enrollments.count_documents({})
    completed_courses = await db.enrollments.count_documents({"completed": True})

    return {
        "total_courses": total_courses,
        "total_students": total_students,
        "total_enrollments": total_enrollments,
        "completed_courses": completed_courses,
    }


@router.get("/stats/admin/analytics")
async def get_admin_analytics(request: Request):
    await require_roles("admin")(request)

    total_courses = await db.courses.count_documents({})
    total_students = await db.users.count_documents({"role": "student"})
    total_enrollments = await db.enrollments.count_documents({})
    completed_enrollments = await db.enrollments.count_documents({"completed": True})
    total_certificates = await db.certificates.count_documents({})
    total_lesson_completions = await db.lesson_progress.count_documents({"completed": True})

    completion_rate = (
        round((completed_enrollments / total_enrollments) * 100, 1)
        if total_enrollments > 0
        else 0
    )

    top_courses = []
    async for row in db.enrollments.aggregate([
        {"$group": {"_id": "$course_id", "enrollments": {"$sum": 1}, "completed": {"$sum": {"$cond": ["$completed", 1, 0]}}}},
        {"$sort": {"enrollments": -1}},
        {"$limit": 5},
        {"$lookup": {
            "from": "courses",
            "let": {"cid": "$_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$_id", {"$toObjectId": "$$cid"}]}}},
                {"$project": {"title": 1}},
            ],
            "as": "course",
        }},
        {"$project": {
            "_id": 1,
            "enrollments": 1,
            "completed": 1,
            "course_title": {"$ifNull": [{"$arrayElemAt": ["$course.title", 0]}, "Unknown"]},
        }},
    ]):
        top_courses.append({
            "course_id": row["_id"],
            "course_title": row.get("course_title", "Unknown"),
            "enrollments": row["enrollments"],
            "completed": row["completed"],
            "completion_rate": round((row["completed"] / row["enrollments"]) * 100, 1) if row["enrollments"] else 0,
        })

    quiz_stats = {"total_attempts": 0, "passed": 0, "failed": 0}
    async for row in db.quiz_attempts.aggregate([
        {"$group": {
            "_id": None,
            "total": {"$sum": 1},
            "passed": {"$sum": {"$cond": ["$passed", 1, 0]}},
        }},
    ]):
        quiz_stats["total_attempts"] = row["total"]
        quiz_stats["passed"] = row["passed"]
        quiz_stats["failed"] = row["total"] - row["passed"]

    avg_lesson_progress = 0
    async for row in db.enrollments.aggregate([
        {"$lookup": {
            "from": "lessons",
            "localField": "course_id",
            "foreignField": "course_id",
            "as": "lesson_docs",
        }},
        {"$lookup": {
            "from": "lesson_progress",
            "let": {"uid": "$user_id", "cid": "$course_id"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [
                    {"$eq": ["$user_id", "$$uid"]},
                    {"$eq": ["$course_id", "$$cid"]},
                    {"$eq": ["$completed", True]},
                ]}}},
                {"$count": "completed"},
            ],
            "as": "progress_docs",
        }},
        {"$project": {
            "total_lessons": {"$size": "$lesson_docs"},
            "completed_lessons": {"$ifNull": [{"$arrayElemAt": ["$progress_docs.completed", 0]}, 0]},
        }},
        {"$project": {
            "progress_percent": {
                "$cond": [
                    {"$gt": ["$total_lessons", 0]},
                    {"$multiply": [{"$divide": ["$completed_lessons", "$total_lessons"]}, 100]},
                    0,
                ]
            }
        }},
        {"$group": {"_id": None, "avg_progress": {"$avg": "$progress_percent"}}},
    ]):
        avg_lesson_progress = round(row.get("avg_progress", 0), 1)

    now = datetime.now(timezone.utc)
    start_day = (now - timedelta(days=13)).date()
    enrollment_trend_map = {}
    async for row in db.enrollments.aggregate([
        {"$addFields": {"created_dt": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$match": {"created_dt": {"$gte": datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_dt"}}, "count": {"$sum": 1}}},
    ]):
        enrollment_trend_map[row["_id"]] = row["count"]

    revenue_trend_map = {}
    async for row in db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$addFields": {"created_dt": {"$dateFromString": {"dateString": "$created_at"}}}},
        {"$match": {"created_dt": {"$gte": datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_dt"}},
            "amount": {"$sum": {"$toDouble": "$amount"}},
        }},
    ]):
        revenue_trend_map[row["_id"]] = round(row["amount"], 2)

    enrollment_trend = []
    revenue_trend = []
    for day_offset in range(14):
        day = start_day + timedelta(days=day_offset)
        day_label = day.isoformat()
        enrollment_trend.append({"date": day_label, "count": enrollment_trend_map.get(day_label, 0)})
        revenue_trend.append({"date": day_label, "amount": revenue_trend_map.get(day_label, 0)})

    return {
        "overview": {
            "total_courses": total_courses,
            "total_students": total_students,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "completion_rate": completion_rate,
            "total_certificates": total_certificates,
            "total_lesson_completions": total_lesson_completions,
            "avg_lesson_progress_percent": avg_lesson_progress,
        },
        "quiz_stats": quiz_stats,
        "top_courses": top_courses,
        "enrollment_trend": enrollment_trend,
        "revenue_trend": revenue_trend,
    }


@router.get("/stats/student")
async def get_student_stats(request: Request):
    user = await get_current_user(request)

    enrollments = await db.enrollments.count_documents({"user_id": user["id"]})
    completed = await db.enrollments.count_documents({"user_id": user["id"], "completed": True})
    certificates = await db.certificates.count_documents({"user_id": user["id"]})
    lessons_completed = await db.lesson_progress.count_documents(
        {"user_id": user["id"], "completed": True}
    )

    return {
        "enrolled_courses": enrollments,
        "completed_courses": completed,
        "certificates": certificates,
        "lessons_completed": lessons_completed,
    }
