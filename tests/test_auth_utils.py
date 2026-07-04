import pytest

from auth_utils import (
    create_access_token,
    hash_password,
    normalize_email,
    verify_password,
)


def test_normalize_email_trims_and_lowercases():
    assert normalize_email("  User@Example.COM  ") == "user@example.com"
    assert normalize_email("user@example.com") == "user@example.com"


def test_hash_and_verify_password():
    hashed = hash_password("test-password-123")
    assert hashed != "test-password-123"
    assert verify_password("test-password-123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_create_access_token_contains_role():
    token = create_access_token("user-id-1", "user@test.com", "student")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3


def test_register_model_defaults_student_role():
    from models import UserCreate

    user = UserCreate(email="student@test.com", password="secret12", name="Student")
    assert user.role == "student"
