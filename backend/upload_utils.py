import os
import uuid
from pathlib import Path

from fastapi import HTTPException

ALLOWED_THUMBNAIL_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_THUMBNAIL_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_THUMBNAIL_SIZE_BYTES = 5 * 1024 * 1024

# Certificate backgrounds share the same image rules as course thumbnails.
ALLOWED_CERTIFICATE_BACKGROUND_CONTENT_TYPES = ALLOWED_THUMBNAIL_CONTENT_TYPES
ALLOWED_CERTIFICATE_BACKGROUND_EXTENSIONS = ALLOWED_THUMBNAIL_EXTENSIONS
MAX_CERTIFICATE_BACKGROUND_SIZE_BYTES = MAX_THUMBNAIL_SIZE_BYTES


def get_uploads_root() -> Path:
    configured = os.environ.get("UPLOADS_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parent / "uploads"


def get_thumbnail_dir() -> Path:
    return get_uploads_root() / "thumbnails"


def get_certificate_background_dir() -> Path:
    return get_uploads_root() / "certificate-backgrounds"


# Backward-compatible aliases used by tests and imports.
UPLOADS_ROOT = get_uploads_root()
THUMBNAIL_DIR = get_thumbnail_dir()


def ensure_thumbnail_dir() -> Path:
    thumbnail_dir = get_thumbnail_dir()
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


def ensure_certificate_background_dir() -> Path:
    background_dir = get_certificate_background_dir()
    background_dir.mkdir(parents=True, exist_ok=True)
    return background_dir


def detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    return None


def _validate_image_upload(
    *,
    content: bytes,
    content_type: str | None,
    filename: str | None,
    allowed_types: set[str],
    allowed_extensions: set[str],
    max_size_bytes: int,
) -> str:
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(content) > max_size_bytes:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    extension = detect_image_extension(content)
    if extension is None:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    declared_type = (content_type or "").split(";", 1)[0].strip().lower()
    if declared_type and declared_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    declared_extension = Path(filename or "").suffix.lower()
    if declared_extension and declared_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are allowed")

    return extension


def validate_thumbnail_upload(
    *,
    content: bytes,
    content_type: str | None,
    filename: str | None,
) -> str:
    return _validate_image_upload(
        content=content,
        content_type=content_type,
        filename=filename,
        allowed_types=ALLOWED_THUMBNAIL_CONTENT_TYPES,
        allowed_extensions=ALLOWED_THUMBNAIL_EXTENSIONS,
        max_size_bytes=MAX_THUMBNAIL_SIZE_BYTES,
    )


def validate_certificate_background_upload(
    *,
    content: bytes,
    content_type: str | None,
    filename: str | None,
) -> str:
    return _validate_image_upload(
        content=content,
        content_type=content_type,
        filename=filename,
        allowed_types=ALLOWED_CERTIFICATE_BACKGROUND_CONTENT_TYPES,
        allowed_extensions=ALLOWED_CERTIFICATE_BACKGROUND_EXTENSIONS,
        max_size_bytes=MAX_CERTIFICATE_BACKGROUND_SIZE_BYTES,
    )


def save_thumbnail(content: bytes, extension: str) -> str:
    thumbnail_dir = ensure_thumbnail_dir()
    filename = f"{uuid.uuid4().hex}{extension}"
    (thumbnail_dir / filename).write_bytes(content)
    return filename


def save_certificate_background(content: bytes, extension: str) -> str:
    background_dir = ensure_certificate_background_dir()
    filename = f"{uuid.uuid4().hex}{extension}"
    (background_dir / filename).write_bytes(content)
    return filename


def thumbnail_public_url(filename: str) -> str:
    return f"/api/uploads/thumbnails/{filename}"


def certificate_background_public_url(filename: str) -> str:
    return f"/api/uploads/certificate-backgrounds/{filename}"


def resolve_certificate_background_path(url: str | None) -> Path | None:
    """Map a public certificate-background URL to a local file path, if valid."""
    if not url or not isinstance(url, str):
        return None
    prefix = "/api/uploads/certificate-backgrounds/"
    if not url.startswith(prefix):
        return None
    filename = Path(url[len(prefix) :]).name
    if not filename or filename != url[len(prefix) :]:
        return None
    path = get_certificate_background_dir() / filename
    if not path.is_file():
        return None
    return path
