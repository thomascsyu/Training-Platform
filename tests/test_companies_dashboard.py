from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from routers import companies as companies_router


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, _limit):
        return self._docs


async def _fake_require_admin_or_manager(_request):
    return {"id": "admin-id", "role": "admin", "company_id": None}


@pytest.mark.asyncio
async def test_company_dashboard_returns_user_training_progress(monkeypatch):
    company_id = "507f1f77bcf86cd799439011"
    course_id_1 = "507f1f77bcf86cd799439012"
    course_id_2 = "507f1f77bcf86cd799439013"
    user_id_1 = "507f1f77bcf86cd799439014"
    user_id_2 = "507f1f77bcf86cd799439015"

    mock_db = MagicMock()
    mock_db.companies.find_one = AsyncMock(
        return_value={
            "_id": ObjectId(company_id),
            "name": "Acme Corp",
            "description": "Enterprise customer",
            "created_at": "2026-07-08T12:00:00Z",
        }
    )
    mock_db.courses.find.return_value = FakeCursor([
        {
            "_id": ObjectId(course_id_1),
            "title": "Security Basics",
            "company_ids": [company_id],
        },
        {
            "_id": ObjectId(course_id_2),
            "title": "Data Privacy",
            "company_ids": [company_id],
        },
    ])
    mock_db.users.find.return_value = FakeCursor([
        {
            "_id": ObjectId(user_id_1),
            "name": "Alice",
            "email": "alice@example.com",
            "role": "student",
            "created_at": "2026-07-01T10:00:00Z",
        },
        {
            "_id": ObjectId(user_id_2),
            "name": "Bob",
            "email": "bob@example.com",
            "role": "student",
            "created_at": "2026-07-01T11:00:00Z",
        },
    ])
    mock_db.enrollments.find.return_value = FakeCursor([
        {
            "user_id": user_id_1,
            "course_id": course_id_1,
            "completed": True,
            "score": 92,
            "created_at": "2026-07-02T09:00:00Z",
            "completed_at": "2026-07-03T09:00:00Z",
        },
        {
            "user_id": user_id_2,
            "course_id": course_id_1,
            "completed": False,
            "score": 0,
            "created_at": "2026-07-02T10:00:00Z",
        },
        {
            "user_id": user_id_2,
            "course_id": course_id_2,
            "completed": False,
            "score": 0,
            "created_at": "2026-07-02T10:30:00Z",
        },
    ])
    mock_db.quiz_attempts.find.return_value = FakeCursor([
        {"user_id": user_id_2, "course_id": course_id_1},
        {"user_id": user_id_2, "course_id": course_id_2},
        {"user_id": user_id_2, "course_id": course_id_2},
    ])

    lesson_progress_mock = AsyncMock(side_effect=[
        {
            user_id_1: {"lessons_completed": 4, "total_lessons": 4, "progress_percent": 100},
            user_id_2: {"lessons_completed": 1, "total_lessons": 5, "progress_percent": 20},
        },
        {
            user_id_1: {"lessons_completed": 0, "total_lessons": 4, "progress_percent": 0},
            user_id_2: {"lessons_completed": 2, "total_lessons": 4, "progress_percent": 50},
        },
    ])

    monkeypatch.setattr(companies_router, "db", mock_db)
    monkeypatch.setattr(companies_router, "require_admin_or_manager", _fake_require_admin_or_manager)
    monkeypatch.setattr(
        companies_router,
        "get_bulk_lesson_progress",
        lesson_progress_mock,
    )

    response = await companies_router.get_company_dashboard(company_id, request=object())

    assert response["company"]["id"] == company_id
    assert response["summary"] == {
        "total_users": 2,
        "total_trainings": 2,
        "total_assignments": 4,
        "completed_assignments": 1,
        "in_progress_assignments": 2,
        "not_started_assignments": 1,
        "completion_rate": 25.0,
        "average_progress_percent": 42.5,
    }

    assert len(response["users"]) == 2
    alice = response["users"][0]
    assert alice["user_name"] == "Alice"
    assert alice["summary"] == {
        "total_trainings": 2,
        "completed_trainings": 1,
        "in_progress_trainings": 0,
        "not_started_trainings": 1,
        "overall_progress_percent": 50.0,
    }
    assert alice["trainings"][0]["status"] == "completed"
    assert alice["trainings"][1]["status"] == "not_started"

    bob = response["users"][1]
    assert bob["user_name"] == "Bob"
    assert bob["summary"] == {
        "total_trainings": 2,
        "completed_trainings": 0,
        "in_progress_trainings": 2,
        "not_started_trainings": 0,
        "overall_progress_percent": 35.0,
    }
    assert bob["trainings"][0]["quiz_attempts"] == 1
    assert bob["trainings"][1]["quiz_attempts"] == 2


@pytest.mark.asyncio
async def test_company_dashboard_returns_404_for_unknown_company(monkeypatch):
    company_id = "507f1f77bcf86cd799439011"

    mock_db = MagicMock()
    mock_db.companies.find_one = AsyncMock(return_value=None)

    monkeypatch.setattr(companies_router, "db", mock_db)
    monkeypatch.setattr(companies_router, "require_admin_or_manager", _fake_require_admin_or_manager)

    with pytest.raises(HTTPException) as exc_info:
        await companies_router.get_company_dashboard(company_id, request=object())

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Company not found"
