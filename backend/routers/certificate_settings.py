import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from auth_utils import require_roles
from certificate_id import (
    CERTIFICATE_SETTINGS_ID,
    DEFAULT_CERTIFICATE_ID_FORMAT,
    preview_certificate_id,
    validate_certificate_id_format,
)
from certificate_template import CERTIFICATE_BACKGROUNDS, normalize_background
from database import db

try:
    from models import CertificateSettingsUpdate
except ImportError:
    # Older images may ship this router before models.py exports the class.
    # Keep a local definition so the API still binds :8080 (login works).
    _BACKGROUND_KEYS = {"plain", "geometric", "waves", "guilloche", "corners"}

    class CertificateSettingsUpdate(BaseModel):
        id_format: Optional[str] = Field(default=None, min_length=1, max_length=120)
        default_background: Optional[str] = None
        default_primary_color: Optional[str] = None
        default_secondary_color: Optional[str] = None

        @field_validator("default_primary_color", "default_secondary_color")
        @classmethod
        def _validate_hex(cls, value: Optional[str]) -> Optional[str]:
            if value is None:
                return value
            if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
                raise ValueError("Color must be a valid 6-digit hex code")
            return value.lower()

        @field_validator("default_background")
        @classmethod
        def _check_background(cls, value: Optional[str]) -> Optional[str]:
            if value is None:
                return value
            key = str(value).strip()
            if key not in _BACKGROUND_KEYS:
                allowed = ", ".join(sorted(_BACKGROUND_KEYS))
                raise ValueError(f"Background must be one of: {allowed}")
            return key

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
