import pytest
from pydantic import ValidationError

from models import (
    CertificateCreate,
    CertificatePreview,
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


def test_certificate_create_score_bounds():
    with pytest.raises(ValidationError):
        CertificateCreate(
            course_id="507f1f77bcf86cd799439011",
            user_id="507f1f77bcf86cd799439012",
            score=101,
        )

    cert = CertificateCreate(
        course_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        score=95,
    )
    assert cert.score == 95


def test_certificate_preview_accepts_sample_or_real_identifiers():
    sample = CertificatePreview(course_title="Security Training", user_name="Jane Doe")
    assert sample.format == "html"
    assert sample.score == 92

    real = CertificatePreview(
        course_id="507f1f77bcf86cd799439011",
        user_id="507f1f77bcf86cd799439012",
        format="pdf",
        language="ja",
    )
    assert real.format == "pdf"
    assert real.language == "ja"


def test_certificate_preview_requires_course_and_recipient():
    with pytest.raises(ValidationError):
        CertificatePreview(user_name="Jane Doe")
    with pytest.raises(ValidationError):
        CertificatePreview(course_title="Security Training")


def test_certificate_preview_rejects_invalid_format():
    with pytest.raises(ValidationError):
        CertificatePreview(
            course_title="Security Training",
            user_name="Jane Doe",
            format="docx",
        )
