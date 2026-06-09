from datetime import datetime, timezone

from database import db
from db_utils import parse_object_id
from email_service import send_enrollment_email


async def enroll_user_after_payment(transaction: dict) -> bool:
    """Create enrollment and send welcome email when payment is confirmed. Returns True if newly enrolled."""
    course_id = transaction["course_id"]
    user_id = transaction["user_id"]

    existing = await db.enrollments.find_one(
        {"course_id": course_id, "user_id": user_id}
    )
    if existing:
        return False

    await db.enrollments.insert_one({
        "course_id": course_id,
        "user_id": user_id,
        "completed": False,
        "score": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    enrolled_user = await db.users.find_one({"_id": parse_object_id(user_id, "user")})
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    if enrolled_user and course:
        await send_enrollment_email(
            enrolled_user.get("email"),
            enrolled_user.get("name"),
            course.get("title"),
            course_id,
        )
    return True


async def mark_transaction_paid(session_id: str) -> dict | None:
    """Mark a payment transaction as paid. Returns the transaction doc or None."""
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        return None

    if transaction.get("payment_status") != "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "payment_status": "paid",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        transaction = {**transaction, "payment_status": "paid"}

    return transaction
