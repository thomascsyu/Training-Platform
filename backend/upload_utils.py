import uuid
from pathlib import Path

from fastapi import HTTPException

UPLOADS_ROOT = Path(__file__).resolve().parent / "uploads"
THUMBNAIL_DIR = UPLOADS_ROOT / "thumbnails"

ALLOWED_THUMBNAIL_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_THUMBNAIL_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_THUMBNAIL_SIZE_BYTES = 5 * 1024 * 1024


def ensure_thumbnail_dir() -> Path:
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
    return THUMBNAIL_DIR


def detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    return None


def validate_thumbnail_upload(
    *,
    content: bytes,
    content_type: str | None,
    filename: str | None,
) -> str:
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(content) > MAX_THUMBNAIL_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    extension = detect_image_extension(content)
    if extension is None:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    declared_type = (content_type or "").split(";", 1)[0].strip().lower()
    if declared_type and declared_type not in ALLOWED_THUMBNAIL_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    declared_extension = Path(filename or "").suffix.lower()
    if declared_extension and declared_extension not in ALLOWED_THUMBNAIL_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    return extension


def save_thumbnail(content: bytes, extension: str) -> str:
    ensure_thumbnail_dir()
    filename = f"{uuid.uuid4().hex}{extension}"
    (THUMBNAIL_DIR / filename).write_bytes(content)
    return filename


def thumbnail_public_url(filename: str) -> str:
    return f"/api/uploads/thumbnails/{filename}"
