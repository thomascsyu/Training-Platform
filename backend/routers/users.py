import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user, hash_password, require_roles
from database import db
from db_utils import parse_object_id
from enrollment_utils import enroll_user_in_assigned_company_courses
from models import AdminUserCreate, AdminUserUpdate, UserImportRequest

router = APIRouter(tags=["users"])

VALID_ROLES = {"admin", "client_manager", "student"}
USER_FIELDS = {
    "_id": 1,
    "email": 1,
    "name": 1,
    "role": 1,
    "company_id": 1,
    "created_at": 1,
}


def _serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "company_id": user.get("company_id"),
        "created_at": user.get("created_at"),
    }


async def _validate_company_id(company_id: Optional[str]) -> Optional[str]:
    if company_id is None or company_id == "":
        return None
    oid = parse_object_id(company_id, "company")
    company = await db.companies.find_one({"_id": oid})
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    return company_id


@router.get("/users")
async def get_users(
    request: Request,
    role: Optional[str] = None,
    company_id: Optional[str] = None,
):
    await require_roles("admin", "client_manager")(request)
    query = {}
    if role:
        query["role"] = role
    if company_id:
        await _validate_company_id(company_id)
        query["company_id"] = company_id

    users = await db.users.find(query, USER_FIELDS).sort("name", 1).to_list(1000)
    return [_serialize_user(u) for u in users]


@router.post("/users")
async def create_user(data: AdminUserCreate, request: Request):
    await require_roles("admin")(request)
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    company_id = await _validate_company_id(data.company_id)
    email = data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": email,
        "password_hash": hash_password(data.password),
        "name": data.name.strip(),
        "role": data.role,
        "company_id": company_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    await enroll_user_in_assigned_company_courses(user_doc)
    return _serialize_user(user_doc)


@router.put("/users/{user_id}")
async def update_user(user_id: str, data: AdminUserUpdate, request: Request):
    await require_roles("admin")(request)
    oid = parse_object_id(user_id, "user")
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {}
    if data.name is not None:
        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name is required")
        updates["name"] = name

    if data.email is not None:
        email = data.email.lower()
        existing = await db.users.find_one({"email": email, "_id": {"$ne": oid}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        updates["email"] = email

    if data.role is not None:
        if data.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="Invalid role")
        if user["role"] == "admin" and data.role != "admin":
            admin_count = await db.users.count_documents({"role": "admin"})
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last admin")
        updates["role"] = data.role

    if data.company_id is not None:
        updates["company_id"] = await _validate_company_id(data.company_id)

    if data.password:
        updates["password_hash"] = hash_password(data.password)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.users.update_one({"_id": oid}, {"$set": updates})
    updated = await db.users.find_one({"_id": oid}, USER_FIELDS)
    await enroll_user_in_assigned_company_courses(updated)
    return _serialize_user(updated)


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    current_user = await require_roles("admin")(request)
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    oid = parse_object_id(user_id, "user")
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] == "admin":
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin")

    await db.users.delete_one({"_id": oid})
    return {"message": "User deleted"}


@router.post("/users/import")
async def import_users(data: UserImportRequest, request: Request):
    await require_roles("admin")(request)
    company_id = await _validate_company_id(data.company_id)
    if not company_id:
        raise HTTPException(status_code=400, detail="Company is required for import")

    if not data.users:
        raise HTTPException(status_code=400, detail="No users to import")

    created = []
    skipped = []
    errors = []

    for index, row in enumerate(data.users, start=1):
        email = row.email.lower()
        role = row.role if row.role in VALID_ROLES else "student"
        if role == "admin":
            role = "student"

        existing = await db.users.find_one({"email": email})
        if existing:
            skipped.append({"row": index, "email": email, "reason": "Email already exists"})
            continue

        password = row.password or secrets.token_urlsafe(10)
        if len(password) < 8:
            errors.append({"row": index, "email": email, "reason": "Password must be at least 8 characters"})
            continue

        name = row.name.strip()
        if not name:
            errors.append({"row": index, "email": email, "reason": "Name is required"})
            continue

        user_doc = {
            "email": email,
            "password_hash": hash_password(password),
            "name": name,
            "role": role,
            "company_id": company_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = await db.users.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        await enroll_user_in_assigned_company_courses(user_doc)
        created.append({"id": str(result.inserted_id), "email": email, "name": name, "role": role})

    return {
        "message": f"Imported {len(created)} user(s)",
        "created_count": len(created),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, request: Request):
    await require_roles("admin")(request)
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    oid = parse_object_id(user_id, "user")
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] == "admin" and role != "admin":
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last admin")

    result = await db.users.update_one({"_id": oid}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated = await db.users.find_one({"_id": oid}, USER_FIELDS)
    await enroll_user_in_assigned_company_courses(updated)
    return {"message": "Role updated"}
