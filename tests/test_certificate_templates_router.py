from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from models import (
    CertificateTemplateCreate,
    CertificateTemplateRender,
    CertificateTemplateUpdate,
    CourseCertificateSettingsUpdate,
)
from routers import certificate_templates as templates_router

TEMPLATE_A = "507f1f77bcf86cd7994390f0"
COURSE_A = "507f1f77bcf86cd7994390c0"


def _fake_require_roles(*args, **kwargs):
    async def _checker(_request):
        return {"id": "admin-id", "role": "admin", "company_id": None}

    return _checker


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.certificate_templates = MagicMock()
    mock_db.course_certificate_settings = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.certificate_templates.find = MagicMock()
    mock_db.certificate_templates.find_one = AsyncMock()
    mock_db.certificate_templates.insert_one = AsyncMock()
    mock_db.certificate_templates.update_one = AsyncMock()
    mock_db.certificate_templates.update_many = AsyncMock()
    mock_db.certificate_templates.delete_one = AsyncMock()
    mock_db.course_certificate_settings.find = MagicMock()
    mock_db.course_certificate_settings.find_one = AsyncMock()
    mock_db.course_certificate_settings.update_one = AsyncMock()
    mock_db.courses.find = MagicMock()
    mock_db.courses.find_one = AsyncMock()
    return mock_db


@pytest.mark.asyncio
async def test_list_templates_as_admin(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find.return_value.sort.return_value.to_list = AsyncMock(
        return_value=[{
            "_id": ObjectId(TEMPLATE_A),
            "name": "Default",
            "html": "<html></html>",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "is_default": True,
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }]
    )
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.list_templates(request=object())
    assert len(response) == 1
    assert response[0]["name"] == "Default"
    assert response[0]["is_default"] is True


@pytest.mark.asyncio
async def test_create_template_generates_default_html(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find_one.return_value = None
    mock_db.certificate_templates.insert_one.return_value = MagicMock(
        inserted_id=ObjectId(TEMPLATE_A)
    )

    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.create_template(
        CertificateTemplateCreate(name="Training Certificate"),
        request=object(),
    )

    assert response["name"] == "Training Certificate"
    assert "<!DOCTYPE html" in response["html"]
    assert "{{user_name}}" in response["html"]
    assert response["primary_color"] == "#002fa7"
    assert response["secondary_color"] == "#0a0b10"
    assert response["is_default"] is False
    mock_db.certificate_templates.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_template_rejects_duplicate_name(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find_one.return_value = {"_id": ObjectId()}
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    with pytest.raises(HTTPException) as exc_info:
        await templates_router.create_template(
            CertificateTemplateCreate(name="Existing Template"),
            request=object(),
        )

    assert exc_info.value.status_code == 409
    mock_db.certificate_templates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_unsets_other_defaults(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find_one.side_effect = [
        {
            "_id": ObjectId(TEMPLATE_A),
            "name": "A",
            "html": "<html>A</html>",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "is_default": False,
        },
        {
            "_id": ObjectId(TEMPLATE_A),
            "name": "A",
            "html": "<html>A</html>",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "is_default": True,
        },
    ]

    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.update_template(
        TEMPLATE_A,
        CertificateTemplateUpdate(is_default=True),
        request=object(),
    )

    assert response["is_default"] is True
    mock_db.certificate_templates.update_many.assert_awaited_once()


@pytest.mark.asyncio
async def test_render_default_template(monkeypatch):
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.render_default_template(
        CertificateTemplateRender(primary_color="#002FA7", secondary_color="#0A0B10"),
        request=object(),
    )

    assert "html" in response
    assert "<!DOCTYPE html" in response["html"]
    assert "{{course_title}}" in response["html"]


@pytest.mark.asyncio
async def test_list_course_certificate_settings(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find.return_value.sort.return_value.to_list = AsyncMock(
        return_value=[{
            "_id": ObjectId(COURSE_A),
            "title": "Security Training",
            "passing_score": 80,
        }]
    )
    mock_db.course_certificate_settings.find.return_value.to_list = AsyncMock(
        return_value=[{
            "_id": ObjectId(TEMPLATE_A),
            "course_id": COURSE_A,
            "primary_color": "#111111",
            "secondary_color": "#222222",
            "background_url": "https://example.com/art.png",
            "validity_days": 365,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }]
    )
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.list_course_certificate_settings(request=object())

    assert response == [{
        "course_id": COURSE_A,
        "course_title": "Security Training",
        "passing_score": 80,
        "primary_color": "#111111",
        "secondary_color": "#222222",
        "background_url": "https://example.com/art.png",
        "validity_days": 365,
        "updated_at": "2026-01-01T00:00:00+00:00",
    }]


@pytest.mark.asyncio
async def test_update_course_certificate_settings(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "passing_score": 80,
    }
    mock_db.course_certificate_settings.find_one.return_value = {
        "_id": ObjectId(TEMPLATE_A),
        "course_id": COURSE_A,
        "primary_color": "#111111",
        "secondary_color": "#222222",
        "background_url": "https://example.com/art.png",
        "validity_days": 365,
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.update_course_certificate_settings(
        COURSE_A,
        CourseCertificateSettingsUpdate(
            primary_color="#111111",
            secondary_color="#222222",
            background_url="https://example.com/art.png",
            validity_days=365,
        ),
        request=object(),
    )

    assert response["course_id"] == COURSE_A
    assert response["validity_days"] == 365
    mock_db.course_certificate_settings.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_preview_course_certificate(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "passing_score": 80,
    }
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.preview_course_certificate(
        COURSE_A,
        CourseCertificateSettingsUpdate(
            primary_color="#111111",
            secondary_color="#222222",
            background_url="https://example.com/art.png",
            validity_days=365,
        ),
        request=object(),
    )

    assert "<!DOCTYPE html" in response["html"]
    assert "Security Training" in response["html"]
    assert "https://example.com/art.png" in response["html"]


@pytest.mark.asyncio
async def test_delete_template_not_found(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.delete_one.return_value = MagicMock(deleted_count=0)
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    with pytest.raises(HTTPException) as exc_info:
        await templates_router.delete_template(TEMPLATE_A, request=object())

    assert exc_info.value.status_code == 404
