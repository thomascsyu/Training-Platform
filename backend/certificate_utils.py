from fastapi import HTTPException

from certificate_i18n import normalize_certificate_language
from certificate_template import (
    DEFAULT_BACKGROUND,
    DEFAULT_ORIENTATION,
    compose_builder_certificate_html,
    compute_valid_until,
    create_certification_template,
    create_certification_template_source,
    normalize_background,
    normalize_orientation,
    render_certification_template,
)
from db_utils import parse_object_id

DEFAULT_PRIMARY_COLOR = "#002FA7"
DEFAULT_SECONDARY_COLOR = "#0A0B10"


async def resolve_certificate_template(
    database,
    template_id: str | None = None,
    course_id: str | None = None,
) -> dict | None:
    """Resolve template: explicit id → course-linked → global default."""
    if template_id:
        template = await database.certificate_templates.find_one(
            {"_id": parse_object_id(template_id, "certificate_template")}
        )
        if not template:
            raise HTTPException(status_code=404, detail="Certificate template not found")
        return template

    if course_id:
        course = await database.courses.find_one(
            {"_id": parse_object_id(course_id, "course")},
            {"certificate_template_id": 1},
        )
        linked_id = (course or {}).get("certificate_template_id")
        if linked_id:
            linked = await database.certificate_templates.find_one(
                {"_id": parse_object_id(str(linked_id), "certificate_template")}
            )
            if linked:
                return linked
        by_course = await database.certificate_templates.find_one({"course_id": str(course_id)})
        if by_course:
            return by_course

    return await database.certificate_templates.find_one({"is_default": True})


def apply_template_to_certificate(
    cert_doc: dict,
    template: dict | None,
    *,
    fallback_template: str = "default",
    fallback_primary_color: str = DEFAULT_PRIMARY_COLOR,
    fallback_secondary_color: str = DEFAULT_SECONDARY_COLOR,
    fallback_background: str = DEFAULT_BACKGROUND,
    fallback_orientation: str = DEFAULT_ORIENTATION,
    fallback_background_image_url: str | None = None,
    fallback_body_text: str | None = None,
    fallback_language: str | None = None,
) -> dict:
    """Attach selected template metadata and rendered HTML to a certificate document.

    The certificate is rendered in ``cert_doc["language"]`` when set, otherwise
    ``fallback_language`` (typically the issuing course's language), falling
    back to English when neither is a supported language.
    """
    cert_doc.setdefault("valid_until", compute_valid_until(cert_doc.get("issued_at")))
    cert_doc["language"] = normalize_certificate_language(
        cert_doc.get("language") or fallback_language
    )

    if template:
        primary = template.get("primary_color") or fallback_primary_color
        secondary = template.get("secondary_color") or fallback_secondary_color
        background = normalize_background(template.get("background") or fallback_background)
        orientation = normalize_orientation(
            template.get("orientation") or fallback_orientation
        )
        background_image_url = (
            template.get("background_image_url")
            if template.get("background_image_url") is not None
            else fallback_background_image_url
        )
        body_text = (
            template.get("body_text")
            if template.get("body_text") is not None
            else fallback_body_text
        )
        cert_doc.update({
            "template": template.get("name") or fallback_template,
            "template_id": str(template["_id"]),
            "template_name": template.get("name"),
            "primary_color": primary,
            "secondary_color": secondary,
            "background": background,
            "orientation": orientation,
            "background_image_url": background_image_url,
            "body_text": body_text,
        })
        if body_text:
            source_html = compose_builder_certificate_html(
                primary_color=primary,
                secondary_color=secondary,
                background=background,
                orientation=orientation,
                background_image_url=background_image_url,
                body_text=body_text,
                language=cert_doc["language"],
            )
        else:
            source_html = template.get("html") or create_certification_template_source(
                primary,
                secondary,
                background,
                cert_doc["language"],
                orientation,
                background_image_url,
            )
        cert_doc["template_html"] = render_certification_template(
            source_html,
            cert_doc,
        )
        return cert_doc

    primary = fallback_primary_color
    secondary = fallback_secondary_color
    background = normalize_background(fallback_background)
    orientation = normalize_orientation(fallback_orientation)
    background_image_url = fallback_background_image_url
    body_text = fallback_body_text
    cert_doc.update({
        "template": fallback_template,
        "template_id": None,
        "template_name": None,
        "primary_color": primary,
        "secondary_color": secondary,
        "background": background,
        "orientation": orientation,
        "background_image_url": background_image_url,
        "body_text": body_text,
    })
    if body_text:
        source_html = compose_builder_certificate_html(
            primary_color=primary,
            secondary_color=secondary,
            background=background,
            orientation=orientation,
            background_image_url=background_image_url,
            body_text=body_text,
            language=cert_doc["language"],
        )
        cert_doc["template_html"] = render_certification_template(source_html, cert_doc)
    else:
        cert_doc["template_html"] = create_certification_template(cert_doc)
    return cert_doc
