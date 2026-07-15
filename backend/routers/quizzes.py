from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user, require_roles
from certificate_id import generate_certificate_id
from certificate_template import compute_valid_until
from certificate_utils import apply_template_to_certificate, resolve_certificate_template
from database import db
from db_utils import parse_object_id
from email_service import send_certificate_email, send_progress_email
from models import QuizAttemptCreate, QuizCreate, QuizUpdate
from progress_utils import require_enrollment

router = APIRouter(tags=["quizzes"])


@router.post("/quizzes")
async def create_quiz(data: QuizCreate, request: Request):
    await require_roles("admin")(request)
    quiz_doc = {
        "course_id": data.course_id,
        "title": data.title,
        "questions": data.questions,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.quizzes.insert_one(quiz_doc)
    return {
        "id": str(result.inserted_id),
        **{k: v for k, v in quiz_doc.items() if k != "_id"},
    }


@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: str, request: Request, lang: str | None = None):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"_id": parse_object_id(quiz_id, "quiz")})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if user["role"] == "student":
        await require_enrollment(user["id"], quiz["course_id"])

    quiz_data = {
        "id": str(quiz["_id"]),
        **{k: v for k, v in quiz.items() if k != "_id"},
    }
    if lang:
        translated = quiz.get("translations", {}).get(lang)
        if translated and not translated.get("error"):
            quiz_data.update({
                "title": translated.get("title", quiz_data.get("title")),
                "questions": translated.get("questions", quiz_data.get("questions", [])),
                "display_language": lang,
            })
    if user["role"] == "student":
        for q in quiz_data.get("questions", []):
            q.pop("correct_answer", None)
    return quiz_data


@router.put("/quizzes/{quiz_id}")
async def update_quiz(quiz_id: str, data: QuizUpdate, request: Request):
    await require_roles("admin")(request)
    update_data = {
        k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None
    }
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "questions" in update_data:
        update_data["translations"] = {}

    result = await db.quizzes.update_one(
        {"_id": parse_object_id(quiz_id, "quiz")},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"message": "Quiz updated"}


@router.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str, request: Request):
    await require_roles("admin")(request)
    oid = parse_object_id(quiz_id, "quiz")
    result = await db.quizzes.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quiz not found")
    await db.quiz_attempts.delete_many({"quiz_id": quiz_id})
    return {"message": "Quiz deleted"}


@router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, data: QuizAttemptCreate, request: Request):
    user = await get_current_user(request)
    quiz = await db.quizzes.find_one({"_id": parse_object_id(quiz_id, "quiz")})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    await require_enrollment(user["id"], quiz["course_id"])

    questions = quiz.get("questions", [])
    correct = 0
    for i, q in enumerate(questions):
        if i < len(data.answers) and data.answers[i] == q.get("correct_answer"):
            correct += 1

    score = int((correct / len(questions)) * 100) if questions else 0

    course = await db.courses.find_one(
        {"_id": parse_object_id(quiz["course_id"], "course")}
    )
    passing_score = course.get("passing_score", 70) if course else 70
    passed = score >= passing_score

    attempt_doc = {
        "quiz_id": quiz_id,
        "course_id": quiz["course_id"],
        "user_id": user["id"],
        "answers": data.answers,
        "score": score,
        "passed": passed,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.quiz_attempts.insert_one(attempt_doc)

    if passed:
        await db.enrollments.update_one(
            {"course_id": quiz["course_id"], "user_id": user["id"]},
            {
                "$set": {
                    "completed": True,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "score": score,
                }
            },
        )

        auto_issue_certificate = course.get("auto_issue_certificate", True) if course else True
        if auto_issue_certificate:
            existing_cert = await db.certificates.find_one({
                "course_id": quiz["course_id"],
                "user_id": user["id"],
            })
            issued_at = datetime.now(timezone.utc).isoformat()
            if not existing_cert:
                course_title = course.get("title") if course else "Course"
                cert_doc = {
                    "course_id": quiz["course_id"],
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "course_title": course_title,
                    "score": score,
                    "issued_at": issued_at,
                    "certificate_id": await generate_certificate_id(
                        db, issued_at=issued_at, course_title=course_title
                    ),
                }
                template = await resolve_certificate_template(db)
                apply_template_to_certificate(
                    cert_doc,
                    template,
                    fallback_language=course.get("language") if course else None,
                )
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
                    {
                        "$set": {
                            "score": score,
                            "issued_at": issued_at,
                            "valid_until": compute_valid_until(issued_at),
                        }
                    },
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

    return {
        "score": score,
        "passed": passed,
        "passing_score": passing_score,
        "correct": correct,
        "total": len(questions),
    }
