from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from certificate_id import (
    CERTIFICATE_SETTINGS_ID,
    DEFAULT_CERTIFICATE_ID_FORMAT,
    preview_certificate_id,
    validate_certificate_id_format,
)
from certificate_template import CERTIFICATE_BACKGROUNDS, DEFAULT_BACKGROUND, normalize_background
from database import db
from models import CertificateSettingsUpdate

router = APIRouter(tags=["certificate_settings"])

_DEFAULT_PRIMARY = "#002fa7"
_DEFAULT_SECONDARY = "#0a0b10"


def _serialize_settings(doc: dict | None) -> dict:
    doc = doc or {}
    id_format = doc.get("id_format") or DEFAULT_CERTIFICATE_ID_FORMAT
    next_sequence = (doc.get("sequence", 0) or 0) + 1
    return {
        "id_format": id_format,
        "default_background": normalize_background(doc.get("default_background")),
        "default_primary_color": doc.get("default_primary_color", _DEFAULT_PRIMARY),
        "default_secondary_color": doc.get("default_secondary_color", _DEFAULT_SECONDARY),
        "next_sequence": next_sequence,
        "sample_id": preview_certificate_id(id_format, sequence=next_sequence),
        "backgrounds": CERTIFICATE_BACKGROUNDS,
    }


@router.get("/certificate-settings")
async def get_certificate_settings(request: Request):
    await require_roles("admin")(request)
    doc = await db.platform_settings.find_one({"_id": CERTIFICATE_SETTINGS_ID})
    return _serialize_settings(doc)


@router.put("/certificate-settings")
async def update_certificate_settings(data: CertificateSettingsUpdate, request: Request):
    await require_roles("admin")(request)

    update_fields: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.id_format is not None:
        try:
            update_fields["id_format"] = validate_certificate_id_format(data.id_format)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    if data.default_background is not None:
        update_fields["default_background"] = normalize_background(data.default_background)
    if data.default_primary_color is not None:
        update_fields["default_primary_color"] = data.default_primary_color
    if data.default_secondary_color is not None:
        update_fields["default_secondary_color"] = data.default_secondary_color

    await db.platform_settings.update_one(
        {"_id": CERTIFICATE_SETTINGS_ID},
        {"$set": update_fields, "$setOnInsert": {"sequence": 0}},
        upsert=True,
    )
    doc = await db.platform_settings.find_one({"_id": CERTIFICATE_SETTINGS_ID})
    return _serialize_settings(doc)
