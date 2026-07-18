from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from models import CourseUpdate
from routers import courses as courses_router

ADMIN_ID = "507f1f77bcf86cd7994390a0"
COURSE_ID = "507f1f77bcf86cd7994390c0"


def _fake_require_roles(*_roles):
    async def checker(_request):
        return {"id": ADMIN_ID, "role": "admin"}

    return checker


def test_resolve_course_type_infers_paid_when_price_is_positive():
    is_free, price, course_type = courses_router._resolve_course_type(None, 25.0, None)
    assert is_free is False
    assert price == 25.0
    assert course_type == "payment_required"


def test_resolve_course_type_force_free_zeroes_price():
    is_free, price, course_type = courses_router._resolve_course_type(None, 25.0, "free")
    assert is_free is True
    assert price == 0.0
    assert course_type == "free"


@pytest.mark.asyncio
async def test_update_course_price_only_switches_to_paid(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.courses.find_one = AsyncMock(
        return_value={
            "_id": ObjectId(COURSE_ID),
            "is_free": True,
            "price": 0.0,
            "course_type": "free",
        }
    )
    mock_db.courses.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    monkeypatch.setattr(courses_router, "db", mock_db)
    monkeypatch.setattr(courses_router, "require_roles", _fake_require_roles)

    await courses_router.update_course(
        COURSE_ID,
        CourseUpdate(price=25.0),
        request=object(),
    )

    update_payload = mock_db.courses.update_one.await_args.args[1]["$set"]
    assert update_payload["is_free"] is False
    assert update_payload["price"] == 25.0
    assert update_payload["course_type"] == "payment_required"


@pytest.mark.asyncio
async def test_update_course_is_free_only_zeroes_price(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.courses.find_one = AsyncMock(
        return_value={
            "_id": ObjectId(COURSE_ID),
            "is_free": False,
            "price": 99.0,
            "course_type": "payment_required",
        }
    )
    mock_db.courses.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    monkeypatch.setattr(courses_router, "db", mock_db)
    monkeypatch.setattr(courses_router, "require_roles", _fake_require_roles)

    await courses_router.update_course(
        COURSE_ID,
        CourseUpdate(is_free=True),
        request=object(),
    )

    update_payload = mock_db.courses.update_one.await_args.args[1]["$set"]
    assert update_payload["is_free"] is True
    assert update_payload["price"] == 0.0
    assert update_payload["course_type"] == "free"
