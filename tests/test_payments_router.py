from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId
from fastapi import HTTPException

from models import PaymentCreate
from routers import payments as payments_router

ADMIN_ID = "507f1f77bcf86cd7994390a0"
STUDENT_ID = "507f1f77bcf86cd7994390b0"
COURSE_ID = "507f1f77bcf86cd7994390c0"


def _build_mock_db():
    mock_db = MagicMock()
    mock_db.payment_transactions = MagicMock()
    mock_db.users = MagicMock()
    mock_db.courses = MagicMock()
    mock_db.payment_transactions.find_one = AsyncMock()
    mock_db.payment_transactions.count_documents = AsyncMock()
    return mock_db


def _cursor_mock(items):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=items)
    return cursor


def _agg_cursor_mock(items):
    async def _generator():
        for item in items:
            yield item

    return _generator()


def _fake_require_roles(*roles):
    async def checker(_request):
        return {"id": ADMIN_ID, "role": "admin", "company_id": None}
    return checker


@pytest.mark.asyncio
async def test_list_transactions_returns_enriched_records(monkeypatch):
    mock_db = _build_mock_db()
    transaction = {
        "_id": ObjectId(),
        "session_id": "sess_123",
        "course_id": COURSE_ID,
        "user_id": STUDENT_ID,
        "amount": 99.99,
        "currency": "usd",
        "payment_status": "paid",
        "created_at": "2026-07-12T00:00:00+00:00",
    }
    mock_db.payment_transactions.find.return_value = _cursor_mock([transaction])
    mock_db.users.find.return_value = _cursor_mock([
        {"_id": ObjectId(STUDENT_ID), "name": "Student A"}
    ])
    mock_db.courses.find.return_value = _cursor_mock([
        {"_id": ObjectId(COURSE_ID), "title": "Stripe Course"}
    ])

    monkeypatch.setattr(payments_router, "db", mock_db)
    monkeypatch.setattr(payments_router, "require_roles", _fake_require_roles)

    result = await payments_router.list_transactions(request=object(), status="paid")

    assert len(result) == 1
    assert result[0]["session_id"] == "sess_123"
    assert result[0]["user_name"] == "Student A"
    assert result[0]["course_title"] == "Stripe Course"
    assert result[0]["amount"] == 99.99
    mock_db.payment_transactions.find.assert_called_once()


@pytest.mark.asyncio
async def test_get_transaction_detail_returns_record(monkeypatch):
    mock_db = _build_mock_db()
    transaction = {
        "_id": ObjectId(),
        "session_id": "sess_456",
        "course_id": COURSE_ID,
        "user_id": STUDENT_ID,
        "amount": 49.5,
        "currency": "usd",
        "payment_status": "pending",
        "created_at": "2026-07-12T00:00:00+00:00",
    }
    mock_db.payment_transactions.find_one.return_value = transaction
    mock_db.users.find_one = AsyncMock(return_value={
        "_id": ObjectId(STUDENT_ID), "name": "Student B"
    })
    mock_db.courses.find_one = AsyncMock(return_value={
        "_id": ObjectId(COURSE_ID), "title": "Another Course"
    })

    monkeypatch.setattr(payments_router, "db", mock_db)
    monkeypatch.setattr(payments_router, "require_roles", _fake_require_roles)

    result = await payments_router.get_transaction_detail("sess_456", request=object())

    assert result["session_id"] == "sess_456"
    assert result["user_name"] == "Student B"
    assert result["course_title"] == "Another Course"


@pytest.mark.asyncio
async def test_create_checkout_rejects_when_already_enrolled(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.courses.find_one = AsyncMock(
        return_value={"_id": ObjectId(COURSE_ID), "title": "Course", "price": 49.0, "is_free": False}
    )
    mock_db.enrollments = MagicMock()
    mock_db.enrollments.find_one = AsyncMock(return_value={"_id": "existing"})

    monkeypatch.setattr(payments_router, "db", mock_db)
    monkeypatch.setattr(payments_router, "STRIPE_API_KEY", "sk_test_123")
    monkeypatch.setattr(
        payments_router,
        "get_current_user",
        AsyncMock(return_value={"id": STUDENT_ID, "role": "student"}),
    )

    data = PaymentCreate(course_id=COURSE_ID, origin_url="https://example.com")

    with pytest.raises(HTTPException) as exc_info:
        await payments_router.create_checkout(data, request=object())

    assert exc_info.value.status_code == 400
    assert "already enrolled" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_payment_status_includes_receipt_info(monkeypatch):
    mock_db = _build_mock_db()
    transaction = {
        "_id": ObjectId(),
        "session_id": "sess_789",
        "course_id": COURSE_ID,
        "user_id": STUDENT_ID,
        "amount": 49.0,
        "currency": "usd",
        "payment_status": "paid",
    }
    mock_db.payment_transactions.find_one.return_value = transaction
    mock_db.courses.find_one = AsyncMock(
        return_value={"_id": ObjectId(COURSE_ID), "title": "Stripe Course"}
    )

    monkeypatch.setattr(payments_router, "db", mock_db)
    monkeypatch.setattr(payments_router, "STRIPE_API_KEY", "sk_test_123")
    monkeypatch.setattr(
        payments_router,
        "get_current_user",
        AsyncMock(return_value={"id": STUDENT_ID, "role": "student"}),
    )

    result = await payments_router.get_payment_status("sess_789", request=object())

    assert result["payment_status"] == "paid"
    assert result["course_id"] == COURSE_ID
    assert result["course_title"] == "Stripe Course"
    assert result["amount"] == 49.0
    assert result["currency"] == "usd"


@pytest.mark.asyncio
async def test_payments_summary_returns_counts_and_revenue(monkeypatch):
    mock_db = _build_mock_db()
    mock_db.payment_transactions.count_documents.side_effect = [10, 6, 4]
    mock_db.payment_transactions.aggregate = MagicMock(
        return_value=_agg_cursor_mock([{"_id": None, "revenue": 35.5}])
    )

    monkeypatch.setattr(payments_router, "db", mock_db)
    monkeypatch.setattr(payments_router, "require_roles", _fake_require_roles)

    result = await payments_router.payments_summary(request=object())

    assert result["total_transactions"] == 10
    assert result["paid_count"] == 6
    assert result["pending_count"] == 4
    assert result["total_revenue"] == 35.5
