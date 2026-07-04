from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse

import jwt
from config import JWT_ALGORITHM, JWT_SECRET
from database import db
from models import UserCreate, UserLogin
from auth_utils import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    normalize_email,
    set_auth_cookies,
    verify_password,
)

router = APIRouter(tags=["auth"], prefix="/auth")

@router.post("/register")
async def register(data: UserCreate):
    email = normalize_email(data.email)
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_doc = {
        "email": email,
        "password_hash": hash_password(data.password),
        "name": data.name,
        "role": "student",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    resp = JSONResponse(
        content={
            "id": user_id,
            "email": email,
            "name": data.name,
            "role": user_doc["role"],
        }
    )
    set_auth_cookies(
        resp,
        create_access_token(user_id, email, user_doc["role"]),
        create_refresh_token(user_id),
    )
    return resp


@router.post("/login")
async def login(data: UserLogin):
    email = normalize_email(data.email)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = str(user["_id"])
    resp = JSONResponse(
        content={
            "id": user_id,
            "email": email,
            "name": user["name"],
            "role": user["role"],
        }
    )
    set_auth_cookies(
        resp,
        create_access_token(user_id, email, user["role"]),
        create_refresh_token(user_id),
    )
    return resp


@router.post("/logout")
async def logout():
    resp = JSONResponse(content={"message": "Logged out"})
    clear_auth_cookies(resp)
    return resp


@router.post("/refresh")
async def refresh_session(request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user_id = str(user["_id"])
        resp = JSONResponse(content={"message": "Token refreshed"})
        set_auth_cookies(
            resp,
            create_access_token(user_id, user["email"], user["role"]),
            create_refresh_token(user_id),
        )
        return resp
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Refresh token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc


@router.get("/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user
