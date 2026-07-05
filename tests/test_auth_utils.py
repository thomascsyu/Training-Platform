import pytest
from starlette.responses import Response

from auth_utils import (
    clear_auth_cookies,
    create_access_token,
    hash_password,
    normalize_email,
    set_auth_cookies,
    verify_password,
)


def _cookie_attributes(response: Response):
    # Starlette stores multiple Set-Cookie headers as repeated raw header pairs.
    return [value.decode() for name, value in response.raw_headers if name.lower() == b"set-cookie"]


def test_set_auth_cookies_uses_configured_samesite(monkeypatch):
    monkeypatch.setattr("auth_utils.COOKIE_SAMESITE", "strict")
    response = Response()
    set_auth_cookies(response, "access-token", "refresh-token")
    cookies = _cookie_attributes(response)
    assert len(cookies) == 2
    assert all("SameSite=strict" in c for c in cookies)
    assert all("HttpOnly" in c for c in cookies)


def test_clear_auth_cookies_sets_zero_max_age(monkeypatch):
    monkeypatch.setattr("auth_utils.COOKIE_SAMESITE", "lax")
    response = Response()
    clear_auth_cookies(response)
    cookies = _cookie_attributes(response)
    assert len(cookies) == 2
    assert all("Max-Age=0" in c for c in cookies)


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
