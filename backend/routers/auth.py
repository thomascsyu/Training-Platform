import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import JSONResponse

import jwt
from config import (
    FRONTEND_URL,
    JWT_ALGORITHM,
    JWT_SECRET,
    RESET_PASSWORD_TOKEN_TTL_MINUTES,
)
from database import db
from email_service import send_password_reset_email, send_welcome_email
from models import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
)
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
PASSWORD_RESET_TOKEN_BYTES = 32
PASSWORD_RESET_GENERIC_MESSAGE = (
    "If an account with that email exists, a password reset link has been sent."
)


def _hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed

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
    await send_welcome_email(email, data.name)

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
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login_at": datetime.now(timezone.utc).isoformat()}},
    )
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


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    email = normalize_email(data.email)
    user = await db.users.find_one({"email": email})
    if not user:
        return {"message": PASSWORD_RESET_GENERIC_MESSAGE}

    token = secrets.token_urlsafe(PASSWORD_RESET_TOKEN_BYTES)
    token_hash = _hash_password_reset_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=RESET_PASSWORD_TOKEN_TTL_MINUTES
    )

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_reset_token_hash": token_hash,
                "password_reset_expires_at": expires_at.isoformat(),
            }
        },
    )

    reset_link = f"{FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
    await send_password_reset_email(
        user_email=email,
        user_name=user.get("name", "Learner"),
        reset_link=reset_link,
        expires_in_minutes=RESET_PASSWORD_TOKEN_TTL_MINUTES,
    )

    return {"message": PASSWORD_RESET_GENERIC_MESSAGE}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    token = data.token.strip()
    token_hash = _hash_password_reset_token(token)
    user = await db.users.find_one({"password_reset_token_hash": token_hash})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires_at = _parse_iso_datetime(user.get("password_reset_expires_at"))
    if not expires_at or expires_at < datetime.now(timezone.utc):
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$unset": {
                    "password_reset_token_hash": "",
                    "password_reset_expires_at": "",
                }
            },
        )
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"password_hash": hash_password(data.new_password)},
            "$unset": {
                "password_reset_token_hash": "",
                "password_reset_expires_at": "",
            },
        },
    )
    return {"message": "Password reset successful"}


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
