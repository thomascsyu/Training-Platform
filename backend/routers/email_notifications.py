from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from config import FRONTEND_URL
from database import db
from email_service import (
    INACTIVE_ENROLLED,
    load_email_notification_settings,
    save_email_notification_settings,
    send_inactive_enrollment_email,
    send_notification_email,
)
from models import EmailNotificationSettingsUpdate, EmailNotificationTestRequest

router = APIRouter(tags=["email-notifications"])


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _event_map(settings: dict) -> dict[str, dict]:
    return {event["key"]: event for event in settings.get("events", [])}


@router.get("/admin/email-notifications")
async def get_email_notifications(request: Request):
    await require_roles("admin")(request)
    return await load_email_notification_settings()


@router.put("/admin/email-notifications")
async def update_email_notifications(
    data: EmailNotificationSettingsUpdate, request: Request
):
    user = await require_roles("admin")(request)
    try:
        return await save_email_notification_settings(
            data.model_dump(exclude_unset=True),
            user.get("id", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/admin/email-notifications/test")
async def test_email_notification(data: EmailNotificationTestRequest, request: Request):
    await require_roles("admin")(request)
    settings = await load_email_notification_settings()
    events = _event_map(settings)
    if data.event_key not in events:
        raise HTTPException(status_code=400, detail="Unknown email notification event")

    sample_course_id = "sample-course"
    await send_notification_email(
        data.event_key,
        data.email,
        data.name,
        {
            "course_title": "Sample Course",
            "course_url": f"{FRONTEND_URL.rstrip('/')}/courses/{sample_course_id}",
            "certificate_id": "ABC12345",
            "score": 95,
            "reset_link": f"{FRONTEND_URL.rstrip('/')}/reset-password?token=sample",
            "expires_in_minutes": 30,
            "inactivity_days": events[data.event_key].get("inactivity_days", 7),
        },
    )
    return {"message": "Test email triggered"}


@router.post("/admin/email-notifications/trigger-inactivity")
async def trigger_inactivity_notifications(request: Request):
    await require_roles("admin")(request)
    settings = await load_email_notification_settings()
    inactivity_event = _event_map(settings).get(INACTIVE_ENROLLED)
    if not inactivity_event:
        raise HTTPException(status_code=400, detail="Inactivity notification is unavailable")
    if not inactivity_event.get("enabled", True):
        return {"message": "Inactivity notification is disabled", "triggered": 0, "skipped": 0}

    inactivity_days = int(inactivity_event.get("inactivity_days") or 7)
    cutoff = datetime.now(timezone.utc) - timedelta(days=inactivity_days)
    enrollments = await db.enrollments.find({"completed": {"$ne": True}}).to_list(10000)

    user_ids = list({e.get("user_id") for e in enrollments if e.get("user_id")})
    course_ids = list({e.get("course_id") for e in enrollments if e.get("course_id")})

    users = await db.users.find(
        {"_id": {"$in": [ObjectId(uid) for uid in user_ids]}},
        {"_id": 1, "email": 1, "name": 1, "last_login_at": 1},
    ).to_list(len(user_ids) or 1)
    courses = await db.courses.find(
        {"_id": {"$in": [ObjectId(cid) for cid in course_ids]}},
        {"_id": 1, "title": 1},
    ).to_list(len(course_ids) or 1)
    user_map = {str(user["_id"]): user for user in users}
    course_map = {str(course["_id"]): course for course in courses}

    triggered = 0
    skipped = 0
    now = datetime.now(timezone.utc).isoformat()
    for enrollment in enrollments:
        user_id = enrollment.get("user_id")
        course_id = enrollment.get("course_id")
        user = user_map.get(user_id)
        course = course_map.get(course_id)
        enrolled_at = _parse_datetime(enrollment.get("created_at"))
        last_login_at = _parse_datetime(user.get("last_login_at")) if user else None
        if not user or not course or not enrolled_at or enrolled_at > cutoff:
            skipped += 1
            continue
        if last_login_at and last_login_at > cutoff:
            skipped += 1
            continue

        existing_log = await db.email_notification_logs.find_one({
            "event_key": INACTIVE_ENROLLED,
            "user_id": user_id,
            "course_id": course_id,
            "inactivity_days": inactivity_days,
        })
        if existing_log:
            skipped += 1
            continue

        result = await send_inactive_enrollment_email(
            user.get("email"),
            user.get("name"),
            course.get("title"),
            course_id,
            inactivity_days,
        )
        await db.email_notification_logs.insert_one({
            "event_key": INACTIVE_ENROLLED,
            "user_id": user_id,
            "course_id": course_id,
            "inactivity_days": inactivity_days,
            "sent": result is not None,
            "created_at": now,
        })
        triggered += 1

    return {"message": "Inactivity notification run complete", "triggered": triggered, "skipped": skipped}
