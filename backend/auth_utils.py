from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from fastapi import HTTPException, Request

from config import COOKIE_SAMESITE, COOKIE_SECURE, JWT_ALGORITHM, JWT_SECRET
from database import db

ACCESS_TOKEN_MAX_AGE = 3600
REFRESH_TOKEN_MAX_AGE = 604800


def normalize_email(email: str) -> str:
    return email.lower().strip()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_auth_cookies(response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_MAX_AGE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_MAX_AGE,
        path="/",
    )


def clear_auth_cookies(response):
    response.delete_cookie(
        "access_token", path="/", samesite=COOKIE_SAMESITE
    )
    response.delete_cookie(
        "refresh_token", path="/", samesite=COOKIE_SAMESITE
    )


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "company_id": user.get("company_id"),
        }
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def get_optional_user(request: Request):
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def require_roles(*roles):
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return role_checker


async def require_admin_or_manager(request: Request) -> dict:
    """Return the current user if they are an admin or a company-assigned client manager."""
    user = await get_current_user(request)
    if user["role"] not in {"admin", "client_manager"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if user["role"] == "client_manager" and not user.get("company_id"):
        raise HTTPException(status_code=403, detail="Client manager is not assigned to a company")
    return user
