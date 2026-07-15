import pytest
from fastapi import HTTPException

from upload_utils import (
    certificate_background_public_url,
    resolve_certificate_background_path,
    save_certificate_background,
    validate_certificate_background_upload,
)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc"
    b"\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_validate_certificate_background_upload_accepts_png():
    extension = validate_certificate_background_upload(
        content=PNG_BYTES,
        content_type="image/png",
        filename="bg.png",
    )
    assert extension == ".png"


def test_validate_certificate_background_upload_rejects_invalid_type():
    with pytest.raises(HTTPException) as exc_info:
        validate_certificate_background_upload(
            content=b"not-an-image",
            content_type="image/png",
            filename="bg.png",
        )
    assert exc_info.value.status_code == 400


def test_validate_certificate_background_upload_rejects_large_file():
    with pytest.raises(HTTPException) as exc_info:
        validate_certificate_background_upload(
            content=PNG_BYTES + (b"0" * (5 * 1024 * 1024)),
            content_type="image/png",
            filename="bg.png",
        )
    assert exc_info.value.status_code == 400
    assert "5MB" in exc_info.value.detail


def test_save_certificate_background_and_resolve_path(tmp_path, monkeypatch):
    monkeypatch.setattr("upload_utils.get_certificate_background_dir", lambda: tmp_path)
    filename = save_certificate_background(PNG_BYTES, ".png")
    url = certificate_background_public_url(filename)
    assert url == f"/api/uploads/certificate-backgrounds/{filename}"
    assert (tmp_path / filename).read_bytes() == PNG_BYTES
    resolved = resolve_certificate_background_path(url)
    assert resolved == tmp_path / filename


def test_resolve_certificate_background_path_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("upload_utils.get_certificate_background_dir", lambda: tmp_path)
    assert resolve_certificate_background_path("/api/uploads/certificate-backgrounds/../x.png") is None
    assert resolve_certificate_background_path("/api/uploads/thumbnails/x.png") is None
