"""Configurable certificate ID naming structure.

Certificate IDs used to be a random 8-character UUID slice. The naming
structure is now configurable from the certificate module itself (not from the
course settings screen). Admins define a *format* string built from literal
text and tokens; each issued certificate expands the tokens against a running
sequence counter and the issuance date.

Supported tokens:

* ``{seq}`` / ``{seq:N}``      – running sequence number, optionally zero-padded
                                 to ``N`` digits (e.g. ``{seq:6}`` -> ``000042``)
* ``{year}``                   – four-digit issuance year
* ``{month}`` / ``{day}``      – two-digit issuance month / day
* ``{random}`` / ``{random:N}``– random uppercase-alphanumeric run (default 4)
* ``{course}``                 – short, sanitised course code

Anything outside a recognised token is treated as a literal, so a format such
as ``CERT-{year}-{seq:5}`` produces ``CERT-2026-00042``.
"""

import random
import re
import string
from datetime import datetime, timezone

try:  # pragma: no cover - import shape differs across pymongo versions
    from pymongo import ReturnDocument
except Exception:  # pragma: no cover
    ReturnDocument = None

DEFAULT_CERTIFICATE_ID_FORMAT = "CERT-{year}-{seq:6}"
CERTIFICATE_SETTINGS_ID = "certificate"

_ALPHABET = string.ascii_uppercase + string.digits
_TOKEN_RE = re.compile(r"\{(seq|year|month|day|random|course)(?::(\d+))?\}")
_ALLOWED_TOKENS = {"seq", "year", "month", "day", "random", "course"}
# Unknown ``{...}`` groups are rejected by the validator.
_ANY_TOKEN_RE = re.compile(r"\{([^{}]*)\}")
_MAX_FORMAT_LENGTH = 120


def course_code_from(title: str | None, length: int = 6) -> str:
    """Derive a short uppercase alphanumeric course code from a course title."""
    if not title:
        return ""
    code = re.sub(r"[^A-Za-z0-9]", "", str(title)).upper()
    return code[:length]


def validate_certificate_id_format(fmt: str) -> str:
    """Validate a certificate ID format string, returning it trimmed.

    Raises ``ValueError`` when the format is empty, too long, or contains an
    unrecognised ``{token}``.
    """
    if not isinstance(fmt, str):
        raise ValueError("Certificate ID format must be a string")
    value = fmt.strip()
    if not value:
        raise ValueError("Certificate ID format cannot be empty")
    if len(value) > _MAX_FORMAT_LENGTH:
        raise ValueError(
            f"Certificate ID format cannot exceed {_MAX_FORMAT_LENGTH} characters"
        )
    for match in _ANY_TOKEN_RE.finditer(value):
        token = match.group(1).split(":", 1)[0]
        if token not in _ALLOWED_TOKENS:
            raise ValueError(f"Unknown token '{{{match.group(1)}}}' in format")
    return value


def format_certificate_id(
    fmt: str,
    *,
    sequence: int,
    issued_at: str | datetime | None = None,
    course_code: str | None = None,
) -> str:
    """Expand a certificate ID *format* into a concrete certificate ID."""
    issued = _coerce_datetime(issued_at)

    def _replace(match: re.Match) -> str:
        token, arg = match.group(1), match.group(2)
        if token == "seq":
            width = int(arg) if arg else 0
            return str(int(sequence)).zfill(width)
        if token == "year":
            return f"{issued.year:04d}"
        if token == "month":
            return f"{issued.month:02d}"
        if token == "day":
            return f"{issued.day:02d}"
        if token == "random":
            width = int(arg) if arg else 4
            return "".join(random.choices(_ALPHABET, k=max(1, width)))
        if token == "course":
            return course_code or ""
        return match.group(0)

    return _TOKEN_RE.sub(_replace, fmt)


def _coerce_datetime(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def preview_certificate_id(fmt: str, *, sequence: int = 1, course_code: str = "COURSE") -> str:
    """Return an example certificate ID for the given format (for admin UIs)."""
    return format_certificate_id(
        fmt, sequence=sequence, issued_at=datetime.now(timezone.utc), course_code=course_code
    )


async def get_certificate_id_format(database) -> str:
    """Return the configured certificate ID format, or the built-in default."""
    doc = await database.platform_settings.find_one({"_id": CERTIFICATE_SETTINGS_ID})
    fmt = (doc or {}).get("id_format")
    if isinstance(fmt, str) and fmt.strip():
        return fmt.strip()
    return DEFAULT_CERTIFICATE_ID_FORMAT


async def generate_certificate_id(
    database,
    *,
    issued_at: str | datetime | None = None,
    course_title: str | None = None,
) -> str:
    """Atomically reserve the next sequence number and build a certificate ID."""
    kwargs = {"upsert": True}
    if ReturnDocument is not None:
        kwargs["return_document"] = ReturnDocument.AFTER
    doc = await database.platform_settings.find_one_and_update(
        {"_id": CERTIFICATE_SETTINGS_ID},
        {
            "$inc": {"sequence": 1},
            "$setOnInsert": {"id_format": DEFAULT_CERTIFICATE_ID_FORMAT},
        },
        **kwargs,
    )
    doc = doc or {}
    fmt = doc.get("id_format") or DEFAULT_CERTIFICATE_ID_FORMAT
    sequence = doc.get("sequence", 1) or 1
    try:
        fmt = validate_certificate_id_format(fmt)
    except ValueError:
        fmt = DEFAULT_CERTIFICATE_ID_FORMAT
    return format_certificate_id(
        fmt,
        sequence=sequence,
        issued_at=issued_at,
        course_code=course_code_from(course_title),
    )
