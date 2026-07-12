from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from certificate_template import create_certification_template_source
from database import db
from db_utils import parse_object_id
from models import CertificateTemplateCreate, CertificateTemplateRender, CertificateTemplateUpdate

router = APIRouter(tags=["certificate_templates"])

_PRIMARY_DEFAULT = "#002FA7"
_SECONDARY_DEFAULT = "#0A0B10"


def _serialize_template(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "html": doc["html"],
        "primary_color": doc.get("primary_color", _PRIMARY_DEFAULT),
        "secondary_color": doc.get("secondary_color", _SECONDARY_DEFAULT),
        "is_default": doc.get("is_default", False),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _default_html(primary: str, secondary: str) -> str:
    return create_certification_template_source(primary, secondary)


async def _ensure_single_default(exclude_id: str | None = None) -> None:
    """Unset is_default on all other templates when one is marked default."""
    query: dict = {"is_default": True}
    if exclude_id:
        query["_id"] = {"$ne": parse_object_id(exclude_id, "certificate_template")}
    await db.certificate_templates.update_many(query, {"$set": {"is_default": False}})


@router.get("/certificate-templates")
async def list_templates(request: Request):
    await require_roles("admin")(request)
    docs = await db.certificate_templates.find().sort("created_at", -1).to_list(100)
    return [_serialize_template(doc) for doc in docs]


@router.post("/certificate-templates/render-default")
async def render_default_template(data: CertificateTemplateRender, request: Request):
    await require_roles("admin")(request)
    return {
        "html": _default_html(data.primary_color, data.secondary_color),
    }


@router.post("/certificate-templates")
async def create_template(data: CertificateTemplateCreate, request: Request):
    await require_roles("admin")(request)

    existing = await db.certificate_templates.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=409, detail="A template with this name already exists")

    primary = data.primary_color
    secondary = data.secondary_color
    html = data.html if data.html is not None else _default_html(primary, secondary)

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "name": data.name,
        "html": html,
        "primary_color": primary,
        "secondary_color": secondary,
        "is_default": data.is_default,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.certificate_templates.insert_one(doc)
    doc["_id"] = result.inserted_id

    if data.is_default:
        await _ensure_single_default(str(result.inserted_id))
        doc["is_default"] = True

    return _serialize_template(doc)


@router.get("/certificate-templates/{template_id}")
async def get_template(template_id: str, request: Request):
    await require_roles("admin")(request)
    doc = await db.certificate_templates.find_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Certificate template not found")
    return _serialize_template(doc)


@router.put("/certificate-templates/{template_id}")
async def update_template(template_id: str, data: CertificateTemplateUpdate, request: Request):
    await require_roles("admin")(request)
    existing = await db.certificate_templates.find_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Certificate template not found")

    if data.name is not None and data.name != existing["name"]:
        name_taken = await db.certificate_templates.find_one({"name": data.name})
        if name_taken:
            raise HTTPException(status_code=409, detail="A template with this name already exists")

    update_fields: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if data.name is not None:
        update_fields["name"] = data.name
    if data.html is not None:
        update_fields["html"] = data.html
    if data.primary_color is not None:
        update_fields["primary_color"] = data.primary_color
    if data.secondary_color is not None:
        update_fields["secondary_color"] = data.secondary_color
    if data.is_default is not None:
        update_fields["is_default"] = data.is_default

    await db.certificate_templates.update_one(
        {"_id": parse_object_id(template_id, "certificate_template")},
        {"$set": update_fields},
    )

    if data.is_default:
        await _ensure_single_default(template_id)

    updated = await db.certificate_templates.find_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    return _serialize_template(updated)


@router.delete("/certificate-templates/{template_id}")
async def delete_template(template_id: str, request: Request):
    await require_roles("admin")(request)
    result = await db.certificate_templates.delete_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Certificate template not found")
    return {"message": "Certificate template deleted"}
