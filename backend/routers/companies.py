from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from database import db
from db_utils import parse_object_id
from enrollment_utils import enroll_company_students_in_course
from models import CompanyCreate, CompanyUpdate

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
