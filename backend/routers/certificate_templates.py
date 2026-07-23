from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from certificate_template import (
    MAX_CERTIFICATE_TEMPLATES,
    compose_builder_certificate_html,
    create_certification_template_source,
    normalize_background,
    normalize_orientation,
)
from database import db
from db_utils import parse_object_id
from models import CertificateTemplateCreate, CertificateTemplateRender, CertificateTemplateUpdate

router = APIRouter(tags=["certificate_templates"])

_PRIMARY_DEFAULT = "#002FA7"
_SECONDARY_DEFAULT = "#0A0B10"
_BACKGROUND_DEFAULT = "plain"


def _serialize_template(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "html": doc["html"],
        "primary_color": doc.get("primary_color", _PRIMARY_DEFAULT),
        "secondary_color": doc.get("secondary_color", _SECONDARY_DEFAULT),
        "background": doc.get("background", _BACKGROUND_DEFAULT),
        "background_image_url": doc.get("background_image_url"),
        "orientation": normalize_orientation(doc.get("orientation")),
        "body_text": doc.get("body_text"),
        "course_id": doc.get("course_id"),
        "is_default": doc.get("is_default", False),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


def _compose_html(
    *,
    primary: str,
    secondary: str,
    background: str,
    orientation: str,
    background_image_url: str | None,
    body_text: str | None,
    html: str | None = None,
) -> str:
    if body_text is not None:
        return compose_builder_certificate_html(
            primary_color=primary,
            secondary_color=secondary,
            background=background,
            orientation=orientation,
            background_image_url=background_image_url,
            body_text=body_text,
        )
    if html is not None:
        return html
    return create_certification_template_source(
        primary,
        secondary,
        background,
        orientation=orientation,
        background_image_url=background_image_url,
    )


async def _ensure_single_default(exclude_id: str | None = None) -> None:
    """Unset is_default on all other templates when one is marked default."""
    query: dict = {"is_default": True}
    if exclude_id:
        query["_id"] = {"$ne": parse_object_id(exclude_id, "certificate_template")}
    await db.certificate_templates.update_many(query, {"$set": {"is_default": False}})


async def _validate_course_id(course_id: str | None) -> str | None:
    if not course_id:
        return None
    course = await db.courses.find_one(
        {"_id": parse_object_id(course_id, "course")},
        {"_id": 1},
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return str(course["_id"])


async def _sync_course_template_link(
    *,
    template_id: str,
    course_id: str | None,
    previous_course_id: str | None = None,
) -> None:
    """Keep courses.certificate_template_id in sync with template.course_id."""
    if previous_course_id and previous_course_id != course_id:
        await db.courses.update_one(
            {
                "_id": parse_object_id(previous_course_id, "course"),
                "certificate_template_id": template_id,
            },
            {"$unset": {"certificate_template_id": ""}},
        )

    if course_id:
        # One active builder config per course: clear other templates' course_id.
        await db.certificate_templates.update_many(
            {
                "course_id": course_id,
                "_id": {"$ne": parse_object_id(template_id, "certificate_template")},
            },
            {"$unset": {"course_id": ""}},
        )
        await db.courses.update_one(
            {"_id": parse_object_id(course_id, "course")},
            {"$set": {"certificate_template_id": template_id}},
        )


@router.get("/certificate-templates")
async def list_templates(request: Request, course_id: str | None = None):
    await require_roles("admin")(request)
    query: dict = {}
    if course_id:
        query["course_id"] = course_id
    docs = await db.certificate_templates.find(query).sort("created_at", -1).to_list(100)
    return [_serialize_template(doc) for doc in docs]


@router.post("/certificate-templates/render-default")
async def render_default_template(data: CertificateTemplateRender, request: Request):
    await require_roles("admin")(request)
    orientation = normalize_orientation(data.orientation)
    background = normalize_background(data.background)
    html = _compose_html(
        primary=data.primary_color,
        secondary=data.secondary_color,
        background=background,
        orientation=orientation,
        background_image_url=data.background_image_url,
        body_text=data.body_text,
    )
    return {"html": html}


@router.post("/certificate-templates")
async def create_template(data: CertificateTemplateCreate, request: Request):
    await require_roles("admin")(request)

    template_count = await db.certificate_templates.count_documents({})
    if template_count >= MAX_CERTIFICATE_TEMPLATES:
        raise HTTPException(
            status_code=409,
            detail=f"At most {MAX_CERTIFICATE_TEMPLATES} certificate templates are allowed",
        )

    existing = await db.certificate_templates.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=409, detail="A template with this name already exists")

    course_id = await _validate_course_id(data.course_id)
    primary = data.primary_color
    secondary = data.secondary_color
    background = normalize_background(data.background)
    orientation = normalize_orientation(data.orientation)
    background_image_url = data.background_image_url
    body_text = data.body_text
    # Course-linked builder configs should not be the global default.
    is_default = False if course_id else data.is_default
    if data.is_default and not course_id:
        is_default = True

    html = _compose_html(
        primary=primary,
        secondary=secondary,
        background=background,
        orientation=orientation,
        background_image_url=background_image_url,
        body_text=body_text,
        html=data.html,
    )

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "name": data.name,
        "html": html,
        "primary_color": primary,
        "secondary_color": secondary,
        "background": background,
        "background_image_url": background_image_url,
        "orientation": orientation,
        "body_text": body_text,
        "course_id": course_id,
        "is_default": is_default,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.certificate_templates.insert_one(doc)
    doc["_id"] = result.inserted_id
    template_id = str(result.inserted_id)

    if is_default:
        await _ensure_single_default(template_id)
        doc["is_default"] = True

    await _sync_course_template_link(template_id=template_id, course_id=course_id)

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

    previous_course_id = existing.get("course_id")
    update_fields: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    fields_set = data.__pydantic_fields_set__
    if data.name is not None:
        update_fields["name"] = data.name
    if data.primary_color is not None:
        update_fields["primary_color"] = data.primary_color
    if data.secondary_color is not None:
        update_fields["secondary_color"] = data.secondary_color
    if data.background is not None:
        update_fields["background"] = normalize_background(data.background)
    if "background_image_url" in fields_set:
        update_fields["background_image_url"] = data.background_image_url
    if data.orientation is not None:
        update_fields["orientation"] = normalize_orientation(data.orientation)
    if "body_text" in fields_set:
        update_fields["body_text"] = data.body_text
    if "course_id" in fields_set:
        update_fields["course_id"] = await _validate_course_id(data.course_id)
    if data.is_default is not None:
        # Course-scoped templates cannot be global default.
        course_for_default = update_fields.get("course_id", previous_course_id)
        update_fields["is_default"] = bool(data.is_default) and not course_for_default

    # Regenerate HTML when builder fields or explicit html change.
    rebuild = any(
        key in update_fields
        for key in (
            "primary_color",
            "secondary_color",
            "background",
            "background_image_url",
            "orientation",
            "body_text",
        )
    ) or data.html is not None

    if rebuild:
        primary = update_fields.get("primary_color", existing.get("primary_color", _PRIMARY_DEFAULT))
        secondary = update_fields.get(
            "secondary_color", existing.get("secondary_color", _SECONDARY_DEFAULT)
        )
        background = update_fields.get(
            "background", existing.get("background", _BACKGROUND_DEFAULT)
        )
        orientation = update_fields.get(
            "orientation", normalize_orientation(existing.get("orientation"))
        )
        if "background_image_url" in update_fields:
            background_image_url = update_fields["background_image_url"]
        else:
            background_image_url = existing.get("background_image_url")
        if "body_text" in update_fields:
            body_text = update_fields["body_text"]
        else:
            body_text = existing.get("body_text")
        update_fields["html"] = _compose_html(
            primary=primary,
            secondary=secondary,
            background=background,
            orientation=orientation,
            background_image_url=background_image_url,
            body_text=body_text,
            html=data.html if data.html is not None else None,
        )
    elif data.html is not None:
        update_fields["html"] = data.html

    await db.certificate_templates.update_one(
        {"_id": parse_object_id(template_id, "certificate_template")},
        {"$set": update_fields},
    )

    if update_fields.get("is_default"):
        await _ensure_single_default(template_id)

    if "course_id" in fields_set or previous_course_id:
        await _sync_course_template_link(
            template_id=template_id,
            course_id=update_fields.get("course_id", previous_course_id)
            if "course_id" in fields_set
            else previous_course_id,
            previous_course_id=previous_course_id,
        )

    updated = await db.certificate_templates.find_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    return _serialize_template(updated)


@router.delete("/certificate-templates/{template_id}")
async def delete_template(template_id: str, request: Request):
    await require_roles("admin")(request)
    existing = await db.certificate_templates.find_one(
        {"_id": parse_object_id(template_id, "certificate_template")},
        {"course_id": 1},
    )
    result = await db.certificate_templates.delete_one(
        {"_id": parse_object_id(template_id, "certificate_template")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Certificate template not found")
    if existing and existing.get("course_id"):
        await db.courses.update_one(
            {
                "_id": parse_object_id(existing["course_id"], "course"),
                "certificate_template_id": template_id,
            },
            {"$unset": {"certificate_template_id": ""}},
        )
    return {"message": "Certificate template deleted"}
