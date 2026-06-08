import uuid
from datetime import datetime, timezone
from typing import Optional

import stripe
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from openai import OpenAI

import jwt
from config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    DEEPSEEK_API_KEY,
    JWT_ALGORITHM,
    JWT_SECRET,
    LANGUAGE_NAMES,
    REQUIRE_STRIPE_WEBHOOK_SECRET,
    STRIPE_API_KEY,
    STRIPE_WEBHOOK_SECRET,
    SUPPORTED_LANGUAGES,
    logger,
)
from database import db
from models import (
    CertificateCustomize,
    ChatMessageCreate,
    CourseCreate,
    CourseUpdate,
    EnrollmentCreate,
    ForumPostCreate,
    LessonCreate,
    LessonUpdate,
    PaymentCreate,
    QuizAttemptCreate,
    QuizCreate,
    TranslateCourseRequest,
    TranslateQuizRequest,
    TranslateRequest,
    UserCreate,
    UserLogin,
)
from auth_utils import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_optional_user,
    hash_password,
    require_roles,
    set_auth_cookies,
    verify_password,
)
from course_utils import delete_course_related_data
from email_service import (
    send_certificate_email,
    send_enrollment_email,
    send_progress_email,
)

deepseek_client = None


router = APIRouter(tags=["payments"])

@router.post("/payments/checkout")
async def create_checkout(data: PaymentCreate, request: Request):
    user = await get_current_user(request)
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    course = await db.courses.find_one({"_id": ObjectId(data.course_id)})
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
        # Create Stripe Checkout Session using standard SDK
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.get("title", "Course"),
                        'description': course.get("description", "")[:500] if course.get("description") else None,
                    },
                    'unit_amount': int(price * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "course_id": data.course_id,
                "user_id": user["id"],
                "course_title": course.get("title", "")
            }
        )
        
        # Create payment transaction record
        await db.payment_transactions.insert_one({
            "session_id": session.id,
            "course_id": data.course_id,
            "user_id": user["id"],
            "amount": price,
            "currency": "usd",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment service error")

@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    user = await get_current_user(request)
    
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Payment service not configured")
    
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return cached status
    if transaction.get("payment_status") == "paid":
        return {"status": "complete", "payment_status": "paid"}
    
    try:
        # Get session status from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status  # 'paid', 'unpaid', 'no_payment_required'
        
        # Update transaction status
        if payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            # Auto-enroll user
            existing = await db.enrollments.find_one({"course_id": transaction["course_id"], "user_id": transaction["user_id"]})
            if not existing:
                await db.enrollments.insert_one({
                    "course_id": transaction["course_id"],
                    "user_id": transaction["user_id"],
                    "completed": False,
                    "score": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Send enrollment email
                enrolled_user = await db.users.find_one({"_id": ObjectId(transaction["user_id"])})
                course = await db.courses.find_one({"_id": ObjectId(transaction["course_id"])})
                if enrolled_user and course:
                    await send_enrollment_email(
                        enrolled_user.get("email"),
                        enrolled_user.get("name"),
                        course.get("title"),
                        transaction["course_id"]
                    )
        
        return {"status": session.status, "payment_status": payment_status}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail="Payment service error")

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    import json

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
        
        # Handle checkout.session.completed event
        if event.type == "checkout.session.completed":
            session = event.data.object
            session_id = session.id
            payment_status = session.payment_status
            
            if payment_status == "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "paid", "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Auto-enroll user
                transaction = await db.payment_transactions.find_one({"session_id": session_id})
                if transaction:
                    existing = await db.enrollments.find_one({
                        "course_id": transaction["course_id"],
                        "user_id": transaction["user_id"]
                    })
                    if not existing:
                        await db.enrollments.insert_one({
                            "course_id": transaction["course_id"],
                            "user_id": transaction["user_id"],
                            "completed": False,
                            "score": 0,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        # Send enrollment email
                        enrolled_user = await db.users.find_one({"_id": ObjectId(transaction["user_id"])})
                        course = await db.courses.find_one({"_id": ObjectId(transaction["course_id"])})
                        if enrolled_user and course:
                            await send_enrollment_email(
                                enrolled_user.get("email"),
                                enrolled_user.get("name"),
                                course.get("title"),
                                transaction["course_id"]
                            )
        
        return {"status": "ok"}
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}
