from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from routers import certificates as certificates_router

COURSE_A = "507f1f77bcf86cd7994390c0"
STUDENT_A = "507f1f77bcf86cd7994390d0"
COMPANY_A = "507f1f77bcf86cd7994390a0"


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
    return mock_db


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
    assert result[0]["valid_until"] is not None
    assert result[0]["is_expired"] is False


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


def _cursor_mock(items):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=items)
    return cursor
