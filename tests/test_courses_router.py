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


def test_resolve_original_price_keeps_valid_special_offer():
    assert courses_router._resolve_original_price(120.0, 90.0, False) == 120.0


def test_resolve_original_price_clears_for_free_courses():
    assert courses_router._resolve_original_price(120.0, 0.0, True) is None


def test_resolve_original_price_rejects_invalid_when_strict():
    with pytest.raises(courses_router.HTTPException) as exc:
        courses_router._resolve_original_price(50.0, 90.0, False, strict=True)
    assert exc.value.status_code == 400


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
            "original_price": 149.0,
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
    assert update_payload["original_price"] is None


@pytest.mark.asyncio
async def test_update_course_sets_special_offer_original_price(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.courses.find_one = AsyncMock(
        return_value={
            "_id": ObjectId(COURSE_ID),
            "is_free": False,
            "price": 90.0,
            "course_type": "payment_required",
            "original_price": None,
        }
    )
    mock_db.courses.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    monkeypatch.setattr(courses_router, "db", mock_db)
    monkeypatch.setattr(courses_router, "require_roles", _fake_require_roles)

    await courses_router.update_course(
        COURSE_ID,
        CourseUpdate(original_price=120.0),
        request=object(),
    )

    update_payload = mock_db.courses.update_one.await_args.args[1]["$set"]
    assert update_payload["original_price"] == 120.0
    assert update_payload["price"] == 90.0


@pytest.mark.asyncio
async def test_update_course_clears_special_offer_original_price(monkeypatch):
    mock_db = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.courses.find_one = AsyncMock(
        return_value={
            "_id": ObjectId(COURSE_ID),
            "is_free": False,
            "price": 90.0,
            "course_type": "payment_required",
            "original_price": 120.0,
        }
    )
    mock_db.courses.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    monkeypatch.setattr(courses_router, "db", mock_db)
    monkeypatch.setattr(courses_router, "require_roles", _fake_require_roles)

    await courses_router.update_course(
        COURSE_ID,
        CourseUpdate(original_price=None),
        request=object(),
    )

    update_payload = mock_db.courses.update_one.await_args.args[1]["$set"]
    assert update_payload["original_price"] is None
