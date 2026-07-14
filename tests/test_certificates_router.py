from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from models import CertificateCreate, CertificateCustomize, CertificatePreview
from routers import certificates as certificates_router

COURSE_A = "507f1f77bcf86cd7994390c0"
STUDENT_A = "507f1f77bcf86cd7994390d0"
STUDENT_B = "507f1f77bcf86cd7994390e0"
COMPANY_A = "507f1f77bcf86cd7994390a0"
COMPANY_B = "507f1f77bcf86cd7994390b0"
TEMPLATE_A = "507f1f77bcf86cd7994390f0"


async def _fake_admin(_request):
    return {"id": "admin-id", "role": "admin", "company_id": None}


async def _fake_manager_a(_request):
    return {"id": "manager-id", "role": "client_manager", "company_id": COMPANY_A}


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.users = MagicMock()
    mock_db.certificates = MagicMock()
    mock_db.certificate_templates = MagicMock()
    mock_db.courses.find_one = AsyncMock()
    mock_db.users.find_one = AsyncMock()
    mock_db.certificates.find_one = AsyncMock()
    mock_db.certificates.insert_one = AsyncMock()
    mock_db.certificate_templates.find_one = AsyncMock(return_value=None)
    mock_db.platform_settings = MagicMock()
    mock_db.platform_settings.find_one = AsyncMock(
        return_value={"_id": "certificate", "id_format": "CERT-{year}-{seq:6}", "sequence": 6}
    )
    mock_db.platform_settings.find_one_and_update = AsyncMock(
        return_value={"_id": "certificate", "id_format": "CERT-{year}-{seq:6}", "sequence": 7}
    )
    return mock_db


@pytest.mark.asyncio
async def test_create_certificate_as_admin(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = None
    mock_db.certificates.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    send_email = AsyncMock()
    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", send_email)

    response = await certificates_router.create_certificate(
        CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=92),
        request=object(),
    )

    assert response["course_id"] == COURSE_A
    assert response["user_name"] == "Student A"
    assert response["score"] == 92
    assert response["template"] == "default"
    assert response["certificate_id"] == "CERT-2026-000007"
    assert response["valid_until"] is not None
    assert response["is_expired"] is False
    send_email.assert_awaited_once()
    inserted_doc = mock_db.certificates.insert_one.await_args.args[0]
    assert inserted_doc["course_title"] == "Security Training"
    assert inserted_doc["user_id"] == STUDENT_A
    assert inserted_doc["template_id"] is None
    assert inserted_doc["valid_until"] is not None
    assert "<!DOCTYPE html" in inserted_doc["template_html"]


@pytest.mark.asyncio
async def test_create_certificate_uses_course_language(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
        "language": "ja",
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = None
    mock_db.certificates.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    response = await certificates_router.create_certificate(
        CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=92),
        request=object(),
    )

    assert response["language"] == "ja"
    inserted_doc = mock_db.certificates.insert_one.await_args.args[0]
    assert inserted_doc["language"] == "ja"
    assert "修了証明書" in inserted_doc["template_html"]


@pytest.mark.asyncio
async def test_create_certificate_language_override_takes_precedence(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
        "language": "ja",
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = None
    mock_db.certificates.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    response = await certificates_router.create_certificate(
        CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=92, language="ko"),
        request=object(),
    )

    assert response["language"] == "ko"


@pytest.mark.asyncio
async def test_create_certificate_defaults_language_to_english_when_course_has_none(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = None
    mock_db.certificates.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    response = await certificates_router.create_certificate(
        CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=92),
        request=object(),
    )

    assert response["language"] == "en"


@pytest.mark.asyncio
async def test_create_certificate_with_selected_template(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = None
    mock_db.certificate_templates.find_one.return_value = {
        "_id": ObjectId(TEMPLATE_A),
        "name": "Executive Certificate",
        "html": "<html><body>{{user_name}} - {{course_title}} - {{score}}%</body></html>",
        "primary_color": "#111111",
        "secondary_color": "#222222",
        "is_default": False,
    }
    mock_db.certificates.insert_one.return_value = MagicMock(inserted_id=ObjectId())

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    response = await certificates_router.create_certificate(
        CertificateCreate(
            course_id=COURSE_A,
            user_id=STUDENT_A,
            score=92,
            template_id=TEMPLATE_A,
        ),
        request=object(),
    )

    assert response["template_id"] == TEMPLATE_A
    assert response["template_name"] == "Executive Certificate"
    assert response["template"] == "Executive Certificate"
    assert response["primary_color"] == "#111111"
    inserted_doc = mock_db.certificates.insert_one.await_args.args[0]
    assert inserted_doc["template_id"] == TEMPLATE_A
    assert inserted_doc["template_html"] == (
        "<html><body>Student A - Security Training - 92%</body></html>"
    )


@pytest.mark.asyncio
async def test_create_certificate_rejects_duplicate(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }
    mock_db.certificates.find_one.return_value = {"_id": ObjectId()}

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await certificates_router.create_certificate(
            CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=92),
            request=object(),
        )

    assert exc_info.value.status_code == 409
    mock_db.certificates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_cannot_create_certificate_for_other_company_student(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_B),
        "name": "Student B",
        "email": "student.b@example.com",
        "role": "student",
        "company_id": COMPANY_B,
    }

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_manager_a)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await certificates_router.create_certificate(
            CertificateCreate(course_id=COURSE_A, user_id=STUDENT_B, score=88),
            request=object(),
        )

    assert exc_info.value.status_code == 403
    mock_db.certificates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_manager_cannot_create_certificate_for_unassigned_course(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_B],
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "email": "student.a@example.com",
        "role": "student",
        "company_id": COMPANY_A,
    }

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_manager_a)
    monkeypatch.setattr(certificates_router, "send_certificate_email", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        await certificates_router.create_certificate(
            CertificateCreate(course_id=COURSE_A, user_id=STUDENT_A, score=90),
            request=object(),
        )

    assert exc_info.value.status_code == 403
    mock_db.certificates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_certificates_as_admin(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificates.find.return_value = _cursor_mock([
        {
            "_id": ObjectId(),
            "certificate_id": "ABC12345",
            "course_id": COURSE_A,
            "course_title": "Security Training",
            "user_id": STUDENT_A,
            "user_name": "Student A",
            "score": 92,
            "template": "default",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "issued_at": "2026-07-12T00:00:00+00:00",
        }
    ])
    mock_db.courses.find.return_value = _cursor_mock([
        {"_id": ObjectId(COURSE_A), "title": "Security Training"}
    ])

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)

    result = await certificates_router.list_certificates(request=object())

    assert len(result) == 1
    assert result[0]["certificate_id"] == "ABC12345"
    assert result[0]["course_title"] == "Security Training"
    assert result[0]["user_name"] == "Student A"


@pytest.mark.asyncio
async def test_list_certificates_scoped_to_manager_company(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.certificates.find.return_value = _cursor_mock([
        {
            "_id": ObjectId(),
            "certificate_id": "XYZ98765",
            "course_id": COURSE_A,
            "course_title": "Company Training",
            "user_id": STUDENT_A,
            "user_name": "Student A",
            "score": 88,
            "template": "default",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "issued_at": "2026-07-12T00:00:00+00:00",
        }
    ])
    mock_db.courses.find.return_value = _cursor_mock([
        {"_id": ObjectId(COURSE_A), "title": "Company Training"}
    ])
    mock_db.users.find.return_value = _cursor_mock([
        {"_id": ObjectId(STUDENT_A), "company_id": COMPANY_A}
    ])

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_manager_a)

    result = await certificates_router.list_certificates(request=object())

    assert len(result) == 1
    assert result[0]["certificate_id"] == "XYZ98765"
    mock_db.certificates.find.assert_called_once()
    query = mock_db.certificates.find.call_args.args[0]
    assert query["user_id"]["$in"] == [STUDENT_A]


def _fake_admin_require_roles(*_roles):
    async def _inner(_request):
        return {"id": "admin-id", "role": "admin", "company_id": None}

    return _inner


@pytest.mark.asyncio
async def test_customize_certificate_updates_language(monkeypatch):
    mock_db = _build_mock_db()
    existing_cert = {
        "_id": ObjectId(),
        "course_id": COURSE_A,
        "certificate_id": "ABC12345",
        "user_name": "Student A",
        "course_title": "Security Training",
        "score": 92,
        "language": "en",
        "template": "default",
        "primary_color": "#002FA7",
        "secondary_color": "#0A0B10",
        "background": "plain",
    }
    mock_db.certificates.find_one.return_value = existing_cert
    mock_db.certificates.update_one = AsyncMock()

    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_roles", _fake_admin_require_roles)

    result = await certificates_router.customize_certificate(
        str(existing_cert["_id"]),
        CertificateCustomize(language="ja"),
        request=object(),
    )

    assert result["message"] == "Updated 1 certificate(s)"
    update_call = mock_db.certificates.update_one.await_args.args[1]
    assert update_call["$set"]["language"] == "ja"
    assert "修了証明書" in update_call["$set"]["template_html"]


@pytest.mark.asyncio
async def test_preview_certificate_with_sample_data_returns_html(monkeypatch):
    mock_db = _build_mock_db()
    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)

    response = await certificates_router.preview_certificate(
        CertificatePreview(
            course_title="Security Training",
            user_name="Jane Doe",
            score=95,
            language="ja",
            format="html",
        ),
        request=object(),
    )

    assert response.media_type == "text/html"
    html = response.body.decode("utf-8")
    assert "Jane Doe" in html
    assert "Security Training" in html
    assert "95%" in html
    assert "修了証明書" in html
    assert "CERT-2026-000007" in html
    mock_db.certificates.insert_one.assert_not_awaited()
    mock_db.platform_settings.find_one_and_update.assert_not_awaited()


@pytest.mark.asyncio
async def test_preview_certificate_with_real_course_and_student(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Advanced Security Training",
        "company_ids": [COMPANY_A],
        "language": "ko",
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_A),
        "name": "Student A",
        "role": "student",
        "company_id": COMPANY_A,
    }
    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)

    response = await certificates_router.preview_certificate(
        CertificatePreview(course_id=COURSE_A, user_id=STUDENT_A, score=88),
        request=object(),
    )

    html = response.body.decode("utf-8")
    assert "Student A" in html
    assert "Advanced Security Training" in html
    assert "수료증" in html
    assert "88%" in html
    mock_db.certificates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_preview_certificate_pdf_format(monkeypatch):
    mock_db = _build_mock_db()
    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_admin)

    response = await certificates_router.preview_certificate(
        CertificatePreview(
            course_title="Security Training",
            user_name="Jane Doe",
            format="pdf",
        ),
        request=object(),
    )

    assert response.media_type == "application/pdf"
    assert response.body[:4] == b"%PDF"
    mock_db.certificates.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_preview_certificate_manager_cannot_preview_other_company(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one.return_value = {
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "company_ids": [COMPANY_A],
        "language": "en",
    }
    mock_db.users.find_one.return_value = {
        "_id": ObjectId(STUDENT_B),
        "name": "Student B",
        "role": "student",
        "company_id": COMPANY_B,
    }
    monkeypatch.setattr(certificates_router, "db", mock_db)
    monkeypatch.setattr(certificates_router, "require_admin_or_manager", _fake_manager_a)

    with pytest.raises(HTTPException) as exc_info:
        await certificates_router.preview_certificate(
            CertificatePreview(course_id=COURSE_A, user_id=STUDENT_B, score=90),
            request=object(),
        )

    assert exc_info.value.status_code == 403


def _cursor_mock(items):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=items)
    return cursor
