from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from enrollment_utils import (
    enroll_company_students_in_course,
    enroll_user_in_assigned_company_courses,
)


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *_args, **_kwargs):
        return self

    async def to_list(self, _limit):
        return self._docs


@pytest.fixture
def mock_db(monkeypatch):
    db = MagicMock()
    db.enrollments = MagicMock()
    db.enrollments.find_one = AsyncMock(return_value=None)
    db.enrollments.find = MagicMock(return_value=FakeCursor([]))
    db.enrollments.insert_one = AsyncMock()
    db.enrollments.insert_many = AsyncMock()
    db.courses = MagicMock()
    db.courses.find = MagicMock(return_value=FakeCursor([]))
    monkeypatch.setattr("enrollment_utils.db", db)
    return db


@pytest.fixture
def mock_email(monkeypatch):
    send_email = AsyncMock()
    monkeypatch.setattr("enrollment_utils.send_enrollment_email", send_email)
    return send_email


@pytest.mark.asyncio
async def test_enroll_student_in_assigned_company_course(mock_db, mock_email):
    company_id = "507f1f77bcf86cd799439011"
    course_id = "507f1f77bcf86cd799439012"
    user_id = "507f1f77bcf86cd799439013"

    mock_db.courses.find.return_value = FakeCursor([{
        "_id": ObjectId(course_id),
        "title": "Security Basics",
        "company_ids": [company_id],
    }])

    user = {
        "_id": ObjectId(user_id),
        "role": "student",
        "company_id": company_id,
        "email": "student@example.com",
        "name": "Student",
    }

    enrolled = await enroll_user_in_assigned_company_courses(user)

    assert enrolled == [course_id]
    mock_db.enrollments.insert_many.assert_awaited_once()
    mock_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_enroll_client_manager_in_assigned_company_course(mock_db, mock_email):
    company_id = "507f1f77bcf86cd799439011"
    course_id = "507f1f77bcf86cd799439012"
    user_id = "507f1f77bcf86cd799439013"

    mock_db.courses.find.return_value = FakeCursor([{
        "_id": ObjectId(course_id),
        "title": "Security Basics",
        "company_ids": [company_id],
    }])

    user = {
        "_id": ObjectId(user_id),
        "role": "client_manager",
        "company_id": company_id,
        "email": "manager@example.com",
        "name": "Manager",
    }

    enrolled = await enroll_user_in_assigned_company_courses(user)

    assert enrolled == [course_id]
    mock_db.enrollments.insert_many.assert_awaited_once()
    mock_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_skip_admin_for_company_course_assignment(mock_db, mock_email):
    company_id = "507f1f77bcf86cd799439011"

    user = {
        "_id": ObjectId("507f1f77bcf86cd799439013"),
        "role": "admin",
        "company_id": company_id,
        "email": "admin@example.com",
        "name": "Admin",
    }

    enrolled = await enroll_user_in_assigned_company_courses(user)

    assert enrolled == []
    mock_db.enrollments.insert_many.assert_not_awaited()
    mock_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_skip_user_without_company(mock_db, mock_email):
    user = {
        "_id": ObjectId("507f1f77bcf86cd799439013"),
        "role": "student",
        "email": "student@example.com",
        "name": "Student",
    }

    enrolled = await enroll_user_in_assigned_company_courses(user)

    assert enrolled == []
    mock_db.courses.find.assert_not_called()
    mock_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_enroll_company_students_includes_client_managers(mock_db, mock_email):
    company_id = "507f1f77bcf86cd799439011"
    course_id = "507f1f77bcf86cd799439012"
    student_id = "507f1f77bcf86cd799439013"
    manager_id = "507f1f77bcf86cd799439014"

    mock_db.users = MagicMock()
    mock_db.users.find.return_value = FakeCursor([
        {
            "_id": ObjectId(student_id),
            "role": "student",
            "company_id": company_id,
            "email": "student@example.com",
            "name": "Student",
        },
        {
            "_id": ObjectId(manager_id),
            "role": "client_manager",
            "company_id": company_id,
            "email": "manager@example.com",
            "name": "Manager",
        },
    ])

    course = {
        "_id": ObjectId(course_id),
        "title": "Security Basics",
        "company_ids": [company_id],
    }

    enrolled = await enroll_company_students_in_course(course, course_id, [company_id])

    assert set(enrolled) == {student_id, manager_id}
    mock_db.enrollments.insert_many.assert_awaited_once()
    inserted_docs = mock_db.enrollments.insert_many.await_args[0][0]
    assert {doc["user_id"] for doc in inserted_docs} == {student_id, manager_id}
    assert mock_email.await_count == 2
