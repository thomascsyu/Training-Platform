from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from models import CertificateSettingsUpdate
from routers import certificate_settings as settings_router


def _fake_require_roles(*args, **kwargs):
    async def _checker(_request):
        return {"id": "admin-id", "role": "admin", "company_id": None}

    return _checker


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.platform_settings = MagicMock()
    mock_db.platform_settings.find_one = AsyncMock(return_value=None)
    mock_db.platform_settings.update_one = AsyncMock()
    return mock_db


@pytest.mark.asyncio
async def test_get_settings_returns_defaults_when_empty(monkeypatch):
    mock_db = _build_mock_db()
    monkeypatch.setattr(settings_router, "db", mock_db)
    monkeypatch.setattr(settings_router, "require_roles", _fake_require_roles)

    response = await settings_router.get_certificate_settings(request=object())

    assert response["id_format"] == "CERT-{year}-{seq:6}"
    assert response["default_background"] == "plain"
    assert response["next_sequence"] == 1
    assert response["sample_id"].startswith("CERT-")
    assert len(response["backgrounds"]) == 5


@pytest.mark.asyncio
async def test_update_settings_persists_valid_format(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.platform_settings.find_one = AsyncMock(
        return_value={
            "_id": "certificate",
            "id_format": "ORG-{year}-{seq:4}",
            "default_background": "waves",
            "sequence": 5,
        }
    )
    monkeypatch.setattr(settings_router, "db", mock_db)
    monkeypatch.setattr(settings_router, "require_roles", _fake_require_roles)

    response = await settings_router.update_certificate_settings(
        CertificateSettingsUpdate(id_format="ORG-{year}-{seq:4}", default_background="waves"),
        request=object(),
    )

    mock_db.platform_settings.update_one.assert_awaited_once()
    set_fields = mock_db.platform_settings.update_one.await_args.args[1]["$set"]
    assert set_fields["id_format"] == "ORG-{year}-{seq:4}"
    assert set_fields["default_background"] == "waves"
    assert response["next_sequence"] == 6
    assert response["sample_id"].startswith("ORG-")


@pytest.mark.asyncio
async def test_update_settings_rejects_bad_format(monkeypatch):
    mock_db = _build_mock_db()
    monkeypatch.setattr(settings_router, "db", mock_db)
    monkeypatch.setattr(settings_router, "require_roles", _fake_require_roles)

    with pytest.raises(HTTPException) as exc_info:
        await settings_router.update_certificate_settings(
            CertificateSettingsUpdate(id_format="BAD-{oops}"),
            request=object(),
        )

    assert exc_info.value.status_code == 422
    mock_db.platform_settings.update_one.assert_not_awaited()