from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from database import db
from db_utils import parse_object_id
from models import CompanyCreate, CompanyUpdate

router = APIRouter(tags=["companies"])


def _serialize_company(company: dict) -> dict:
    return {
        "id": str(company["_id"]),
        "name": company["name"],
        "description": company.get("description", ""),
        "created_at": company.get("created_at"),
    }


@router.get("/companies")
async def list_companies(request: Request):
    await require_roles("admin", "client_manager")(request)
    companies = await db.companies.find().sort("name", 1).to_list(1000)
    return [_serialize_company(c) for c in companies]


@router.post("/companies")
async def create_company(data: CompanyCreate, request: Request):
    await require_roles("admin")(request)
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Company name is required")

    existing = await db.companies.find_one({"name": name})
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")

    doc = {
        "name": name,
        "description": (data.description or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.companies.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_company(doc)


@router.put("/companies/{company_id}")
async def update_company(company_id: str, data: CompanyUpdate, request: Request):
    await require_roles("admin")(request)
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

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.companies.update_one({"_id": oid}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")

    company = await db.companies.find_one({"_id": oid})
    return _serialize_company(company)


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
