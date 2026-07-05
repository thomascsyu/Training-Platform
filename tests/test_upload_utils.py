import pytest
from fastapi import HTTPException

from upload_utils import (
    detect_image_extension,
    get_uploads_root,
    save_thumbnail,
    thumbnail_public_url,
    validate_thumbnail_upload,
)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc"
    b"\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)
JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.\x27 ,#\x1c\x1c(7),01444\x1f\x27=9=82<.342\xff\xc0\x00\x0b\x08"
    b"\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01"
    b"\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
    b"\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05"
    b"\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa"
    b"\x07\"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17"
    b"\x18\x19\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85"
    b"\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5"
    b"\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5"
    b"\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4"
    b"\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda"
    b"\x00\x08\x01\x01\x00\x00?\x00\xfb\xd0\xff\xd9"
)


def test_detect_image_extension_for_png():
    assert detect_image_extension(PNG_BYTES) == ".png"


def test_detect_image_extension_for_jpeg():
    assert detect_image_extension(JPEG_BYTES) == ".jpg"


def test_validate_thumbnail_upload_rejects_invalid_content():
    with pytest.raises(HTTPException) as exc_info:
        validate_thumbnail_upload(
            content=b"not-an-image",
            content_type="image/png",
            filename="thumb.png",
        )

    assert exc_info.value.status_code == 400


def test_validate_thumbnail_upload_rejects_large_file():
    with pytest.raises(HTTPException) as exc_info:
        validate_thumbnail_upload(
            content=PNG_BYTES + (b"0" * (5 * 1024 * 1024)),
            content_type="image/png",
            filename="thumb.png",
        )

    assert exc_info.value.status_code == 400
    assert "5MB" in exc_info.value.detail


def test_save_thumbnail_writes_file(tmp_path, monkeypatch):
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("upload_utils.get_thumbnail_dir", lambda: tmp_path)
    extension = validate_thumbnail_upload(
        content=JPEG_BYTES,
        content_type="image/jpeg",
        filename="course.jpg",
    )
    filename = save_thumbnail(JPEG_BYTES, extension)

    saved_file = tmp_path / filename
    assert saved_file.exists()
    assert filename.endswith(".jpg")
    assert thumbnail_public_url(filename) == f"/api/uploads/thumbnails/{filename}"


def test_get_uploads_root_uses_uploads_dir_env(tmp_path, monkeypatch):
    uploads_root = tmp_path / "custom-uploads"
    monkeypatch.setenv("UPLOADS_DIR", str(uploads_root))

    assert get_uploads_root() == uploads_root.resolve()

    extension = validate_thumbnail_upload(
        content=JPEG_BYTES,
        content_type="image/jpeg",
        filename="course.jpg",
    )
    filename = save_thumbnail(JPEG_BYTES, extension)

    saved_file = uploads_root / "thumbnails" / filename
    assert saved_file.exists()
    assert saved_file.read_bytes() == JPEG_BYTES
