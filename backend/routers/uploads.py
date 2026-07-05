from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from auth_utils import require_roles
from upload_utils import (
    save_thumbnail,
    thumbnail_public_url,
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
