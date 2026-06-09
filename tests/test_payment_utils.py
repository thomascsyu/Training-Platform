import asyncio
from unittest.mock import AsyncMock, patch

from payment_utils import enroll_user_after_payment


def test_enroll_user_after_payment_skips_existing():
    transaction = {"course_id": "c1", "user_id": "u1"}
    with patch("payment_utils.db") as mock_db:
        mock_db.enrollments.find_one = AsyncMock(return_value={"_id": "existing"})
        result = asyncio.run(enroll_user_after_payment(transaction))
    assert result is False


def test_enroll_user_after_payment_creates_enrollment():
    transaction = {
        "course_id": "507f1f77bcf86cd799439011",
        "user_id": "507f1f77bcf86cd799439012",
    }
    with patch("payment_utils.db") as mock_db, patch(
        "payment_utils.send_enrollment_email", new_callable=AsyncMock
    ) as mock_email:
        mock_db.enrollments.find_one = AsyncMock(return_value=None)
        mock_db.enrollments.insert_one = AsyncMock()
        mock_db.users.find_one = AsyncMock(
            return_value={"email": "u@test.com", "name": "User"}
        )
        mock_db.courses.find_one = AsyncMock(return_value={"title": "Course"})
        result = asyncio.run(enroll_user_after_payment(transaction))
    assert result is True
    mock_email.assert_awaited_once()
