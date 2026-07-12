from fastapi import HTTPException

from certificate_template import (
    create_certification_template,
    create_certification_template_source,
    render_certification_template,
)
from db_utils import parse_object_id

DEFAULT_PRIMARY_COLOR = "#002FA7"
DEFAULT_SECONDARY_COLOR = "#0A0B10"


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
) -> dict:
    """Attach selected template metadata and rendered HTML to a certificate document."""
    if template:
        primary = template.get("primary_color") or fallback_primary_color
        secondary = template.get("secondary_color") or fallback_secondary_color
        cert_doc.update({
            "template": template.get("name") or fallback_template,
            "template_id": str(template["_id"]),
            "template_name": template.get("name"),
            "primary_color": primary,
            "secondary_color": secondary,
        })
        source_html = template.get("html") or create_certification_template_source(
            primary,
            secondary,
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
    })
    cert_doc["template_html"] = create_certification_template(cert_doc)
    return cert_doc
