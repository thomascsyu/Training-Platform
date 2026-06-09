import pytest
from fastapi import HTTPException

from db_utils import parse_object_id


def test_parse_object_id_valid():
    oid = parse_object_id("507f1f77bcf86cd799439011", "user")
    assert str(oid) == "507f1f77bcf86cd799439011"


def test_parse_object_id_invalid():
    with pytest.raises(HTTPException) as exc:
        parse_object_id("not-an-id", "course")
    assert exc.value.status_code == 400
    assert "Invalid course id" in exc.value.detail
