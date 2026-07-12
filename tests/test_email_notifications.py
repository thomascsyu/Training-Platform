from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

import email_service
from routers import email_notifications as notifications_router


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, _limit):
        return self.docs


def _fake_require_roles(*_roles):
    async def _checker(_request):
        return {"id": "admin-id", "role": "admin"}

    return _checker


@pytest.mark.asyncio
async def test_send_notification_email_uses_saved_template(monkeypatch):
    settings_collection = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "events": {
                    email_service.COURSE_ENROLLMENT_FREE: {
                        "enabled": True,
                        "subject": "Start {{course_title}}",
                        "html_content": "<p>Hello {{user_name}}, open {{course_title}}</p>",
                        "text_content": "Hello {{user_name}}",
                    }
                }
            }
        )
    )
    monkeypatch.setattr(
        email_service,
        "db",
        SimpleNamespace(email_notification_settings=settings_collection),
    )
    send_brevo = AsyncMock(return_value={"messageId": "123"})
    monkeypatch.setattr(email_service, "send_brevo_email", send_brevo)

    result = await email_service.send_notification_email(
        email_service.COURSE_ENROLLMENT_FREE,
        "learner@example.com",
        "<Learner>",
        {"course_title": "Security <Basics>"},
    )

    assert result == {"messageId": "123"}
    send_brevo.assert_awaited_once()
    _, to_name, subject, html_content = send_brevo.await_args.args[:4]
    assert to_name == "<Learner>"
    assert subject == "Start Security <Basics>"
    assert "Hello &lt;Learner&gt;" in html_content
    assert "Security &lt;Basics&gt;" in html_content


@pytest.mark.asyncio
async def test_save_email_notification_settings_rejects_unknown_event(monkeypatch):
    settings_collection = SimpleNamespace(
        find_one=AsyncMock(return_value=None),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(
        email_service,
        "db",
        SimpleNamespace(email_notification_settings=settings_collection),
    )

    with pytest.raises(ValueError):
        await email_service.save_email_notification_settings(
            {"events": {"unknown_event": {"enabled": True}}},
            "admin-id",
        )

    settings_collection.update_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_inactivity_notifications_sends_for_stale_enrollment(monkeypatch):
    user_id = ObjectId()
    course_id = ObjectId()
    stale_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

    mock_db = MagicMock()
    mock_db.enrollments.find.return_value = FakeCursor([
        {
            "user_id": str(user_id),
            "course_id": str(course_id),
            "completed": False,
            "created_at": stale_date,
        }
    ])
    mock_db.users.find.return_value = FakeCursor([
        {
            "_id": user_id,
            "email": "learner@example.com",
            "name": "Learner",
        }
    ])
    mock_db.courses.find.return_value = FakeCursor([
        {
            "_id": course_id,
            "title": "Security Basics",
        }
    ])
    mock_db.email_notification_logs.find_one = AsyncMock(return_value=None)
    mock_db.email_notification_logs.insert_one = AsyncMock()

    monkeypatch.setattr(notifications_router, "db", mock_db)
    monkeypatch.setattr(notifications_router, "require_roles", _fake_require_roles)
    monkeypatch.setattr(
        notifications_router,
        "load_email_notification_settings",
        AsyncMock(
            return_value={
                "events": [
                    {
                        "key": email_service.INACTIVE_ENROLLED,
                        "enabled": True,
                        "inactivity_days": 7,
                    }
                ]
            }
        ),
    )
    send_inactive = AsyncMock(return_value={"messageId": "123"})
    monkeypatch.setattr(
        notifications_router,
        "send_inactive_enrollment_email",
        send_inactive,
    )

    response = await notifications_router.trigger_inactivity_notifications(request=object())

    assert response["triggered"] == 1
    assert response["skipped"] == 0
    send_inactive.assert_awaited_once_with(
        "learner@example.com",
        "Learner",
        "Security Basics",
        str(course_id),
        7,
    )
    mock_db.email_notification_logs.insert_one.assert_awaited_once()
