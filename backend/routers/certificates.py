import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import Response

from auth_utils import get_current_user, require_admin_or_manager, require_roles
from certificate_pdf import generate_certificate_pdf
from certificate_utils import apply_template_to_certificate, resolve_certificate_template
from database import db
from db_utils import parse_object_id
from email_service import send_certificate_email
from models import CertificateCreate, CertificateCustomize

router = APIRouter(tags=["certificates"])


def _serialize_certificate(cert: dict, fallback_course_title: str | None = None) -> dict:
    return {
        "id": str(cert["_id"]),
        "certificate_id": cert.get("certificate_id"),
        "course_id": cert["course_id"],
        "course_title": cert.get("course_title") or fallback_course_title,
        "user_name": cert.get("user_name"),
        "score": cert.get("score"),
        "template": cert.get("template"),
        "template_id": cert.get("template_id"),
        "template_name": cert.get("template_name"),
        "primary_color": cert.get("primary_color"),
        "secondary_color": cert.get("secondary_color"),
        "issued_at": cert.get("issued_at"),
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


@router.post("/certificates")
async def create_certificate(data: CertificateCreate, request: Request):
    actor = await require_admin_or_manager(request)

    course = await db.courses.find_one(
        {"_id": parse_object_id(data.course_id, "course")},
        {"_id": 1, "title": 1, "company_ids": 1},
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    target_user = await db.users.find_one(
        {"_id": parse_object_id(data.user_id, "user")},
        {"_id": 1, "name": 1, "email": 1, "role": 1, "company_id": 1},
    )
    if not target_user or target_user.get("role") != "student":
        raise HTTPException(status_code=404, detail="Student not found")

    if actor["role"] == "client_manager":
        company_id = actor["company_id"]
        if target_user.get("company_id") != company_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create certificates for this student",
            )
        course_company_ids = course.get("company_ids", [])
        if not course_company_ids or company_id not in course_company_ids:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create certificates for this course",
            )

    existing_cert = await db.certificates.find_one({
        "course_id": data.course_id,
        "user_id": data.user_id,
    })
    if existing_cert:
        raise HTTPException(
            status_code=409,
            detail="Certificate already exists for this student and course",
        )

    template = await resolve_certificate_template(db, data.template_id)

    cert_doc = {
        "certificate_id": str(uuid.uuid4())[:8].upper(),
        "course_id": data.course_id,
        "course_title": course.get("title") or "Course",
        "user_id": data.user_id,
        "user_name": target_user.get("name"),
        "score": data.score,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    apply_template_to_certificate(
        cert_doc,
        template,
        fallback_template=data.template,
        fallback_primary_color=data.primary_color,
        fallback_secondary_color=data.secondary_color,
    )
    result = await db.certificates.insert_one(cert_doc)
    cert_doc["_id"] = result.inserted_id

    await send_certificate_email(
        target_user["email"],
        target_user["name"],
        cert_doc["course_title"],
        cert_doc["certificate_id"],
        data.score,
    )
    return _serialize_certificate(cert_doc)


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

    update_fields = {
        "template": data.template,
        "primary_color": data.primary_color,
        "secondary_color": data.secondary_color,
    }
    if data.apply_to_course:
        result = await db.certificates.update_many(
            {"course_id": cert["course_id"]},
            {"$set": update_fields},
        )
    else:
        result = await db.certificates.update_one(
            {"_id": parse_object_id(certificate_id, "certificate")},
            {"$set": update_fields},
        )
    return {"message": f"Updated {result.modified_count} certificate(s)"}
