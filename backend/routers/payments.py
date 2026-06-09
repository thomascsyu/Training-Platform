import json
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user
from config import (
    REQUIRE_STRIPE_WEBHOOK_SECRET,
    STRIPE_API_KEY,
    STRIPE_WEBHOOK_SECRET,
    logger,
)
from database import db
from db_utils import parse_object_id
from models import PaymentCreate
from payment_utils import enroll_user_after_payment, mark_transaction_paid

router = APIRouter(tags=["payments"])


@router.post("/payments/checkout")
async def create_checkout(data: PaymentCreate, request: Request):
    user = await get_current_user(request)

    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    course = await db.courses.find_one({"_id": parse_object_id(data.course_id, "course")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.get("is_free"):
        raise HTTPException(status_code=400, detail="This is a free course")

    price = float(course.get("price", 0))
    if price <= 0:
        raise HTTPException(status_code=400, detail="Invalid course price")

    success_url = f"{data.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/courses/{data.course_id}"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": course.get("title", "Course"),
                        "description": (
                            course.get("description", "")[:500]
                            if course.get("description")
                            else None
                        ),
                    },
                    "unit_amount": int(price * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "course_id": data.course_id,
                "user_id": user["id"],
                "course_title": course.get("title", ""),
            },
        )

        await db.payment_transactions.insert_one({
            "session_id": session.id,
            "course_id": data.course_id,
            "user_id": user["id"],
            "amount": price,
            "currency": "usd",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error("Stripe error: %s", e)
        raise HTTPException(status_code=500, detail="Payment service error") from e


@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    user = await get_current_user(request)

    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if (
        transaction["user_id"] != user["id"]
        and user["role"] != "admin"
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this payment")

    if transaction.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid"}

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status

        if payment_status == "paid":
            await mark_transaction_paid(session_id)
            await enroll_user_after_payment(transaction)

        return {"status": session.status, "payment_status": payment_status}
    except stripe.error.StripeError as e:
        logger.error("Stripe error: %s", e)
        raise HTTPException(status_code=500, detail="Payment service error") from e


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")

    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    if REQUIRE_STRIPE_WEBHOOK_SECRET and not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhook secret is required")

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(body, signature, STRIPE_WEBHOOK_SECRET)
        else:
            event = stripe.Event.construct_from(json.loads(body), stripe.api_key)

        if event.type == "checkout.session.completed":
            session = event.data.object
            if session.payment_status == "paid":
                transaction = await mark_transaction_paid(session.id)
                if transaction:
                    await enroll_user_after_payment(transaction)

        return {"status": "ok"}
    except stripe.error.SignatureVerificationError as e:
        logger.error("Webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature") from e
    except Exception as e:
        logger.error("Webhook error: %s", e)
        return {"status": "error"}
