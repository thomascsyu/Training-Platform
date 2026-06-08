from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from database import db
from db_utils import parse_object_id

router = APIRouter(tags=["users"])


@router.get("/users")
async def get_users(request: Request, role: Optional[str] = None):
    await require_roles("admin", "client_manager")(request)
    query = {}
    if role:
        query["role"] = role
    users = await db.users.find(
        query, {"_id": 1, "email": 1, "name": 1, "role": 1, "created_at": 1}
    ).to_list(1000)
    return [
        {"id": str(u["_id"]), **{k: v for k, v in u.items() if k != "_id"}}
        for u in users
    ]


@router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, request: Request):
    await require_roles("admin")(request)
    if role not in ["admin", "client_manager", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    result = await db.users.update_one(
        {"_id": parse_object_id(user_id, "user")},
        {"$set": {"role": role}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}
