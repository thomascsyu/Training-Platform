import html
import re
from datetime import datetime
from urllib.parse import urlparse

_PRIMARY_DEFAULT = "#002FA7"
_SECONDARY_DEFAULT = "#0A0B10"
_TEXT_MUTED = "#64748B"
_TEXT_PRIMARY = "#0A0B10"
_BACKGROUND = "#F4F5F7"

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_color(value: str, fallback: str) -> str:
    if isinstance(value, str) and _COLOR_RE.match(value.strip()):
        return value.strip().lower()
    return fallback.lower()


def _safe(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    return html.escape(str(value))


def _safe_background_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(str(value).strip())
    if parsed.scheme not in {"http", "https"} and not str(value).startswith("/"):
        return ""
    return html.escape(str(value).strip(), quote=True)


def _format_score(value: int | float | str | None) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _format_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime("%B %d, %Y")
    except Exception:
        return html.escape(str(value)[:10])


def _format_valid_until(value: str | None) -> str:
    if not value:
        return "No expiration"
    return _format_date(value)


def _base_certificate_html(primary: str, secondary: str, background_url: str = "") -> str:
    background = _safe_background_url(background_url)
    background_style = ""
    if background:
        background_style = (
            "background-image: linear-gradient(rgba(255,255,255,0.86), "
            f"rgba(255,255,255,0.9)), url('{background}'); "
            "background-size: cover; background-position: center;"
        )
    return _CERTIFICATE_HTML.replace("__PRIMARY_COLOR__", primary).replace(
        "__SECONDARY_COLOR__", secondary
    ).replace("__BACKGROUND_IMAGE_STYLE__", background_style)


def create_certification_template_source(
    primary_color: str = _PRIMARY_DEFAULT,
    secondary_color: str = _SECONDARY_DEFAULT,
    background_url: str = "",
) -> str:
    """Return reusable certificate template HTML with user-data placeholders."""
    primary = _validate_color(primary_color, _PRIMARY_DEFAULT)
    secondary = _validate_color(secondary_color, _SECONDARY_DEFAULT)
    return (
        _base_certificate_html(primary, secondary, background_url)
        .replace("__USER_NAME__", "{{user_name}}")
        .replace("__COURSE_TITLE__", "{{course_title}}")
        .replace("__SCORE__", "{{score}}")
        .replace("__CERTIFICATE_ID__", "{{certificate_id}}")
        .replace("__ISSUED_AT__", "{{issued_at}}")
        .replace("__VALID_UNTIL__", "{{valid_until}}")
    )


def render_certification_template(template_html: str, cert: dict) -> str:
    """Render certificate data into a reusable HTML certificate template."""
    values = {
        "user_name": _safe(cert.get("user_name"), "Student"),
        "course_title": _safe(cert.get("course_title", cert.get("course", "Course"))),
        "score": str(_format_score(cert.get("score"))),
        "certificate_id": _safe(cert.get("certificate_id"), "—"),
        "issued_at": _format_date(cert.get("issued_at")),
        "valid_until": _format_valid_until(cert.get("valid_until")),
    }
    replacements = {
        "__USER_NAME__": values["user_name"],
        "__COURSE_TITLE__": values["course_title"],
        "__SCORE__": values["score"],
        "__CERTIFICATE_ID__": values["certificate_id"],
        "__ISSUED_AT__": values["issued_at"],
        "__VALID_UNTIL__": values["valid_until"],
        "{{user_name}}": values["user_name"],
        "{{course_title}}": values["course_title"],
        "{{score}}": values["score"],
        "{{certificate_id}}": values["certificate_id"],
        "{{issued_at}}": values["issued_at"],
        "{{valid_until}}": values["valid_until"],
    }
    rendered = template_html
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def create_certification_template(cert: dict) -> str:
    """Return a styled HTML training certificate for the given certificate data.

    Design reference: https://claude.ai/design/p/5f15a85e-9833-48c2-8e02-b82b726e130d
    The template follows the LearnHub design system (International Klein Blue, high
    contrast, sharp edges) and is safe to render with untrusted certificate fields.
    """
    primary = _validate_color(cert.get("primary_color"), _PRIMARY_DEFAULT)
    secondary = _validate_color(cert.get("secondary_color"), _SECONDARY_DEFAULT)
    return render_certification_template(
        _base_certificate_html(primary, secondary, cert.get("background_url", "")),
        cert,
    )


_CERTIFICATE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Training Certificate - __COURSE_TITLE__</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: 11in 8.5in landscape;
      margin: 0;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
      background: __BACKGROUND__;
      color: __TEXT_PRIMARY__;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .certificate {
      width: 11in;
      height: 8.5in;
      background: #FFFFFF;
      __BACKGROUND_IMAGE_STYLE__
      position: relative;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(10, 11, 16, 0.12);
    }
    .accent-bar {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 14px;
      background: linear-gradient(90deg, __PRIMARY_COLOR__, __SECONDARY_COLOR__);
    }
    .frame-outer {
      position: absolute;
      top: 0.5in;
      left: 0.5in;
      right: 0.5in;
      bottom: 0.5in;
      border: 4px solid __PRIMARY_COLOR__;
    }
    .frame-inner {
      position: absolute;
      top: 0.65in;
      left: 0.65in;
      right: 0.65in;
      bottom: 0.65in;
      border: 1px solid __SECONDARY_COLOR__;
    }
    .content {
      position: absolute;
      top: 0.85in;
      left: 0.85in;
      right: 0.85in;
      bottom: 0.85in;
      text-align: center;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 0 0.5in;
    }
    .badge {
      width: 84px;
      height: 84px;
      color: __PRIMARY_COLOR__;
      margin-bottom: 24px;
    }
    .overline {
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: __TEXT_MUTED__;
      margin-bottom: 12px;
    }
    h1 {
      font-family: "Playfair Display", Georgia, serif;
      font-size: 52px;
      font-weight: 700;
      color: __SECONDARY_COLOR__;
      margin: 0 0 28px;
      letter-spacing: -0.02em;
      line-height: 1.1;
    }
    .presented {
      font-size: 16px;
      color: __TEXT_MUTED__;
      margin-bottom: 10px;
    }
    .recipient {
      font-size: 44px;
      font-weight: 700;
      color: __PRIMARY_COLOR__;
      margin: 0 0 14px;
      line-height: 1.2;
      max-width: 9in;
    }
    .course {
      font-size: 26px;
      font-weight: 600;
      color: __TEXT_PRIMARY__;
      margin: 0 0 10px;
      max-width: 8.5in;
      line-height: 1.3;
    }
    .score {
      font-size: 16px;
      color: __TEXT_MUTED__;
      margin-bottom: 44px;
    }
    .score strong {
      color: __TEXT_PRIMARY__;
      font-weight: 600;
    }
    .footer {
      position: absolute;
      left: 1.1in;
      right: 1.1in;
      bottom: 1.1in;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 13px;
      color: __TEXT_MUTED__;
    }
    .signature {
      text-align: center;
    }
    .signature-line {
      width: 2.2in;
      border-top: 1px solid __SECONDARY_COLOR__;
      margin: 0 auto 6px;
    }
    .signature-label {
      font-size: 12px;
      font-weight: 600;
      color: __TEXT_PRIMARY__;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .meta {
      text-align: right;
      line-height: 1.6;
    }
    .meta strong {
      color: __TEXT_PRIMARY__;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="certificate">
    <div class="accent-bar"></div>
    <div class="frame-outer"></div>
    <div class="frame-inner"></div>
    <div class="content">
      <svg class="badge" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="8" r="6"></circle>
        <path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"></path>
      </svg>
      <div class="overline">Training Certificate</div>
      <h1>Certificate of Completion</h1>
      <div class="presented">This certifies that</div>
      <div class="recipient">__USER_NAME__</div>
      <div class="presented">has successfully completed</div>
      <div class="course">__COURSE_TITLE__</div>
      <div class="score">with a score of <strong>__SCORE__%</strong></div>
    </div>
    <div class="footer">
      <div class="signature">
        <div class="signature-line"></div>
        <div class="signature-label">LearnHub</div>
      </div>
      <div class="meta">
        <div>Certificate ID: <strong>__CERTIFICATE_ID__</strong></div>
        <div>Issued: <strong>__ISSUED_AT__</strong></div>
        <div>Valid until: <strong>__VALID_UNTIL__</strong></div>
      </div>
    </div>
  </div>
</body>
</html>
""".replace("__BACKGROUND__", _BACKGROUND).replace("__TEXT_PRIMARY__", _TEXT_PRIMARY).replace("__TEXT_MUTED__", _TEXT_MUTED)
