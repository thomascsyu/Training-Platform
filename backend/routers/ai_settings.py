from fastapi import APIRouter, HTTPException, Request

from ai_settings import (
    load_ai_settings_masked,
    save_ai_settings,
    test_provider_connection,
)
from auth_utils import require_roles
from models import AISettingsUpdate, AITestConnectionRequest

router = APIRouter(tags=["ai-settings"])


def _admin_user_id(request: Request) -> str:
    user = request.state.user
    return user.get("id") or user.get("_id") or str(user.get("email"))


@router.get("/admin/ai-settings")
async def get_ai_settings(request: Request):
    await require_roles("admin")(request)
    return await load_ai_settings_masked()


@router.put("/admin/ai-settings")
async def update_ai_settings(data: AISettingsUpdate, request: Request):
    user = await require_roles("admin")(request)

    if data.default_provider and data.default_provider not in ("deepseek", "xai"):
        raise HTTPException(status_code=400, detail="Invalid default_provider")

    try:
        await save_ai_settings(data.model_dump(exclude_unset=True), user.get("id", ""))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save AI settings") from exc

    return await load_ai_settings_masked()


@router.post("/admin/ai-settings/test")
async def test_ai_connection(data: AITestConnectionRequest, request: Request):
    await require_roles("admin")(request)

    if data.provider not in ("deepseek", "xai"):
        raise HTTPException(status_code=400, detail="Invalid provider")

    return await test_provider_connection(data.provider, data.api_key)
