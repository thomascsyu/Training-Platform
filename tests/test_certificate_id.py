from unittest.mock import AsyncMock, MagicMock

import pytest

from certificate_id import (
    DEFAULT_CERTIFICATE_ID_FORMAT,
    course_code_from,
    format_certificate_id,
    generate_certificate_id,
    preview_certificate_id,
    validate_certificate_id_format,
)


def test_format_seq_padding_and_year():
    result = format_certificate_id(
        "CERT-{year}-{seq:6}", sequence=42, issued_at="2026-07-13T10:00:00+00:00"
    )
    assert result == "CERT-2026-000042"


def test_format_month_day_and_literal_text():
    result = format_certificate_id(
        "ID/{year}{month}{day}/{seq}", sequence=5, issued_at="2026-01-09T00:00:00"
    )
    assert result == "ID/20260109/5"


def test_format_course_token():
    result = format_certificate_id(
        "{course}-{seq:3}", sequence=7, course_code="SECURITY"
    )
    assert result == "SECURITY-007"


def test_format_random_token_length():
    result = format_certificate_id("{random:8}", sequence=1)
    assert len(result) == 8
    assert result.isalnum()


def test_course_code_from_sanitises_and_truncates():
    assert course_code_from("Security & Compliance 101") == "SECURI"
    assert course_code_from("Data Science", length=4) == "DATA"
    assert course_code_from(None) == ""


def test_validate_rejects_unknown_token():
    with pytest.raises(ValueError):
        validate_certificate_id_format("CERT-{unknown}")


def test_validate_rejects_empty():
    with pytest.raises(ValueError):
        validate_certificate_id_format("   ")


def test_validate_accepts_known_tokens():
    assert validate_certificate_id_format("  CERT-{year}-{seq:5}  ") == "CERT-{year}-{seq:5}"


def test_preview_uses_default_format():
    preview = preview_certificate_id(DEFAULT_CERTIFICATE_ID_FORMAT, sequence=3)
    assert preview.startswith("CERT-")
    assert preview.endswith("000003")


@pytest.mark.asyncio
async def test_generate_certificate_id_increments_sequence():
    mock_db = MagicMock()
    mock_db.platform_settings = MagicMock()
    mock_db.platform_settings.find_one_and_update = AsyncMock(
        return_value={"id_format": "CERT-{year}-{seq:4}", "sequence": 12}
    )
    result = await generate_certificate_id(
        mock_db, issued_at="2026-07-13T00:00:00+00:00", course_title="Security"
    )
    assert result == "CERT-2026-0012"
    mock_db.platform_settings.find_one_and_update.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_certificate_id_falls_back_on_invalid_format():
    mock_db = MagicMock()
    mock_db.platform_settings = MagicMock()
    mock_db.platform_settings.find_one_and_update = AsyncMock(
        return_value={"id_format": "{bogus}", "sequence": 1}
    )
    result = await generate_certificate_id(mock_db, issued_at="2026-07-13T00:00:00+00:00")
    assert result.startswith("CERT-2026-")
