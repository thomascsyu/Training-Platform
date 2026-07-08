from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from models import ForgotPasswordRequest, ResetPasswordRequest
from routers import auth as auth_router


@pytest.mark.asyncio
async def test_forgot_password_returns_generic_message_for_missing_user(monkeypatch):
    users = SimpleNamespace(
        find_one=AsyncMock(return_value=None),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(auth_router, "db", SimpleNamespace(users=users))
    send_email = AsyncMock()
    monkeypatch.setattr(auth_router, "send_password_reset_email", send_email)

    response = await auth_router.forgot_password(
        ForgotPasswordRequest(email="missing@example.com")
    )

    assert response["message"] == auth_router.PASSWORD_RESET_GENERIC_MESSAGE
    users.update_one.assert_not_awaited()
    send_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_forgot_password_stores_token_and_sends_email(monkeypatch):
    users = SimpleNamespace(
        find_one=AsyncMock(return_value={"_id": "user-1", "name": "A User"}),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(auth_router, "db", SimpleNamespace(users=users))
    monkeypatch.setattr(auth_router, "FRONTEND_URL", "http://localhost:3000")
    monkeypatch.setattr(auth_router.secrets, "token_urlsafe", lambda _: "reset-token-abc")
    send_email = AsyncMock()
    monkeypatch.setattr(auth_router, "send_password_reset_email", send_email)

    response = await auth_router.forgot_password(
        ForgotPasswordRequest(email="user@example.com")
    )

    assert response["message"] == auth_router.PASSWORD_RESET_GENERIC_MESSAGE

    users.update_one.assert_awaited_once()
    filter_doc, update_doc = users.update_one.await_args.args
    assert filter_doc == {"_id": "user-1"}
    assert (
        update_doc["$set"]["password_reset_token_hash"]
        == auth_router._hash_password_reset_token("reset-token-abc")
    )
    expires_at = datetime.fromisoformat(update_doc["$set"]["password_reset_expires_at"])
    assert expires_at > datetime.now(timezone.utc)

    send_email.assert_awaited_once()
    send_kwargs = send_email.await_args.kwargs
    assert send_kwargs["user_email"] == "user@example.com"
    assert send_kwargs["user_name"] == "A User"
    assert send_kwargs["reset_link"].endswith("/reset-password?token=reset-token-abc")


@pytest.mark.asyncio
async def test_reset_password_rejects_invalid_token(monkeypatch):
    users = SimpleNamespace(
        find_one=AsyncMock(return_value=None),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(auth_router, "db", SimpleNamespace(users=users))

    with pytest.raises(HTTPException) as exc_info:
        await auth_router.reset_password(
            ResetPasswordRequest(
                token="t" * 20,
                new_password="new-password-123",
            )
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired reset token"
    users.update_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_reset_password_clears_expired_token(monkeypatch):
    expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    users = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "_id": "user-1",
                "password_reset_expires_at": expired,
            }
        ),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(auth_router, "db", SimpleNamespace(users=users))

    with pytest.raises(HTTPException) as exc_info:
        await auth_router.reset_password(
            ResetPasswordRequest(
                token="t" * 20,
                new_password="new-password-123",
            )
        )

    assert exc_info.value.status_code == 400
    users.update_one.assert_awaited_once()
    _, update_doc = users.update_one.await_args.args
    assert "password_reset_token_hash" in update_doc["$unset"]
    assert "password_reset_expires_at" in update_doc["$unset"]


@pytest.mark.asyncio
async def test_reset_password_updates_hash_and_clears_token(monkeypatch):
    valid = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    users = SimpleNamespace(
        find_one=AsyncMock(
            return_value={
                "_id": "user-1",
                "password_reset_expires_at": valid,
            }
        ),
        update_one=AsyncMock(),
    )
    monkeypatch.setattr(auth_router, "db", SimpleNamespace(users=users))
    monkeypatch.setattr(auth_router, "hash_password", lambda _: "new-password-hash")

    response = await auth_router.reset_password(
        ResetPasswordRequest(
            token="t" * 20,
            new_password="new-password-123",
        )
    )

    assert response == {"message": "Password reset successful"}
    users.update_one.assert_awaited_once()
    filter_doc, update_doc = users.update_one.await_args.args
    assert filter_doc == {"_id": "user-1"}
    assert update_doc["$set"]["password_hash"] == "new-password-hash"
    assert "password_reset_token_hash" in update_doc["$unset"]
    assert "password_reset_expires_at" in update_doc["$unset"]
