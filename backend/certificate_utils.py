from fastapi import HTTPException

from certificate_i18n import normalize_certificate_language
from certificate_template import (
    DEFAULT_BACKGROUND,
    compute_valid_until,
    create_certification_template,
    create_certification_template_source,
    render_certification_template,
)
from db_utils import parse_object_id

DEFAULT_PRIMARY_COLOR = "#002FA7"
DEFAULT_SECONDARY_COLOR = "#0A0B10"
DEFAULT_BACKGROUND = "plain"


async def resolve_certificate_template(database, template_id: str | None = None) -> dict | None:
    """Resolve an explicit certificate template, or the default template if available."""
    if template_id:
        template = await database.certificate_templates.find_one(
            {"_id": parse_object_id(template_id, "certificate_template")}
        )
        if not template:
            raise HTTPException(status_code=404, detail="Certificate template not found")
        return template
    return await database.certificate_templates.find_one({"is_default": True})


def apply_template_to_certificate(
    cert_doc: dict,
    template: dict | None,
    *,
    fallback_template: str = "default",
    fallback_primary_color: str = DEFAULT_PRIMARY_COLOR,
    fallback_secondary_color: str = DEFAULT_SECONDARY_COLOR,
    fallback_background: str = DEFAULT_BACKGROUND,
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
        background = template.get("background") or fallback_background
        cert_doc.update({
            "template": template.get("name") or fallback_template,
            "template_id": str(template["_id"]),
            "template_name": template.get("name"),
            "primary_color": primary,
            "secondary_color": secondary,
            "background": background,
        })
        source_html = template.get("html") or create_certification_template_source(
            primary,
            secondary,
            background,
        )
        cert_doc["template_html"] = render_certification_template(
            source_html,
            cert_doc,
        )
        return cert_doc

    cert_doc.update({
        "template": fallback_template,
        "template_id": None,
        "template_name": None,
        "primary_color": fallback_primary_color,
        "secondary_color": fallback_secondary_color,
        "background": fallback_background,
    })
    cert_doc["template_html"] = create_certification_template(cert_doc)
    return cert_doc
