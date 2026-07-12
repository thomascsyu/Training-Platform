import html
import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional

from config import BREVO_API_KEY, EMAIL_FROM, EMAIL_FROM_NAME, FRONTEND_URL, logger
from database import db

SETTINGS_DOC_ID = "email_notifications"

PASSWORD_RESET = "password_reset"
WELCOME_USER = "welcome_user"
COURSE_ENROLLMENT_FREE = "course_enrollment_free"
COURSE_ENROLLMENT_PAID = "course_enrollment_paid"
COURSE_COMPLETED = "course_completed"
INACTIVE_ENROLLED = "inactive_enrolled"

DEFAULT_NOTIFICATION_EVENTS = {
    PASSWORD_RESET: {
        "label": "Forgot or reset password",
        "description": "Sent when a learner requests a password reset link.",
        "enabled": True,
        "subject": "Reset your LearnHub password",
        "html_content": """
        <h1>Password Reset Request</h1>
        <p>Hi {{user_name}},</p>
        <p>We received a request to reset your LearnHub password. Click below to choose a new password.</p>
        <p><a href="{{reset_link}}">Reset Password</a></p>
        <p>This link expires in {{expires_in_minutes}} minutes. If you did not request this, you can ignore this email.</p>
        """,
        "text_content": (
            "Hi {{user_name}},\n\n"
            "We received a request to reset your LearnHub password.\n"
            "Use this link to set a new password: {{reset_link}}\n\n"
            "This link expires in {{expires_in_minutes}} minutes."
        ),
    },
    WELCOME_USER: {
        "label": "First join welcome email",
        "description": "Sent after a learner creates an account.",
        "enabled": True,
        "subject": "Welcome to LearnHub, {{user_name}}",
        "html_content": """
        <h1>Welcome to LearnHub</h1>
        <p>Hi {{user_name}},</p>
        <p>Your account is ready. Browse courses and start learning whenever you are ready.</p>
        <p><a href="{{frontend_url}}/courses">Browse Courses</a></p>
        """,
        "text_content": (
            "Hi {{user_name}},\n\n"
            "Welcome to LearnHub. Browse courses here: {{frontend_url}}/courses"
        ),
    },
    COURSE_ENROLLMENT_FREE: {
        "label": "Join or enroll course",
        "description": "Sent when a learner joins or is enrolled in a free/direct course.",
        "enabled": True,
        "subject": "Welcome to {{course_title}}",
        "html_content": """
        <h1>You are enrolled</h1>
        <p>Hi {{user_name}},</p>
        <p>You have been enrolled in <strong>{{course_title}}</strong>.</p>
        <p><a href="{{course_url}}">Start Learning</a></p>
        """,
        "text_content": (
            "Hi {{user_name}},\n\n"
            "You have been enrolled in {{course_title}}.\n"
            "Start learning: {{course_url}}"
        ),
    },
    COURSE_ENROLLMENT_PAID: {
        "label": "Just paid course access",
        "description": "Sent after payment succeeds and course access is created.",
        "enabled": True,
        "subject": "Payment complete: {{course_title}} is ready",
        "html_content": """
        <h1>Your course is ready</h1>
        <p>Hi {{user_name}},</p>
        <p>Thanks for your payment. You can now access <strong>{{course_title}}</strong>.</p>
        <p><a href="{{course_url}}">Open Course</a></p>
        """,
        "text_content": (
            "Hi {{user_name}},\n\n"
            "Thanks for your payment. {{course_title}} is ready: {{course_url}}"
        ),
    },
    COURSE_COMPLETED: {
        "label": "Completed course",
        "description": "Sent when a learner completes a course and receives a certificate.",
        "enabled": True,
        "subject": "Congratulations! You completed {{course_title}}",
        "html_content": """
        <h1>Congratulations!</h1>
        <p>Dear {{user_name}},</p>
        <p>You completed <strong>{{course_title}}</strong> with a score of <strong>{{score}}%</strong>.</p>
        <p>Certificate ID: {{certificate_id}}</p>
        <p><a href="{{frontend_url}}/certificates">View Your Certificate</a></p>
        """,
        "text_content": (
            "Dear {{user_name}},\n\n"
            "You completed {{course_title}} with a score of {{score}}%.\n"
            "Certificate ID: {{certificate_id}}\n"
            "View certificates: {{frontend_url}}/certificates"
        ),
    },
    INACTIVE_ENROLLED: {
        "label": "Enrolled but not logged in",
        "description": "Sent to enrolled learners who have not logged in for the configured number of days.",
        "enabled": True,
        "inactivity_days": 7,
        "subject": "Continue learning {{course_title}}",
        "html_content": """
        <h1>Your course is waiting</h1>
        <p>Hi {{user_name}},</p>
        <p>You enrolled in <strong>{{course_title}}</strong>, but we have not seen you for {{inactivity_days}} days.</p>
        <p><a href="{{course_url}}">Resume Learning</a></p>
        """,
        "text_content": (
            "Hi {{user_name}},\n\n"
            "You enrolled in {{course_title}}, but have not logged in for {{inactivity_days}} days.\n"
            "Resume learning: {{course_url}}"
        ),
    },
}

AVAILABLE_PLACEHOLDERS = [
    "user_name",
    "user_email",
    "course_title",
    "course_url",
    "certificate_id",
    "score",
    "reset_link",
    "expires_in_minutes",
    "frontend_url",
    "inactivity_days",
]

PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


async def send_brevo_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
):
    if not BREVO_API_KEY:
        logger.warning("Brevo API key not configured, skipping email")
        return None

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }
    payload = {
        "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code in [200, 201, 202]:
                logger.info("Email sent successfully to %s", to_email)
                return response.json()
            logger.error(
                "Failed to send email: %s - %s", response.status_code, response.text
            )
            return None
    except Exception as exc:
        logger.error("Email sending error: %s", exc)
        return None


def _base_email_html(content: str) -> str:
    return f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">LearnHub</h1>
            </div>
            <div style="padding: 30px; color: #0A0B10; font-size: 14px; line-height: 1.6;">
                {content}
            </div>
        </div>
    </body>
    </html>
    """


def _merge_event_settings(saved_events: dict[str, Any] | None = None) -> dict[str, dict]:
    merged = deepcopy(DEFAULT_NOTIFICATION_EVENTS)
    for key, saved in (saved_events or {}).items():
        if key in merged and isinstance(saved, dict):
            allowed = {
                "enabled",
                "subject",
                "html_content",
                "text_content",
                "inactivity_days",
            }
            merged[key].update({k: v for k, v in saved.items() if k in allowed})
    return merged


def _serialize_settings(events: dict[str, dict]) -> dict:
    return {
        "events": [
            {"key": key, **value}
            for key, value in events.items()
        ],
        "placeholders": AVAILABLE_PLACEHOLDERS,
    }


async def load_email_notification_settings() -> dict:
    doc = await db.email_notification_settings.find_one({"_id": SETTINGS_DOC_ID})
    events = _merge_event_settings((doc or {}).get("events"))
    return _serialize_settings(events)


async def save_email_notification_settings(updates: dict, updated_by: str = "") -> dict:
    current = await db.email_notification_settings.find_one({"_id": SETTINGS_DOC_ID})
    events = _merge_event_settings((current or {}).get("events"))

    for key, patch in (updates.get("events") or {}).items():
        if key not in events:
            raise ValueError(f"Unknown email notification event: {key}")
        if patch:
            events[key].update({k: v for k, v in patch.items() if v is not None})

    now = datetime.now(timezone.utc).isoformat()
    await db.email_notification_settings.update_one(
        {"_id": SETTINGS_DOC_ID},
        {
            "$set": {
                "events": events,
                "updated_at": now,
                "updated_by": updated_by,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    return _serialize_settings(events)


def _render_template(template: str, context: dict[str, Any], *, escape: bool) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1)
        value = "" if context.get(key) is None else str(context.get(key))
        return html.escape(value) if escape else value

    return PLACEHOLDER_RE.sub(replace, template or "")


async def send_notification_email(
    event_key: str,
    user_email: str,
    user_name: str,
    context: Optional[dict[str, Any]] = None,
):
    if not user_email:
        logger.warning("Skipping %s email because recipient email is missing", event_key)
        return None

    settings = await load_email_notification_settings()
    events = {event["key"]: event for event in settings["events"]}
    event = events.get(event_key)
    if not event:
        logger.warning("Skipping unknown email notification event: %s", event_key)
        return None
    if not event.get("enabled", True):
        logger.info("Email notification %s is disabled", event_key)
        return None

    render_context = {
        "user_name": user_name or "Learner",
        "user_email": user_email,
        "frontend_url": FRONTEND_URL.rstrip("/"),
        **(context or {}),
    }
    subject = _render_template(event["subject"], render_context, escape=False)
    html_content = _base_email_html(
        _render_template(event["html_content"], render_context, escape=True)
    )
    text_content = (
        _render_template(event.get("text_content", ""), render_context, escape=False)
        if event.get("text_content")
        else None
    )
    return await send_brevo_email(
        user_email,
        user_name or "Learner",
        subject,
        html_content,
        text_content=text_content,
    )


async def send_enrollment_email(
    user_email: str,
    user_name: str,
    course_title: str,
    course_id: str,
    event_key: str = COURSE_ENROLLMENT_FREE,
):
    return await send_notification_email(
        event_key,
        user_email,
        user_name,
        {
            "course_title": course_title or "Course",
            "course_url": f"{FRONTEND_URL.rstrip('/')}/courses/{course_id}",
        },
    )


async def send_progress_email(
    user_email: str,
    user_name: str,
    course_title: str,
    progress: int,
    course_id: str,
):
    subject = f"Progress Update: {progress}% Complete - {course_title}"
    html_content = f"""
    <html>
    <body style="font-family: 'IBM Plex Sans', Arial, sans-serif; background-color: #F4F5F7; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 4px; overflow: hidden;">
            <div style="background-color: #002FA7; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px;">Progress Update</h1>
            </div>
            <div style="padding: 30px;">
                <p style="color: #0A0B10; font-size: 16px;">Hi {user_name},</p>
                <p style="color: #64748B; font-size: 14px;">Great progress on <strong>{course_title}</strong>!</p>
                <div style="background-color: #E2E8F0; height: 24px; border-radius: 12px; overflow: hidden; margin: 20px 0;">
                    <div style="background-color: #002FA7; height: 100%; width: {progress}%;"></div>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_URL}/courses/{course_id}"
                       style="background-color: #002FA7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px;">
                        Continue Learning
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_brevo_email(user_email, user_name, subject, html_content)


async def send_certificate_email(
    user_email: str,
    user_name: str,
    course_title: str,
    certificate_id: str,
    score: int,
):
    return await send_notification_email(
        COURSE_COMPLETED,
        user_email,
        user_name,
        {
            "course_title": course_title or "Course",
            "certificate_id": certificate_id,
            "score": score,
        },
    )


async def send_password_reset_email(
    user_email: str,
    user_name: str,
    reset_link: str,
    expires_in_minutes: int,
):
    return await send_notification_email(
        PASSWORD_RESET,
        user_email,
        user_name,
        {
            "reset_link": reset_link,
            "expires_in_minutes": expires_in_minutes,
        },
    )


async def send_welcome_email(user_email: str, user_name: str):
    return await send_notification_email(WELCOME_USER, user_email, user_name)


async def send_inactive_enrollment_email(
    user_email: str,
    user_name: str,
    course_title: str,
    course_id: str,
    inactivity_days: int,
):
    return await send_notification_email(
        INACTIVE_ENROLLED,
        user_email,
        user_name,
        {
            "course_title": course_title or "Course",
            "course_url": f"{FRONTEND_URL.rstrip('/')}/courses/{course_id}",
            "inactivity_days": inactivity_days,
        },
    )
