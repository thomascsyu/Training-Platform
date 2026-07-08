from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from routers import companies as companies_router
from routers import groups as groups_router
from routers import users as users_router

import auth_utils


COMPANY_A = "507f1f77bcf86cd7994390a0"
COMPANY_B = "507f1f77bcf86cd7994390b0"
COURSE_A = "507f1f77bcf86cd7994390c0"
USER_A = "507f1f77bcf86cd7994390d0"
USER_B = "507f1f77bcf86cd7994390e0"


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, _limit):
        return self._docs


async def _fake_admin(_request):
    return {"id": "admin-id", "role": "admin", "company_id": None}


async def _fake_manager_a(_request):
    return {"id": "manager-a-id", "role": "client_manager", "company_id": COMPANY_A}


async def _fake_manager_no_company(_request):
    return {"id": "manager-none-id", "role": "client_manager", "company_id": None}


@pytest.mark.asyncio
async def test_get_users_scoped_to_manager_company(monkeypatch):
    mock_db = MagicMock()
    mock_db.users.find.return_value = FakeCursor([])

    monkeypatch.setattr(users_router, "db", mock_db)
    monkeypatch.setattr(users_router, "require_admin_or_manager", _fake_manager_a)

    await users_router.get_users(request=object())
    assert mock_db.users.find.call_args[0][0] == {"company_id": COMPANY_A}


@pytest.mark.asyncio
async def test_get_users_allows_admin_to_filter_by_company(monkeypatch):
    mock_db = MagicMock()
    mock_db.users.find.return_value = FakeCursor([])
    mock_db.companies.find_one = AsyncMock(return_value={"_id": ObjectId(COMPANY_A)})

    monkeypatch.setattr(users_router, "db", mock_db)
    monkeypatch.setattr(users_router, "require_admin_or_manager", _fake_admin)

    await users_router.get_users(request=object(), company_id=COMPANY_A)
    assert mock_db.users.find.call_args[0][0] == {"company_id": COMPANY_A}


@pytest.mark.asyncio
async def test_require_admin_or_manager_accepts_admin(monkeypatch):
    monkeypatch.setattr(auth_utils, "get_current_user", _fake_admin)

    user = await auth_utils.require_admin_or_manager(object())
    assert user["role"] == "admin"


@pytest.mark.asyncio
async def test_require_admin_or_manager_accepts_assigned_manager(monkeypatch):
    monkeypatch.setattr(auth_utils, "get_current_user", _fake_manager_a)

    user = await auth_utils.require_admin_or_manager(object())
    assert user["role"] == "client_manager"
    assert user["company_id"] == COMPANY_A


@pytest.mark.asyncio
async def test_require_admin_or_manager_rejects_unassigned_manager(monkeypatch):
    monkeypatch.setattr(auth_utils, "get_current_user", _fake_manager_no_company)

    with pytest.raises(HTTPException) as exc_info:
        await auth_utils.require_admin_or_manager(object())

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_list_companies_scoped_to_manager_company(monkeypatch):
    mock_db = MagicMock()
    mock_db.companies.find_one = AsyncMock(return_value={
        "_id": ObjectId(COMPANY_A),
        "name": "Company A",
        "description": "",
        "created_at": "2026-07-08T12:00:00Z",
    })
    mock_db.courses.find.return_value = FakeCursor([])

    monkeypatch.setattr(companies_router, "db", mock_db)
    monkeypatch.setattr(companies_router, "require_admin_or_manager", _fake_manager_a)

    response = await companies_router.list_companies(request=object())
    assert len(response) == 1
    assert response[0]["id"] == COMPANY_A


@pytest.mark.asyncio
async def test_company_dashboard_blocks_manager_for_other_company(monkeypatch):
    mock_db = MagicMock()
    monkeypatch.setattr(companies_router, "db", mock_db)
    monkeypatch.setattr(companies_router, "require_admin_or_manager", _fake_manager_a)

    with pytest.raises(HTTPException) as exc_info:
        await companies_router.get_company_dashboard(COMPANY_B, request=object())

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_groups_overview_scoped_to_manager_company(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses.find.return_value = FakeCursor([
        {"_id": ObjectId(COURSE_A), "title": "Training A", "language": "en", "thumbnail_url": None},
    ])
    mock_db.enrollments.find.return_value = FakeCursor([
        {"user_id": USER_A, "course_id": COURSE_A, "completed": True, "score": 80},
        {"user_id": USER_B, "course_id": COURSE_A, "completed": False, "score": 0},
    ])
    mock_db.users.find.return_value = FakeCursor([
        {"_id": ObjectId(USER_A), "company_id": COMPANY_A},
    ])

    monkeypatch.setattr(groups_router, "db", mock_db)
    monkeypatch.setattr(groups_router, "require_admin_or_manager", _fake_manager_a)

    response = await groups_router.get_groups_overview(request=object())
    assert len(response) == 1
    assert response[0]["total_enrolled"] == 1
    assert response[0]["completed"] == 1


@pytest.mark.asyncio
async def test_course_group_progress_blocks_manager_for_other_company_course(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses.find_one = AsyncMock(return_value={
        "_id": ObjectId(COURSE_A),
        "title": "Other Course",
        "company_ids": [COMPANY_B],
    })

    monkeypatch.setattr(groups_router, "db", mock_db)
    monkeypatch.setattr(groups_router, "require_admin_or_manager", _fake_manager_a)

    with pytest.raises(HTTPException) as exc_info:
        await groups_router.get_course_group_progress(COURSE_A, request=object())

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_student_progress_blocks_manager_for_other_company_student(monkeypatch):
    mock_db = MagicMock()
    mock_db.users.find_one = AsyncMock(return_value={
        "_id": ObjectId(USER_B),
        "name": "Student B",
        "email": "b@co.com",
        "company_id": COMPANY_B,
    })

    monkeypatch.setattr(groups_router, "db", mock_db)
    monkeypatch.setattr(groups_router, "require_admin_or_manager", _fake_manager_a)

    with pytest.raises(HTTPException) as exc_info:
        await groups_router.get_student_progress(USER_B, request=object())

    assert exc_info.value.status_code == 403
