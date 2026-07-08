import pytest
from pydantic import ValidationError

from models import CourseCreate, CourseUpdate, UserCreate


def test_user_create_password_min_length():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short", name="Test")


def test_user_create_accepts_valid_password():
    user = UserCreate(email="a@b.com", password="longenough", name="Test")
    assert user.password == "longenough"


def test_course_create_defaults_to_no_assigned_companies():
    course = CourseCreate(title="Course", description="Description")
    assert course.company_ids == []


def test_course_create_accepts_assigned_companies():
    course = CourseCreate(
        title="Course",
        description="Description",
        company_ids=["507f1f77bcf86cd799439011"],
    )
    assert course.company_ids == ["507f1f77bcf86cd799439011"]


def test_course_update_accepts_clearing_assigned_companies():
    update = CourseUpdate(company_ids=[])
    assert update.company_ids == []
