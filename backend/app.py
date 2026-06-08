from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from auth_utils import hash_password
from config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    CORS_ALLOW_CREDENTIALS,
    CORS_ORIGINS,
    logger,
)
from database import close_db_client, db
from rate_limit import RateLimitMiddleware
from routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.users.create_index("email", unique=True)
    await db.enrollments.create_index([("course_id", 1), ("user_id", 1)])
    await db.lesson_progress.create_index(
        [("user_id", 1), ("course_id", 1), ("lesson_id", 1)], unique=True
    )
    await db.chat_messages.create_index([("course_id", 1), ("user_id", 1)])

    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        from datetime import datetime, timezone

        await db.users.insert_one({
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "name": "Admin",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin user created: %s", ADMIN_EMAIL)

    yield
    await close_db_client()


app = FastAPI(title="LearnHub - Course Platform", lifespan=lifespan)
app.include_router(api_router)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)
