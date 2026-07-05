import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from pymongo.errors import PyMongoError

import app


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.command = AsyncMock()
    db.users = MagicMock()
    db.users.create_index = AsyncMock()
    db.users.find_one = AsyncMock()
    db.users.insert_one = AsyncMock()
    db.users.update_one = AsyncMock()
    db.users.count_documents = AsyncMock()
    db.companies = MagicMock()
    db.companies.create_index = AsyncMock()
    db.enrollments = MagicMock()
    db.enrollments.create_index = AsyncMock()
    db.lesson_progress = MagicMock()
    db.lesson_progress.create_index = AsyncMock()
    db.chat_messages = MagicMock()
    db.chat_messages.create_index = AsyncMock()
    monkeypatch.setattr(app, "db", db)
    return db


@pytest.mark.asyncio
async def test_admin_password_is_reset_when_changed(mock_db, monkeypatch):
    monkeypatch.setattr(app, "ADMIN_PASSWORD", "new-password")
    mock_db.users.find_one.return_value = {
        "email": app.ADMIN_EMAIL,
        "password_hash": "old-hash",
    }
    with patch.object(app, "verify_password", return_value=False):
        await app.initialize_database()

    mock_db.users.update_one.assert_awaited_once()
    args, kwargs = mock_db.users.update_one.await_args
    assert args[0] == {"email": app.ADMIN_EMAIL}
    assert "password_hash" in args[1]["$set"]


@pytest.mark.asyncio
async def test_admin_password_is_not_changed_when_unchanged(mock_db, monkeypatch):
    monkeypatch.setattr(app, "ADMIN_PASSWORD", "same-password")
    mock_db.users.find_one.return_value = {
        "email": app.ADMIN_EMAIL,
        "password_hash": "old-hash",
    }
    with patch.object(app, "verify_password", return_value=True):
        await app.initialize_database()

    mock_db.users.update_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_admin_is_created_when_missing_and_password_set(mock_db, monkeypatch):
    monkeypatch.setattr(app, "ADMIN_PASSWORD", "admin-password")
    mock_db.users.find_one.return_value = None
    await app.initialize_database()

    mock_db.users.insert_one.assert_awaited_once()
    args, kwargs = mock_db.users.insert_one.await_args
    assert args[0]["email"] == app.ADMIN_EMAIL
    assert args[0]["role"] == "admin"
    assert "password_hash" in args[0]


@pytest.mark.asyncio
async def test_admin_is_not_created_when_password_not_set(mock_db, monkeypatch):
    monkeypatch.setattr(app, "ADMIN_PASSWORD", None)
    mock_db.users.find_one.return_value = None
    await app.initialize_database()

    mock_db.users.insert_one.assert_not_awaited()
    mock_db.users.update_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_initialize_database_with_retry_succeeds_after_transient_failure(
    mock_db, monkeypatch
):
    monkeypatch.setattr(app, "_database_initialized", False)
    attempts = {"count": 0}

    async def flaky_initialize():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise PyMongoError("connection refused")

    monkeypatch.setattr(app, "initialize_database", flaky_initialize)

    await app._initialize_database_with_retry(max_attempts=3, base_delay=0)

    assert attempts["count"] == 2
    assert app._database_initialized is True


@pytest.mark.asyncio
async def test_initialize_database_with_retry_keeps_app_alive_after_exhausted_retries(
    mock_db, monkeypatch
):
    monkeypatch.setattr(app, "_database_initialized", False)

    async def always_fail():
        raise PyMongoError("connection refused")

    monkeypatch.setattr(app, "initialize_database", always_fail)

    await app._initialize_database_with_retry(max_attempts=2, base_delay=0)

    assert app._database_initialized is False


@pytest.mark.asyncio
async def test_ready_returns_503_until_database_initialized(monkeypatch):
    monkeypatch.setattr(app, "_database_initialized", False)

    with pytest.raises(HTTPException) as exc_info:
        await app.ready()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Database initialization pending"
