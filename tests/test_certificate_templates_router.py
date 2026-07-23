from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException
from pydantic import ValidationError

from models import CertificateTemplateCreate, CertificateTemplateRender, CertificateTemplateUpdate
from routers import certificate_templates as templates_router

TEMPLATE_A = "507f1f77bcf86cd7994390f0"


def _fake_require_roles(*args, **kwargs):
    async def _checker(_request):
        return {"id": "admin-id", "role": "admin", "company_id": None}

    return _checker


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.certificate_templates = MagicMock()
    mock_db.certificate_templates.find = MagicMock()
    mock_db.certificate_templates.find_one = AsyncMock()
    mock_db.certificate_templates.insert_one = AsyncMock()
    mock_db.certificate_templates.update_one = AsyncMock()
    mock_db.certificate_templates.update_many = AsyncMock()
    mock_db.certificate_templates.delete_one = AsyncMock()
    mock_db.certificate_templates.count_documents = AsyncMock(return_value=0)
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
    assert response["background"] == "plain"
    assert response["is_default"] is False
    mock_db.certificate_templates.insert_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_template_with_custom_background(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find_one.return_value = None
    mock_db.certificate_templates.insert_one.return_value = MagicMock(
        inserted_id=ObjectId(TEMPLATE_A)
    )

    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.create_template(
        CertificateTemplateCreate(name="Waves Certificate", background="waves"),
        request=object(),
    )

    assert response["background"] == "waves"
    assert 'class="artwork"' in response["html"]


def test_certificate_template_create_rejects_invalid_background():
    with pytest.raises(ValidationError):
        CertificateTemplateCreate(name="Bad Background", background="not-a-real-style")


@pytest.mark.asyncio
async def test_create_template_rejects_when_at_template_limit(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.count_documents = AsyncMock(return_value=5)
    mock_db.certificate_templates.find_one.return_value = None
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    with pytest.raises(HTTPException) as exc_info:
        await templates_router.create_template(
            CertificateTemplateCreate(name="Sixth Template"),
            request=object(),
        )

    assert exc_info.value.status_code == 409
    assert "5" in exc_info.value.detail
    mock_db.certificate_templates.insert_one.assert_not_awaited()


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
async def test_create_template_with_builder_fields(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificate_templates.find_one.return_value = None
    mock_db.certificate_templates.insert_one.return_value = MagicMock(
        inserted_id=ObjectId(TEMPLATE_A)
    )
    mock_db.courses = MagicMock()
    mock_db.courses.find_one = AsyncMock(
        return_value={"_id": ObjectId("507f1f77bcf86cd799439011")}
    )
    mock_db.courses.update_one = AsyncMock()

    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    response = await templates_router.create_template(
        CertificateTemplateCreate(
            name="Course Builder Cert",
            course_id="507f1f77bcf86cd799439011",
            orientation="portrait",
            body_text="{{recipient_name}} completed {{course_title}}",
            background_image_url="/api/uploads/certificate-backgrounds/x.png",
            is_default=True,
        ),
        request=object(),
    )

    assert response["orientation"] == "portrait"
    assert response["course_id"] == "507f1f77bcf86cd799439011"
    assert response["is_default"] is False
    assert "{{recipient_name}}" in response["html"]
    assert "8.5in 11in" in response["html"]
    mock_db.courses.update_one.assert_awaited()
    mock_db = _build_mock_db()
    mock_db.certificate_templates.delete_one.return_value = MagicMock(deleted_count=0)
    monkeypatch.setattr(templates_router, "db", mock_db)
    monkeypatch.setattr(templates_router, "require_roles", _fake_require_roles)

    with pytest.raises(HTTPException) as exc_info:
        await templates_router.delete_template(TEMPLATE_A, request=object())

    assert exc_info.value.status_code == 404
