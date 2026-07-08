from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from database import db
from db_utils import parse_object_id
from enrollment_utils import enroll_company_students_in_course
from models import CompanyCreate, CompanyUpdate
from progress_utils import get_bulk_lesson_progress

router = APIRouter(tags=["companies"])


def _serialize_company(company: dict, trainings: Optional[list[dict]] = None) -> dict:
    training_items = trainings or []
    return {
        "id": str(company["_id"]),
        "name": company["name"],
        "description": company.get("description", ""),
        "created_at": company.get("created_at"),
        "trainings": training_items,
        "training_ids": [training["id"] for training in training_items],
    }


async def _validate_training_ids(training_ids: Optional[list[str]]) -> list[str]:
    if not training_ids:
        return []

    normalized = []
    seen = set()
    for training_id in training_ids:
        if not training_id or training_id in seen:
            continue
        parse_object_id(training_id, "course")
        normalized.append(training_id)
        seen.add(training_id)

    existing_count = await db.courses.count_documents({
        "_id": {"$in": [parse_object_id(training_id, "course") for training_id in normalized]},
    })
    if existing_count != len(normalized):
        raise HTTPException(status_code=400, detail="Training not found")

    return normalized


async def _company_training_map(company_ids: list[str]) -> dict[str, list[dict]]:
    if not company_ids:
        return {}

    trainings_by_company = {company_id: [] for company_id in company_ids}
    courses = await db.courses.find(
        {"company_ids": {"$in": company_ids}},
        {"_id": 1, "title": 1, "company_ids": 1},
    ).sort("title", 1).to_list(5000)

    for course in courses:
        course_item = {
            "id": str(course["_id"]),
            "title": course.get("title", ""),
        }
        for company_id in course.get("company_ids", []):
            if company_id in trainings_by_company:
                trainings_by_company[company_id].append(course_item)

    return trainings_by_company


async def _sync_company_training_assignments(
    company_id: str,
    training_ids: list[str],
    enrolled_by: Optional[str] = None,
) -> list[str]:
    current_courses = await db.courses.find(
        {"company_ids": company_id},
        {"_id": 1},
    ).to_list(5000)
    current_training_ids = {str(course["_id"]) for course in current_courses}
    target_training_ids = set(training_ids)

    remove_training_ids = current_training_ids - target_training_ids
    add_training_ids = target_training_ids - current_training_ids

    if remove_training_ids:
        await db.courses.update_many(
            {"_id": {"$in": [parse_object_id(training_id, "course") for training_id in remove_training_ids]}},
            {"$pull": {"company_ids": company_id}},
        )

    enrolled_user_ids = []
    if add_training_ids:
        add_training_object_ids = [parse_object_id(training_id, "course") for training_id in add_training_ids]
        await db.courses.update_many(
            {"_id": {"$in": add_training_object_ids}},
            {"$addToSet": {"company_ids": company_id}},
        )
        newly_assigned_courses = await db.courses.find(
            {"_id": {"$in": add_training_object_ids}},
            {"_id": 1, "title": 1, "company_ids": 1},
        ).to_list(5000)
        for course in newly_assigned_courses:
            enrolled_user_ids.extend(await enroll_company_students_in_course(
                course,
                str(course["_id"]),
                [company_id],
                enrolled_by=enrolled_by,
            ))

    return list(dict.fromkeys(enrolled_user_ids))


def _normalize_training_progress(
    enrollment: Optional[dict],
    lesson_progress: dict,
    quiz_attempt_count: int,
    training: dict,
) -> dict:
    completed = bool(enrollment and enrollment.get("completed"))
    lesson_progress_percent = lesson_progress.get("progress_percent", 0)
    progress_percent = 100 if completed else lesson_progress_percent

    if completed:
        status = "completed"
    elif enrollment:
        status = "in_progress"
    else:
        status = "not_started"

    return {
        "course_id": training["id"],
        "course_title": training.get("title", ""),
        "status": status,
        "completed": completed,
        "score": enrollment.get("score", 0) if enrollment else 0,
        "enrolled_at": enrollment.get("created_at") if enrollment else None,
        "completed_at": enrollment.get("completed_at") if enrollment else None,
        "lessons_completed": lesson_progress.get("lessons_completed", 0),
        "lessons_total": lesson_progress.get("total_lessons", 0),
        "progress_percent": progress_percent,
        "quiz_attempts": quiz_attempt_count,
    }


async def _build_company_dashboard_users(company_id: str, trainings: list[dict]) -> list[dict]:
    users = await db.users.find(
        {"company_id": company_id},
        {"_id": 1, "name": 1, "email": 1, "role": 1, "created_at": 1},
    ).sort("name", 1).to_list(5000)
    if not users:
        return []

    user_ids = [str(user["_id"]) for user in users]
    training_ids = [training["id"] for training in trainings]
    if not training_ids:
        return [
            {
                "user_id": str(user["_id"]),
                "user_name": user.get("name", ""),
                "user_email": user.get("email", ""),
                "role": user.get("role", ""),
                "created_at": user.get("created_at"),
                "summary": {
                    "total_trainings": 0,
                    "completed_trainings": 0,
                    "in_progress_trainings": 0,
                    "not_started_trainings": 0,
                    "overall_progress_percent": 0,
                },
                "trainings": [],
            }
            for user in users
        ]

    enrollments = await db.enrollments.find({
        "user_id": {"$in": user_ids},
        "course_id": {"$in": training_ids},
    }).to_list(20000)
    enrollment_map = {
        (enrollment["user_id"], enrollment["course_id"]): enrollment
        for enrollment in enrollments
    }

    quiz_attempts = await db.quiz_attempts.find(
        {"user_id": {"$in": user_ids}, "course_id": {"$in": training_ids}},
        {"user_id": 1, "course_id": 1},
    ).to_list(50000)
    quiz_attempt_counts: dict[tuple[str, str], int] = {}
    for attempt in quiz_attempts:
        key = (attempt["user_id"], attempt["course_id"])
        quiz_attempt_counts[key] = quiz_attempt_counts.get(key, 0) + 1

    lesson_progress_by_course: dict[str, dict[str, dict]] = {}
    for training_id in training_ids:
        lesson_progress_by_course[training_id] = await get_bulk_lesson_progress(
            user_ids,
            training_id,
        )

    company_users = []
    for user in users:
        user_id = str(user["_id"])
        user_trainings = []
        completed_trainings = 0
        in_progress_trainings = 0
        progress_total = 0

        for training in trainings:
            training_id = training["id"]
            enrollment = enrollment_map.get((user_id, training_id))
            lesson_progress = lesson_progress_by_course.get(training_id, {}).get(user_id, {})
            quiz_attempt_count = quiz_attempt_counts.get((user_id, training_id), 0)

            normalized = _normalize_training_progress(
                enrollment,
                lesson_progress,
                quiz_attempt_count,
                training,
            )
            user_trainings.append(normalized)
            progress_total += normalized["progress_percent"]

            if normalized["status"] == "completed":
                completed_trainings += 1
            elif normalized["status"] == "in_progress":
                in_progress_trainings += 1

        total_trainings = len(user_trainings)
        overall_progress_percent = (
            round(progress_total / total_trainings, 1) if total_trainings > 0 else 0
        )

        company_users.append({
            "user_id": user_id,
            "user_name": user.get("name", ""),
            "user_email": user.get("email", ""),
            "role": user.get("role", ""),
            "created_at": user.get("created_at"),
            "summary": {
                "total_trainings": total_trainings,
                "completed_trainings": completed_trainings,
                "in_progress_trainings": in_progress_trainings,
                "not_started_trainings": max(
                    total_trainings - completed_trainings - in_progress_trainings,
                    0,
                ),
                "overall_progress_percent": overall_progress_percent,
            },
            "trainings": user_trainings,
        })

    return company_users


@router.get("/companies")
async def list_companies(request: Request):
    await require_roles("admin", "client_manager")(request)
    companies = await db.companies.find().sort("name", 1).to_list(1000)
    company_ids = [str(company["_id"]) for company in companies]
    trainings_by_company = await _company_training_map(company_ids)
    return [
        _serialize_company(
            company,
            trainings=trainings_by_company.get(str(company["_id"]), []),
        )
        for company in companies
    ]


@router.get("/companies/{company_id}/dashboard")
async def get_company_dashboard(company_id: str, request: Request):
    await require_roles("admin", "client_manager")(request)
    oid = parse_object_id(company_id, "company")
    company = await db.companies.find_one({"_id": oid})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    trainings_by_company = await _company_training_map([company_id])
    trainings = trainings_by_company.get(company_id, [])
    users = await _build_company_dashboard_users(company_id, trainings)

    total_users = len(users)
    total_trainings = len(trainings)
    total_assignments = total_users * total_trainings
    completed_assignments = sum(
        user["summary"]["completed_trainings"] for user in users
    )
    in_progress_assignments = sum(
        user["summary"]["in_progress_trainings"] for user in users
    )
    not_started_assignments = sum(
        user["summary"]["not_started_trainings"] for user in users
    )
    completion_rate = (
        round((completed_assignments / total_assignments) * 100, 1)
        if total_assignments > 0
        else 0
    )
    average_progress = (
        round(
            sum(user["summary"]["overall_progress_percent"] for user in users)
            / total_users,
            1,
        )
        if total_users > 0
        else 0
    )

    return {
        "company": _serialize_company(company, trainings=trainings),
        "summary": {
            "total_users": total_users,
            "total_trainings": total_trainings,
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "in_progress_assignments": in_progress_assignments,
            "not_started_assignments": not_started_assignments,
            "completion_rate": completion_rate,
            "average_progress_percent": average_progress,
        },
        "users": users,
    }


@router.post("/companies")
async def create_company(data: CompanyCreate, request: Request):
    user = await require_roles("admin")(request)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name is required")

    existing = await db.companies.find_one({"name": name})
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")

    training_ids = await _validate_training_ids(data.training_ids)
    doc = {
        "name": name,
        "description": (data.description or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.companies.insert_one(doc)
    doc["_id"] = result.inserted_id
    company_id = str(result.inserted_id)
    await _sync_company_training_assignments(
        company_id,
        training_ids,
        enrolled_by=user["id"],
    )
    trainings_by_company = await _company_training_map([company_id])
    return _serialize_company(doc, trainings=trainings_by_company.get(company_id, []))


@router.put("/companies/{company_id}")
async def update_company(company_id: str, data: CompanyUpdate, request: Request):
    user = await require_roles("admin")(request)
    oid = parse_object_id(company_id, "company")
    updates = {}

    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Company name is required")
        existing = await db.companies.find_one({"name": name, "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(status_code=400, detail="Company name already exists")
        updates["name"] = name

    if data.description is not None:
        updates["description"] = data.description.strip()

    normalized_training_ids = None
    if data.training_ids is not None:
        normalized_training_ids = await _validate_training_ids(data.training_ids)

    if not updates and normalized_training_ids is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    company = await db.companies.find_one({"_id": oid})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if updates:
        await db.companies.update_one({"_id": oid}, {"$set": updates})

    if normalized_training_ids is not None:
        await _sync_company_training_assignments(
            company_id,
            normalized_training_ids,
            enrolled_by=user["id"],
        )

    company = await db.companies.find_one({"_id": oid})
    trainings_by_company = await _company_training_map([company_id])
    return _serialize_company(company, trainings=trainings_by_company.get(company_id, []))


@router.delete("/companies/{company_id}")
async def delete_company(company_id: str, request: Request):
    await require_roles("admin")(request)
    oid = parse_object_id(company_id, "company")

    user_count = await db.users.count_documents({"company_id": company_id})
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete company with {user_count} assigned user(s)",
        )

    result = await db.companies.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted"}
