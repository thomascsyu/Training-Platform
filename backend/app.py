import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pymongo.errors import PyMongoError
from starlette.middleware.cors import CORSMiddleware

from auth_utils import hash_password, verify_password
from config import (
    CORS_ALLOW_CREDENTIALS,
    CORS_ORIGINS,
    get_seeded_admin_accounts,
    logger,
)
from database import close_db_client, db
from rate_limit import RateLimitMiddleware
from routes import api_router

_database_initialized = False


async def initialize_database():
    await db.command("ping")
    await db.users.create_index("email", unique=True)
    await db.users.create_index("password_reset_token_hash")
    await db.companies.create_index("name", unique=True)
    await db.users.create_index("company_id")
    await db.courses.create_index("company_ids")
    await db.enrollments.create_index([("course_id", 1), ("user_id", 1)])
    await db.lesson_progress.create_index(
        [("user_id", 1), ("course_id", 1), ("lesson_id", 1)], unique=True
    )
    await db.chat_messages.create_index([("course_id", 1), ("user_id", 1)])

    for name, email, password in get_seeded_admin_accounts():
        await _seed_admin_account(name, email, password)


async def _seed_admin_account(name: str, email: str, password: str | None) -> None:
    existing = await db.users.find_one({"email": email})
    if not existing:
        if not password:
            logger.warning(
                "Password not set for %s; skipping admin seed. "
                "Set ADMIN_PASSWORD (and ADMIN2_PASSWORD if used) to create admin accounts.",
                email,
            )
            return

        from datetime import datetime, timezone

        await db.users.insert_one({
            "email": email,
            "password_hash": hash_password(password),
            "name": name,
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin user created: %s", email)
    elif password:
        if not verify_password(password, existing["password_hash"]):
            await db.users.update_one(
                {"email": email},
                {"$set": {"password_hash": hash_password(password)}},
            )
            logger.info("Admin password reset for: %s", email)


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
