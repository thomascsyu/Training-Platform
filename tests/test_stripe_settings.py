from unittest.mock import AsyncMock, MagicMock

import pytest

import stripe_settings
from models import StripeSettingsUpdate, StripeTestConnectionRequest
from routers import stripe_settings as stripe_settings_router


@pytest.fixture
def admin_user():
    return {"id": "admin-id", "email": "admin@learnhub.com", "role": "admin"}


@pytest.fixture
def mock_require_admin(monkeypatch, admin_user):
    async def _fake(*_args, **_kwargs):
        return admin_user

    monkeypatch.setattr(stripe_settings_router, "require_roles", lambda *_args, **_kwargs: _fake)


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.platform_settings = MagicMock()
    db.platform_settings.find_one = AsyncMock(return_value=None)
    db.platform_settings.replace_one = AsyncMock()
    monkeypatch.setattr(stripe_settings, "db", db)
    return db


@pytest.mark.asyncio
async def test_resolve_falls_back_to_env(mock_db, monkeypatch):
    monkeypatch.setattr(stripe_settings, "STRIPE_API_KEY", "sk_test_env")
    monkeypatch.setattr(stripe_settings, "STRIPE_WEBHOOK_SECRET", "whsec_env")

    creds = await stripe_settings.resolve_stripe_credentials()

    assert creds["api_key"] == "sk_test_env"
    assert creds["webhook_secret"] == "whsec_env"
    assert creds["api_key_source"] == "environment"
    assert creds["webhook_secret_source"] == "environment"


@pytest.mark.asyncio
async def test_resolve_prefers_database_over_env(mock_db, monkeypatch):
    import ai_settings

    monkeypatch.setattr(stripe_settings, "STRIPE_API_KEY", "sk_test_env")
    monkeypatch.setattr(stripe_settings, "STRIPE_WEBHOOK_SECRET", "whsec_env")
    monkeypatch.setattr(ai_settings, "SETTINGS_ENCRYPTION_KEY", "test-secret")
    monkeypatch.setattr(ai_settings, "JWT_SECRET", "test-jwt")

    mock_db.platform_settings.find_one.return_value = {
        "_id": "stripe",
        "api_key": ai_settings._encrypt_value("sk_test_db"),
        "webhook_secret": ai_settings._encrypt_value("whsec_db"),
    }

    creds = await stripe_settings.resolve_stripe_credentials()

    assert creds["api_key"] == "sk_test_db"
    assert creds["webhook_secret"] == "whsec_db"
    assert creds["api_key_source"] == "database"


@pytest.mark.asyncio
async def test_save_stripe_settings_encrypts(mock_db, monkeypatch):
    import ai_settings

    monkeypatch.setattr(ai_settings, "SETTINGS_ENCRYPTION_KEY", "test-secret")
    monkeypatch.setattr(ai_settings, "JWT_SECRET", "test-jwt")

    await stripe_settings.save_stripe_settings(
        {"api_key": "sk_test_save", "webhook_secret": "whsec_save"},
        user_id="admin-id",
    )

    mock_db.platform_settings.replace_one.assert_awaited_once()
    args, kwargs = mock_db.platform_settings.replace_one.await_args
    assert args[0] == {"_id": "stripe"}
    assert args[1]["api_key"].startswith("enc:")
    assert args[1]["webhook_secret"].startswith("enc:")
    assert kwargs.get("upsert") is True


@pytest.mark.asyncio
async def test_get_stripe_settings_returns_masked(mock_db, mock_require_admin, monkeypatch):
    monkeypatch.setattr(stripe_settings, "STRIPE_API_KEY", None)
    monkeypatch.setattr(stripe_settings, "STRIPE_WEBHOOK_SECRET", None)
    mock_db.platform_settings.find_one.return_value = {
        "_id": "stripe",
        "api_key": "sk_test_1234567890",
        "webhook_secret": "whsec_abcdef",
    }

    response = await stripe_settings_router.get_stripe_settings(request=object())

    assert response["api_key_configured"] is True
    assert "•" in response["api_key"]
    assert response["api_key_source"] == "database"
    assert response["webhook_secret_configured"] is True


@pytest.mark.asyncio
async def test_update_stripe_settings_saves(mock_db, mock_require_admin, monkeypatch):
    import ai_settings

    monkeypatch.setattr(ai_settings, "SETTINGS_ENCRYPTION_KEY", "test-secret")
    monkeypatch.setattr(ai_settings, "JWT_SECRET", "test-jwt")
    monkeypatch.setattr(stripe_settings, "STRIPE_API_KEY", None)
    monkeypatch.setattr(stripe_settings, "STRIPE_WEBHOOK_SECRET", None)

    # After save, load_masked reads find_one again — return encrypted doc
    async def fake_replace(query, doc, upsert=False):
        mock_db.platform_settings.find_one.return_value = doc

    mock_db.platform_settings.replace_one = AsyncMock(side_effect=fake_replace)

    response = await stripe_settings_router.update_stripe_settings(
        StripeSettingsUpdate(api_key="sk_test_newkey", webhook_secret="whsec_new"),
        request=object(),
    )

    assert response["api_key_configured"] is True
    assert response["api_key_source"] == "database"


@pytest.mark.asyncio
async def test_test_stripe_connection_without_key(mock_db, mock_require_admin, monkeypatch):
    monkeypatch.setattr(stripe_settings, "STRIPE_API_KEY", None)
    monkeypatch.setattr(
        stripe_settings, "get_stripe_api_key", AsyncMock(return_value="")
    )

    result = await stripe_settings_router.test_stripe_settings(
        StripeTestConnectionRequest(),
        request=object(),
    )

    assert result["connected"] is False
    assert "not configured" in result["error"].lower()
