from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from auth_utils import require_roles
from upload_utils import (
    get_thumbnail_dir,
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
