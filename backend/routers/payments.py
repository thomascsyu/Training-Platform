import json
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user, require_roles
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
        raise HTTPException(status_code=500, detail="Webhook processing failed") from e


@router.get("/payments/transactions")
async def list_transactions(
    request: Request,
    status: Optional[str] = None,
    course_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
):
    await require_roles("admin")(request)

    query: dict = {}
    if status:
        query["payment_status"] = status
    if course_id:
        query["course_id"] = course_id
    if user_id:
        query["user_id"] = user_id

    transactions = await db.payment_transactions.find(query).sort(
        "created_at", -1
    ).skip(skip).limit(limit).to_list(limit)

    user_ids = list({t.get("user_id") for t in transactions if t.get("user_id")})
    course_ids = list({t.get("course_id") for t in transactions if t.get("course_id")})

    user_map = {}
    if user_ids:
        users = await db.users.find(
            {"_id": {"$in": [parse_object_id(uid, "user") for uid in user_ids]}},
            {"_id": 1, "name": 1},
        ).to_list(len(user_ids))
        user_map = {str(u["_id"]): u for u in users}

    course_map = {}
    if course_ids:
        courses = await db.courses.find(
            {"_id": {"$in": [parse_object_id(cid, "course") for cid in course_ids]}},
            {"_id": 1, "title": 1},
        ).to_list(len(course_ids))
        course_map = {str(c["_id"]): c for c in courses}

    results = []
    for t in transactions:
        user = user_map.get(t.get("user_id", ""))
        course = course_map.get(t.get("course_id", ""))
        results.append({
            "id": str(t["_id"]),
            "session_id": t.get("session_id"),
            "course_id": t.get("course_id"),
            "course_title": course.get("title") if course else "Unknown",
            "user_id": t.get("user_id"),
            "user_name": user.get("name") if user else "Unknown",
            "amount": float(t.get("amount", 0)),
            "currency": t.get("currency", "usd"),
            "payment_status": t.get("payment_status"),
            "created_at": t.get("created_at"),
            "updated_at": t.get("updated_at"),
        })
    return results


@router.get("/payments/transactions/{session_id}")
async def get_transaction_detail(session_id: str, request: Request):
    await require_roles("admin")(request)

    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    user = None
    if transaction.get("user_id"):
        user = await db.users.find_one(
            {"_id": parse_object_id(transaction["user_id"], "user")},
            {"_id": 1, "name": 1},
        )
    course = None
    if transaction.get("course_id"):
        course = await db.courses.find_one(
            {"_id": parse_object_id(transaction["course_id"], "course")},
            {"_id": 1, "title": 1},
        )

    return {
        "id": str(transaction["_id"]),
        "session_id": transaction.get("session_id"),
        "course_id": transaction.get("course_id"),
        "course_title": course.get("title") if course else "Unknown",
        "user_id": transaction.get("user_id"),
        "user_name": user.get("name") if user else "Unknown",
        "amount": float(transaction.get("amount", 0)),
        "currency": transaction.get("currency", "usd"),
        "payment_status": transaction.get("payment_status"),
        "created_at": transaction.get("created_at"),
        "updated_at": transaction.get("updated_at"),
    }


@router.get("/payments/summary")
async def payments_summary(request: Request):
    await require_roles("admin")(request)

    total = await db.payment_transactions.count_documents({})
    paid = await db.payment_transactions.count_documents({"payment_status": "paid"})
    pending = await db.payment_transactions.count_documents({"payment_status": "pending"})

    paid_transactions = await db.payment_transactions.find(
        {"payment_status": "paid"}
    ).to_list(10000)
    revenue = sum(float(t.get("amount", 0)) for t in paid_transactions)

    return {
        "total_transactions": total,
        "paid_count": paid,
        "pending_count": pending,
        "total_revenue": round(revenue, 2),
    }
