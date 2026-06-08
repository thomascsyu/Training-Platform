import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import Response

from auth_utils import get_current_user, require_roles
from certificate_pdf import generate_certificate_pdf
from database import db
from models import CertificateCustomize

router = APIRouter(tags=["certificates"])


@router.get("/certificates/my")
async def get_my_certificates(request: Request):
    user = await get_current_user(request)
    enrollments = await db.enrollments.find(
        {"user_id": user["id"], "completed": True}
    ).to_list(100)

    certificates = []
    for e in enrollments:
        course = await db.courses.find_one({"_id": ObjectId(e["course_id"])})
        if not course:
            continue

        cert = await db.certificates.find_one(
            {"course_id": e["course_id"], "user_id": user["id"]}
        )
        if not cert:
            cert_doc = {
                "course_id": e["course_id"],
                "user_id": user["id"],
                "user_name": user["name"],
                "course_title": course.get("title"),
                "score": e.get("score", 0),
                "template": "default",
                "primary_color": "#002FA7",
                "secondary_color": "#0A0B10",
                "issued_at": datetime.now(timezone.utc).isoformat(),
                "certificate_id": str(uuid.uuid4())[:8].upper(),
            }
            result = await db.certificates.insert_one(cert_doc)
            cert = {**cert_doc, "_id": result.inserted_id}

        certificates.append({
            "id": str(cert["_id"]),
            "certificate_id": cert.get("certificate_id"),
            "course_id": cert["course_id"],
            "course_title": cert.get("course_title"),
            "user_name": cert.get("user_name"),
            "score": cert.get("score"),
            "template": cert.get("template"),
            "primary_color": cert.get("primary_color"),
            "secondary_color": cert.get("secondary_color"),
            "issued_at": cert.get("issued_at"),
        })
    return certificates


@router.get("/certificates/{certificate_id}/pdf")
async def download_certificate_pdf(certificate_id: str, request: Request):
    user = await get_current_user(request)
    cert = await db.certificates.find_one({"_id": ObjectId(certificate_id)})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if user["role"] not in ["admin", "client_manager"] and cert.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to download this certificate")

    pdf_bytes = generate_certificate_pdf(cert)
    filename = f"certificate-{cert.get('certificate_id', certificate_id)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/certificates/{certificate_id}")
async def get_certificate(certificate_id: str, request: Request):
    user = await get_current_user(request)
    cert = await db.certificates.find_one({"_id": ObjectId(certificate_id)})
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if user["role"] not in ["admin", "client_manager"] and cert.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this certificate")
    return {
        "id": str(cert["_id"]),
        "certificate_id": cert.get("certificate_id"),
        "course_id": cert["course_id"],
        "course_title": cert.get("course_title"),
        "user_name": cert.get("user_name"),
        "score": cert.get("score"),
        "template": cert.get("template"),
        "primary_color": cert.get("primary_color"),
        "secondary_color": cert.get("secondary_color"),
        "issued_at": cert.get("issued_at"),
    }


@router.put("/certificates/{certificate_id}/customize")
async def customize_certificate(
    certificate_id: str, data: CertificateCustomize, request: Request
):
    await require_roles("admin")(request)
    cert = await db.certificates.find_one({"_id": ObjectId(certificate_id)})
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
            {"_id": ObjectId(certificate_id)},
            {"$set": update_fields},
        )
    return {"message": f"Updated {result.modified_count} certificate(s)"}
