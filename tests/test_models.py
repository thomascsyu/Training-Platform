import pytest
from pydantic import ValidationError

from models import (
    CompanyCreate,
    CompanyUpdate,
    CourseCreate,
    CourseUpdate,
    UserCreate,
)


def test_user_create_password_min_length():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short", name="Test")


def test_user_create_accepts_valid_password():
    user = UserCreate(email="a@b.com", password="longenough", name="Test")
    assert user.password == "longenough"


def test_course_create_defaults_to_no_assigned_companies():
    course = CourseCreate(title="Course", description="Description")
    assert course.company_ids == []
    assert course.ai_assistant_enabled is True
    assert course.ai_assistant_prompt is None
    assert course.auto_issue_certificate is True


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


def test_course_update_accepts_ai_assistant_settings():
    update = CourseUpdate(ai_assistant_enabled=False, ai_assistant_prompt="Use only course examples.")
    assert update.ai_assistant_enabled is False
    assert update.ai_assistant_prompt == "Use only course examples."


def test_company_create_defaults_to_no_assigned_trainings():
    company = CompanyCreate(name="Acme")
    assert company.training_ids == []


def test_company_update_accepts_training_assignments():
    update = CompanyUpdate(training_ids=["507f1f77bcf86cd799439011"])
    assert update.training_ids == ["507f1f77bcf86cd799439011"]


def test_course_update_accepts_auto_issue_certificate():
    update = CourseUpdate(auto_issue_certificate=False)
    assert update.auto_issue_certificate is False


def test_course_create_rejects_negative_price():
    with pytest.raises(ValidationError):
        CourseCreate(title="Course", description="Description", price=-1)


def test_course_update_rejects_negative_price():
    with pytest.raises(ValidationError):
        CourseUpdate(price=-0.01)


def test_course_create_accepts_special_offer_original_price():
    course = CourseCreate(
        title="Course",
        description="Description",
        price=90,
        original_price=120,
        course_type="payment_required",
        is_free=False,
    )
    assert course.original_price == 120


def test_course_create_rejects_original_price_not_higher_than_price():
    with pytest.raises(ValidationError):
        CourseCreate(
            title="Course",
            description="Description",
            price=90,
            original_price=90,
        )


def test_course_create_treats_zero_original_price_as_unset():
    course = CourseCreate(
        title="Course",
        description="Description",
        price=90,
        original_price=0,
    )
    assert course.original_price is None


def test_course_update_accepts_clearing_original_price():
    update = CourseUpdate(original_price=None)
    assert "original_price" in update.model_dump(exclude_unset=True)
    assert update.original_price is None
