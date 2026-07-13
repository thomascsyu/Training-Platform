from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from models import QuizAttemptCreate
from routers import quizzes as quizzes_router

QUIZ_A = "507f1f77bcf86cd7994390c1"
COURSE_A = "507f1f77bcf86cd7994390c0"
STUDENT_A = "507f1f77bcf86cd7994390d0"


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.quizzes = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.quiz_attempts = MagicMock()
    mock_db.enrollments = MagicMock()
    mock_db.certificates = MagicMock()
    mock_db.certificate_templates = MagicMock()

    mock_db.quizzes.find_one = AsyncMock(return_value={
        "_id": ObjectId(QUIZ_A),
        "course_id": COURSE_A,
        "questions": [{"correct_answer": 0}, {"correct_answer": 1}],
    })
    mock_db.quiz_attempts.insert_one = AsyncMock()
    mock_db.enrollments.update_one = AsyncMock()
    mock_db.certificates.find_one = AsyncMock(return_value=None)
    mock_db.certificates.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))
    mock_db.certificates.update_one = AsyncMock()
    mock_db.certificate_templates.find_one = AsyncMock(return_value=None)
    return mock_db


async def _fake_user(_request):
    return {"id": STUDENT_A, "name": "Student A", "email": "student.a@example.com", "role": "student"}


@pytest.mark.asyncio
async def test_submit_quiz_auto_issues_certificate_by_default(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one = AsyncMock(return_value={
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "passing_score": 70,
    })

    send_certificate_email = AsyncMock()
    monkeypatch.setattr(quizzes_router, "db", mock_db)
    monkeypatch.setattr(quizzes_router, "get_current_user", _fake_user)
    monkeypatch.setattr(quizzes_router, "require_enrollment", AsyncMock(return_value={"course_id": COURSE_A}))
    monkeypatch.setattr(quizzes_router, "send_certificate_email", send_certificate_email)
    monkeypatch.setattr(quizzes_router, "send_progress_email", AsyncMock())

    result = await quizzes_router.submit_quiz(
        QUIZ_A, QuizAttemptCreate(quiz_id=QUIZ_A, answers=[0, 1]), request=object()
    )

    assert result["passed"] is True
    mock_db.certificates.insert_one.assert_awaited_once()
    send_certificate_email.assert_awaited_once()
    inserted_doc = mock_db.certificates.insert_one.await_args.args[0]
    assert inserted_doc["course_id"] == COURSE_A
    assert inserted_doc["user_id"] == STUDENT_A


@pytest.mark.asyncio
async def test_submit_quiz_skips_certificate_when_auto_issue_disabled(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one = AsyncMock(return_value={
        "_id": ObjectId(COURSE_A),
        "title": "Security Training",
        "passing_score": 70,
        "auto_issue_certificate": False,
    })

    send_certificate_email = AsyncMock()
    monkeypatch.setattr(quizzes_router, "db", mock_db)
    monkeypatch.setattr(quizzes_router, "get_current_user", _fake_user)
    monkeypatch.setattr(quizzes_router, "require_enrollment", AsyncMock(return_value={"course_id": COURSE_A}))
    monkeypatch.setattr(quizzes_router, "send_certificate_email", send_certificate_email)
    monkeypatch.setattr(quizzes_router, "send_progress_email", AsyncMock())

    result = await quizzes_router.submit_quiz(
        QUIZ_A, QuizAttemptCreate(quiz_id=QUIZ_A, answers=[0, 1]), request=object()
    )

    assert result["passed"] is True
    mock_db.certificates.insert_one.assert_not_awaited()
    send_certificate_email.assert_not_awaited()
    mock_db.enrollments.update_one.assert_awaited_once()
    completed_update = mock_db.enrollments.update_one.await_args.args[1]
    assert completed_update["$set"]["completed"] is True
