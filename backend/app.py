import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pymongo.errors import PyMongoError
from starlette.middleware.cors import CORSMiddleware

from auth_utils import hash_password, verify_password
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

_database_initialized = False


async def initialize_database():
    await db.command("ping")
    await db.users.create_index("email", unique=True)
    await db.companies.create_index("name", unique=True)
    await db.users.create_index("company_id")
    await db.enrollments.create_index([("course_id", 1), ("user_id", 1)])
    await db.lesson_progress.create_index(
        [("user_id", 1), ("course_id", 1), ("lesson_id", 1)], unique=True
    )
    await db.chat_messages.create_index([("course_id", 1), ("user_id", 1)])

    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        if not ADMIN_PASSWORD:
            logger.warning(
                "ADMIN_PASSWORD not set; skipping admin seed. "
                "Set ADMIN_PASSWORD to create the default admin account."
            )
        else:
            from datetime import datetime, timezone

            await db.users.insert_one({
                "email": ADMIN_EMAIL,
                "password_hash": hash_password(ADMIN_PASSWORD),
                "name": "Admin",
                "role": "admin",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("Admin user created: %s", ADMIN_EMAIL)
    elif ADMIN_PASSWORD:
        if not verify_password(ADMIN_PASSWORD, existing["password_hash"]):
            await db.users.update_one(
                {"email": ADMIN_EMAIL},
                {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}},
            )
            logger.info("Admin password reset for: %s", ADMIN_EMAIL)


async def _initialize_database_with_retry(
    max_attempts: int = 12,
    base_delay: float = 0.5,
) -> None:
    global _database_initialized

    for attempt in range(1, max_attempts + 1):
        try:
            await initialize_database()
            _database_initialized = True
            return
        except PyMongoError:
            if attempt == max_attempts:
                logger.exception(
                    "Database initialization failed after %s attempts; "
                    "continuing so liveness checks can respond",
                    max_attempts,
                )
                return

            delay = min(base_delay * (2 ** (attempt - 1)), 8)
            logger.warning(
                "Database initialization attempt %s/%s failed; retrying in %.1fs",
                attempt,
                max_attempts,
                delay,
            )
            await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _initialize_database_with_retry()

    yield

    await close_db_client()


app = FastAPI(title="LearnHub - Course Platform", lifespan=lifespan)


@app.get("/", tags=["health"])
async def root():
    return {"message": "LearnHub API", "version": "1.0.0", "health": "/health"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
async def ready():
    if not _database_initialized:
        raise HTTPException(
            status_code=503,
            detail="Database initialization pending",
        )
    try:
        await db.command("ping")
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}


app.include_router(api_router)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)
