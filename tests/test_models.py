import pytest
from pydantic import ValidationError

from models import UserCreate


def test_user_create_password_min_length():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.com", password="short", name="Test")


def test_user_create_accepts_valid_password():
    user = UserCreate(email="a@b.com", password="longenough", name="Test")
    assert user.password == "longenough"
