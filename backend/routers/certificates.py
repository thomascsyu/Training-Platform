from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import Response

from auth_utils import get_current_user, require_admin_or_manager, require_roles
from certificate_i18n import normalize_certificate_language
from certificate_id import (
    course_code_from,
    get_certificate_id_format,
    preview_certificate_id,
)
from certificate_pdf import generate_certificate_pdf
from certificate_template import (
    compute_valid_until,
    create_certification_template,
    is_certificate_expired,
)
from certificate_utils import apply_template_to_certificate, resolve_certificate_template
from database import db
from db_utils import parse_object_id
from models import CertificateCustomize, CertificatePreview

router = APIRouter(tags=["certificates"])


def _serialize_certificate(cert: dict, fallback_course_title: str | None = None) -> dict:
    valid_until = cert.get("valid_until") or compute_valid_until(cert.get("issued_at"))
    return {
        "id": str(cert["_id"]),
        "certificate_id": cert.get("certificate_id"),
        "course_id": cert["course_id"],
        "course_title": cert.get("course_title") or fallback_course_title,
        "user_name": cert.get("user_name"),
        "score": cert.get("score"),
        "language": cert.get("language", "en"),
        "template": cert.get("template"),
        "template_id": cert.get("template_id"),
        "template_name": cert.get("template_name"),
        "primary_color": cert.get("primary_color"),
        "secondary_color": cert.get("secondary_color"),
        "background": cert.get("background"),
        "issued_at": cert.get("issued_at"),
        "valid_until": valid_until,
        "is_expired": is_certificate_expired(valid_until),
    }


@router.get("/certificates/my")
async def get_my_certificates(request: Request):
    user = await get_current_user(request)
    certs = await db.certificates.find({"user_id": user["id"]}).sort(
        "issued_at", -1
    ).to_list(100)

    course_ids = list({c["course_id"] for c in certs if c.get("course_id")})
    course_map = {}
    if course_ids:
        courses = await db.courses.find(
            {"_id": {"$in": [parse_object_id(cid, "course") for cid in course_ids]}},
            {"_id": 1, "title": 1},
        ).to_list(100)
        course_map = {str(c["_id"]): c for c in courses}

    certificates = []
    for cert in certs:
        course = course_map.get(cert.get("course_id", ""))
        certificates.append(
            _serialize_certificate(
                cert,
                fallback_course_title=course.get("title") if course else None,
            )
        )
    return certificates


@router.get("/certificates")
async def list_certificates(
    request: Request,
    course_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
):
    user = await require_admin_or_manager(request)
    query: dict = {}

    if user["role"] == "client_manager":
        company_users = await db.users.find(
            {"company_id": user["company_id"]}, {"_id": 1}
        ).to_list(1000)
        allowed_user_ids = {str(u["_id"]) for u in company_users}
        if user_id and user_id not in allowed_user_ids:
            return []
        query["user_id"] = {"$in": [user_id] if user_id else list(allowed_user_ids)}
    elif user_id:
        query["user_id"] = user_id

    if course_id:
        query["course_id"] = course_id

    certs = await db.certificates.find(query).sort(
        "issued_at", -1
    ).skip(skip).limit(limit).to_list(limit)

    course_ids = list({c["course_id"] for c in certs if c.get("course_id")})
    course_map = {}
    if course_ids:
        courses = await db.courses.find(
            {"_id": {"$in": [parse_object_id(cid, "course") for cid in course_ids]}},
            {"_id": 1, "title": 1},
        ).to_list(len(course_ids))
        course_map = {str(c["_id"]): c for c in courses}

    return [
        _serialize_certificate(
            cert,
            fallback_course_title=course_map.get(cert.get("course_id", ""), {}).get("title"),
        )
        for cert in certs
    ]


@router.post("/certificates/preview")
async def preview_certificate(data: CertificatePreview, request: Request):
    """Render a fully filled certificate without issuing or persisting it.

    Accepts a real course/student (by id) or free-form sample title/name. The
    certificate ID shown in the preview is a non-consuming sample derived from
    the configured ID format — the sequence counter is not incremented.
    """
    actor = await require_admin_or_manager(request)

    course = None
    course_title = (data.course_title or "").strip() or "Course"
    course_language = None
    if data.course_id:
        course = await db.courses.find_one(
            {"_id": parse_object_id(data.course_id, "course")},
            {"_id": 1, "title": 1, "company_ids": 1, "language": 1},
        )
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        course_title = course.get("title") or course_title
        course_language = course.get("language")

    target_user = None
    user_name = (data.user_name or "").strip() or "Student"
    if data.user_id:
        target_user = await db.users.find_one(
            {"_id": parse_object_id(data.user_id, "user")},
            {"_id": 1, "name": 1, "role": 1, "company_id": 1},
        )
        if not target_user or target_user.get("role") != "student":
            raise HTTPException(status_code=404, detail="Student not found")
        user_name = target_user.get("name") or user_name

    if actor["role"] == "client_manager":
        company_id = actor["company_id"]
        if target_user and target_user.get("company_id") != company_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to preview certificates for this student",
            )
        if course is not None:
            course_company_ids = course.get("company_ids", [])
            if not course_company_ids or company_id not in course_company_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Not authorized to preview certificates for this course",
                )

    template = await resolve_certificate_template(db, data.template_id, course_id=data.course_id)

    issued_at = datetime.now(timezone.utc).isoformat()
    if data.certificate_id:
        sample_id = data.certificate_id
    else:
        settings = await db.platform_settings.find_one({"_id": "certificate"})
        id_format = await get_certificate_id_format(db)
        next_sequence = ((settings or {}).get("sequence", 0) or 0) + 1
        sample_id = preview_certificate_id(
            id_format,
            sequence=next_sequence,
            course_code=course_code_from(course_title) or "COURSE",
        )

    cert_doc = {
        "certificate_id": sample_id,
        "course_id": data.course_id,
        "course_title": course_title,
        "user_id": data.user_id,
        "user_name": user_name,
        "score": data.score,
        "issued_at": issued_at,
    }
    if data.language:
        cert_doc["language"] = data.language

    # Builder fields on the preview request override / compose without a saved template.
    use_builder_fields = (
        data.body_text is not None
        or data.background_image_url is not None
        or (data.orientation and data.orientation != "landscape")
    )
    if use_builder_fields and not data.template_id:
        apply_template_to_certificate(
            cert_doc,
            None,
            fallback_template=data.template,
            fallback_primary_color=data.primary_color,
            fallback_secondary_color=data.secondary_color,
            fallback_background=data.background,
            fallback_orientation=data.orientation,
            fallback_background_image_url=data.background_image_url,
            fallback_body_text=data.body_text,
            fallback_language=course_language or data.language,
        )
    else:
        apply_template_to_certificate(
            cert_doc,
            template,
            fallback_template=data.template,
            fallback_primary_color=data.primary_color,
            fallback_secondary_color=data.secondary_color,
            fallback_background=data.background,
            fallback_orientation=data.orientation,
            fallback_background_image_url=data.background_image_url,
            fallback_body_text=data.body_text,
            fallback_language=course_language or data.language,
        )

    if data.format == "pdf":
        pdf_bytes = generate_certificate_pdf(cert_doc)
        filename = f"certificate-preview-{sample_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )

    return Response(content=cert_doc["template_html"], media_type="text/html")


async def _get_authorized_certificate(certificate_id: str, request: Request) -> dict:
    user = await get_current_user(request)
    cert = await db.certificates.find_one(
        {"_id": parse_object_id(certificate_id, "certificate")}
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if user["role"] == "client_manager":
        cert_user = await db.users.find_one(
            {"_id": parse_object_id(cert.get("user_id", ""), "user")},
            {"_id": 1, "company_id": 1},
        )
        if not cert_user or cert_user.get("company_id") != user.get("company_id"):
            raise HTTPException(
                status_code=403, detail="Not authorized to view this certificate"
            )
    elif user["role"] != "admin" and cert.get("user_id") != user["id"]:
        raise HTTPException(
            status_code=403, detail="Not authorized to view this certificate"
        )
    return cert


@router.get("/certificates/{certificate_id}/pdf")
async def download_certificate_pdf(certificate_id: str, request: Request):
    cert = await _get_authorized_certificate(certificate_id, request)

    pdf_bytes = generate_certificate_pdf(cert)
    filename = f"certificate-{cert.get('certificate_id', certificate_id)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/certificates/{certificate_id}/html")
async def view_certificate_html(certificate_id: str, request: Request):
    cert = await _get_authorized_certificate(certificate_id, request)
    html = cert.get("template_html")
    if not html:
        apply_template_to_certificate(
            cert,
            None,
            fallback_template=cert.get("template", "default"),
            fallback_primary_color=cert.get("primary_color", "#002FA7"),
            fallback_secondary_color=cert.get("secondary_color", "#0A0B10"),
        )
        html = cert["template_html"]
    return Response(content=html, media_type="text/html")


@router.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str, request: Request):
    cert = await _get_authorized_certificate(certificate_id, request)
    return _serialize_certificate(cert)


@router.put("/certificates/{certificate_id}/customize")
async def customize_certificate(
    certificate_id: str, data: CertificateCustomize, request: Request
):
    await require_roles("admin")(request)
    cert = await db.certificates.find_one(
        {"_id": parse_object_id(certificate_id, "certificate")}
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if data.apply_to_course:
        targets = await db.certificates.find({"course_id": cert["course_id"]}).to_list(1000)
    else:
        targets = [cert]

    modified = 0
    for target in targets:
        target["template"] = data.template
        target["primary_color"] = data.primary_color
        target["secondary_color"] = data.secondary_color
        target["background"] = data.background or target.get("background") or "plain"
        target["language"] = normalize_certificate_language(
            data.language or target.get("language")
        )
        # Re-render the stored HTML so downloads/previews reflect the new style.
        rendered = create_certification_template(target)
        await db.certificates.update_one(
            {"_id": target["_id"]},
            {
                "$set": {
                    "template": target["template"],
                    "primary_color": target["primary_color"],
                    "secondary_color": target["secondary_color"],
                    "background": target["background"],
                    "language": target["language"],
                    "template_html": rendered,
                }
            },
        )
        modified += 1
    return {"message": f"Updated {modified} certificate(s)"}
