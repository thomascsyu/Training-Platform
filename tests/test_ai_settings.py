from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import ai_settings
from models import AISettingsUpdate, AITestConnectionRequest
from routers import ai_settings as ai_settings_router


@pytest.fixture
def admin_user():
    return {"id": "admin-id", "email": "admin@learnhub.com", "role": "admin"}


@pytest.fixture
def mock_require_admin(monkeypatch, admin_user):
    async def _fake(*_args, **_kwargs):
        return admin_user

    monkeypatch.setattr(ai_settings_router, "require_roles", lambda *_args, **_kwargs: _fake)


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.platform_settings = MagicMock()
    db.platform_settings.find_one = AsyncMock(return_value=None)
    db.platform_settings.replace_one = AsyncMock()
    monkeypatch.setattr(ai_settings, "db", db)
    return db


@pytest.mark.asyncio
async def test_load_ai_settings_returns_defaults_when_missing(mock_db):
    settings = await ai_settings.load_ai_settings()

    assert settings["default_provider"] == "deepseek"
    assert "deepseek" in settings["providers"]
    assert "xai" in settings["providers"]
    assert settings["providers"]["deepseek"]["model"] == "deepseek-chat"
    assert settings["providers"]["xai"]["model"] == "grok-3"


@pytest.mark.asyncio
async def test_save_ai_settings_encrypts_and_stores_keys(mock_db, monkeypatch):
    monkeypatch.setattr(ai_settings, "SETTINGS_ENCRYPTION_KEY", "test-secret")
    monkeypatch.setattr(ai_settings, "JWT_SECRET", "test-jwt")

    await ai_settings.save_ai_settings(
        {
            "default_provider": "xai",
            "providers": {
                "deepseek": {"api_key": "sk-deepseek", "model": "deepseek-v3", "enabled": False},
                "xai": {"api_key": "sk-xai", "model": "grok-3", "enabled": True},
            },
        },
        user_id="admin-id",
    )

    mock_db.platform_settings.replace_one.assert_awaited_once()
    args, kwargs = mock_db.platform_settings.replace_one.await_args
    assert args[0] == {"_id": "ai"}
    assert args[1]["default_provider"] == "xai"
    assert args[1]["providers"]["deepseek"]["model"] == "deepseek-v3"
    assert args[1]["providers"]["deepseek"]["enabled"] is False
    assert args[1]["providers"]["xai"]["enabled"] is True
    assert kwargs.get("upsert") is True
    # Keys should be encrypted with the configured prefix
    assert args[1]["providers"]["deepseek"]["api_key"].startswith("enc:")
    assert args[1]["providers"]["xai"]["api_key"].startswith("enc:")


@pytest.mark.asyncio
async def test_get_ai_settings_returns_masked_keys(mock_db, mock_require_admin):
    mock_db.platform_settings.find_one.return_value = {
        "_id": "ai",
        "default_provider": "deepseek",
        "providers": {
            "deepseek": {"api_key": "sk-deepseek-test-key", "model": "deepseek-chat", "enabled": True},
            "xai": {"api_key": "", "model": "grok-3", "enabled": False},
        },
    }

    response = await ai_settings_router.get_ai_settings(request=object())

    assert response["default_provider"] == "deepseek"
    assert response["providers"]["deepseek"]["api_key"].startswith("sk-d")
    assert "•" in response["providers"]["deepseek"]["api_key"]
    assert response["providers"]["xai"]["api_key"] == ""


@pytest.mark.asyncio
async def test_update_ai_settings_rejects_invalid_default_provider(
    mock_db, mock_require_admin
):
    with pytest.raises(HTTPException) as exc_info:
        await ai_settings_router.update_ai_settings(
            AISettingsUpdate(default_provider="openai"),
            request=object(),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_ai_settings_saves_and_returns_masked(
    mock_db, mock_require_admin, monkeypatch
):
    monkeypatch.setattr(ai_settings, "SETTINGS_ENCRYPTION_KEY", "test-secret")
    monkeypatch.setattr(ai_settings, "JWT_SECRET", "test-jwt")

    response = await ai_settings_router.update_ai_settings(
        AISettingsUpdate(
            default_provider="xai",
            providers={
                "deepseek": {"api_key": "", "model": "deepseek-chat", "enabled": True},
                "xai": {"api_key": "sk-xai", "model": "grok-3", "enabled": True},
            },
        ),
        request=object(),
    )

    mock_db.platform_settings.replace_one.assert_awaited_once()
    assert response is not None
    assert "providers" in response


@pytest.mark.asyncio
async def test_test_ai_connection_rejects_invalid_provider(mock_require_admin):
    with pytest.raises(HTTPException) as exc_info:
        await ai_settings_router.test_ai_connection(
            AITestConnectionRequest(provider="openai"),
            request=object(),
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_test_ai_connection_returns_provider_result(mock_require_admin, monkeypatch):
    async def fake_test(provider, override_key=None):
        return {
            "provider": provider,
            "connected": True,
            "model": "grok-3",
            "latency_ms": 120,
            "message": "OK",
        }

    monkeypatch.setattr(ai_settings_router, "test_provider_connection", fake_test)

    response = await ai_settings_router.test_ai_connection(
        AITestConnectionRequest(provider="xai"),
        request=object(),
    )

    assert response["provider"] == "xai"
    assert response["connected"] is True
    assert response["latency_ms"] == 120


@pytest.mark.asyncio
async def test_get_ai_settings_blocks_non_admin(monkeypatch, mock_db):
    async def _reject(*_args, **_kwargs):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    monkeypatch.setattr(ai_settings_router, "require_roles", lambda *_args, **_kwargs: _reject)

    with pytest.raises(HTTPException) as exc_info:
        await ai_settings_router.get_ai_settings(request=object())

    assert exc_info.value.status_code == 403


def test_mask_key_masks_middle_and_handles_empty():
    assert ai_settings._mask_key("") == ""
    assert ai_settings._mask_key("short") == "•••••"
    assert ai_settings._mask_key("sk-1234567890abcdef") == "sk-1••••cdef"
