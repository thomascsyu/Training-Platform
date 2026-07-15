from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from auth_utils import require_roles
from upload_utils import (
    certificate_background_public_url,
    get_certificate_background_dir,
    get_thumbnail_dir,
    save_certificate_background,
    save_thumbnail,
    thumbnail_public_url,
    validate_certificate_background_upload,
    validate_thumbnail_upload,
)

router = APIRouter(tags=["uploads"])


@router.post("/uploads/thumbnail")
async def upload_thumbnail(request: Request, file: UploadFile = File(...)):
    await require_roles("admin")(request)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    extension = validate_thumbnail_upload(
        content=content,
        content_type=file.content_type,
        filename=file.filename,
    )
    filename = save_thumbnail(content, extension)
    return {"url": thumbnail_public_url(filename)}


@router.get("/uploads/thumbnails/{filename}")
async def get_thumbnail(filename: str):
    # Reject path traversal and nested paths.
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumbnail_path = get_thumbnail_dir() / safe_name
    if not thumbnail_path.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    return FileResponse(path=thumbnail_path)


@router.post("/uploads/certificate-background")
async def upload_certificate_background(request: Request, file: UploadFile = File(...)):
    await require_roles("admin")(request)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content = await file.read()
    extension = validate_certificate_background_upload(
        content=content,
        content_type=file.content_type,
        filename=file.filename,
    )
    filename = save_certificate_background(content, extension)
    return {"url": certificate_background_public_url(filename)}


@router.get("/uploads/certificate-backgrounds/{filename}")
async def get_certificate_background(filename: str):
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=404, detail="Certificate background not found")

    background_path = get_certificate_background_dir() / safe_name
    if not background_path.is_file():
        raise HTTPException(status_code=404, detail="Certificate background not found")

    return FileResponse(path=background_path)
