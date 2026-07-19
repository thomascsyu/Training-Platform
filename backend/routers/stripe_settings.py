from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from models import StripeSettingsUpdate, StripeTestConnectionRequest
from stripe_settings import (
    load_stripe_settings_masked,
    save_stripe_settings,
    test_stripe_connection,
)

router = APIRouter(tags=["stripe-settings"])


@router.get("/admin/stripe-settings")
async def get_stripe_settings(request: Request):
    await require_roles("admin")(request)
    return await load_stripe_settings_masked()


@router.put("/admin/stripe-settings")
async def update_stripe_settings(data: StripeSettingsUpdate, request: Request):
    user = await require_roles("admin")(request)

    try:
        await save_stripe_settings(
            data.model_dump(exclude_unset=True),
            user.get("id", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save Stripe settings") from exc

    return await load_stripe_settings_masked()


@router.post("/admin/stripe-settings/test")
async def test_stripe_settings(data: StripeTestConnectionRequest, request: Request):
    await require_roles("admin")(request)
    return await test_stripe_connection(data.api_key)
