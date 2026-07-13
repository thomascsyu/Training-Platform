import html
import re
from datetime import datetime

_PRIMARY_DEFAULT = "#002FA7"
_SECONDARY_DEFAULT = "#0A0B10"
_TEXT_MUTED = "#64748B"
_TEXT_PRIMARY = "#0A0B10"
_BACKGROUND = "#F4F5F7"

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# Selectable background artworks for certificates. The first entry ("plain") is
# the default and keeps the original clean look; the remaining four add a
# decorative pattern rendered behind the certificate content.
CERTIFICATE_BACKGROUNDS = [
    {"key": "plain", "label": "Plain"},
    {"key": "geometric", "label": "Geometric"},
    {"key": "waves", "label": "Waves"},
    {"key": "guilloche", "label": "Guilloché"},
    {"key": "corners", "label": "Corner Flourish"},
]
_BACKGROUND_KEYS = {bg["key"] for bg in CERTIFICATE_BACKGROUNDS}
DEFAULT_BACKGROUND = "plain"


def normalize_background(value: str | None) -> str:
    """Return a valid background artwork key, falling back to the default."""
    if isinstance(value, str) and value.strip() in _BACKGROUND_KEYS:
        return value.strip()
    return DEFAULT_BACKGROUND


def _render_artwork(background: str, primary: str, secondary: str) -> str:
    """Return an SVG artwork layer (with colors already inlined) for a background."""
    key = normalize_background(background)
    svg = _ARTWORK_SVGS.get(key, "")
    if not svg:
        return ""
    svg = svg.replace("__PRIMARY__", primary).replace("__SECONDARY__", secondary)
    return f'<div class="artwork" aria-hidden="true">{svg}</div>'


def _validate_color(value: str, fallback: str) -> str:
    if isinstance(value, str) and _COLOR_RE.match(value.strip()):
        return value.strip().lower()
    return fallback.lower()


def _safe(value: str | None, default: str = "") -> str:
    if value is None:
        return default
    return html.escape(str(value))


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


CERTIFICATE_VALIDITY_YEARS = 1


def compute_valid_until(issued_at: str | None, years: int = CERTIFICATE_VALIDITY_YEARS) -> str | None:
    """Return the ISO timestamp a certificate expires, one year after issuance."""
    if not issued_at:
        return None
    try:
        issued = datetime.fromisoformat(str(issued_at))
    except (TypeError, ValueError):
        return None
    try:
        expiry = issued.replace(year=issued.year + years)
    except ValueError:
        # Issued on Feb 29; the expiry year has no such day.
        expiry = issued.replace(month=2, day=28, year=issued.year + years)
    return expiry.isoformat()


def is_certificate_expired(valid_until: str | None) -> bool:
    """Return True if the given expiry timestamp has passed."""
    if not valid_until:
        return False
    try:
        expiry = datetime.fromisoformat(str(valid_until))
    except (TypeError, ValueError):
        return False
    now = datetime.now(expiry.tzinfo) if expiry.tzinfo else datetime.now()
    return now > expiry


def _base_certificate_html(
    primary: str, secondary: str, background: str = DEFAULT_BACKGROUND
) -> str:
    # Insert the artwork (with real colors already inlined) before running the
    # placeholder colour substitution so the artwork colours are untouched.
    artwork = _render_artwork(background, primary, secondary)
    return (
        _CERTIFICATE_HTML.replace("__ARTWORK__", artwork)
        .replace("__PRIMARY_COLOR__", primary)
        .replace("__SECONDARY_COLOR__", secondary)
    )


def create_certification_template_source(
    primary_color: str = _PRIMARY_DEFAULT,
    secondary_color: str = _SECONDARY_DEFAULT,
    background: str = DEFAULT_BACKGROUND,
) -> str:
    """Return reusable certificate template HTML with user-data placeholders."""
    primary = _validate_color(primary_color, _PRIMARY_DEFAULT)
    secondary = _validate_color(secondary_color, _SECONDARY_DEFAULT)
    return (
        _base_certificate_html(primary, secondary, background)
        .replace("__USER_NAME__", "{{user_name}}")
        .replace("__COURSE_TITLE__", "{{course_title}}")
        .replace("__SCORE__", "{{score}}")
        .replace("__CERTIFICATE_ID__", "{{certificate_id}}")
        .replace("__ISSUED_AT__", "{{issued_at}}")
        .replace("__VALID_UNTIL__", "{{valid_until}}")
    )


def render_certification_template(template_html: str, cert: dict) -> str:
    """Render certificate data into a reusable HTML certificate template."""
    valid_until = cert.get("valid_until") or compute_valid_until(cert.get("issued_at"))
    expired = is_certificate_expired(valid_until)
    values = {
        "user_name": _safe(cert.get("user_name"), "Student"),
        "course_title": _safe(cert.get("course_title", cert.get("course", "Course"))),
        "score": str(_format_score(cert.get("score"))),
        "certificate_id": _safe(cert.get("certificate_id"), "—"),
        "issued_at": _format_date(cert.get("issued_at")),
        "valid_until": _format_date(valid_until),
    }
    replacements = {
        "__USER_NAME__": values["user_name"],
        "__COURSE_TITLE__": values["course_title"],
        "__SCORE__": values["score"],
        "__CERTIFICATE_ID__": values["certificate_id"],
        "__ISSUED_AT__": values["issued_at"],
        "__VALID_UNTIL__": values["valid_until"],
        "__EXPIRED_BADGE__": _EXPIRED_BADGE_HTML if expired else "",
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
    background = normalize_background(cert.get("background"))
    return render_certification_template(
        _base_certificate_html(primary, secondary, background),
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
      position: relative;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(10, 11, 16, 0.12);
    }
    .artwork {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
    }
    .artwork svg {
      width: 100%;
      height: 100%;
      display: block;
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
    .expired-stamp {
      position: absolute;
      top: 55%;
      left: 50%;
      transform: translate(-50%, -50%) rotate(-18deg);
      font-family: "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
      font-size: 64px;
      font-weight: 700;
      letter-spacing: 0.15em;
      color: #DC2626;
      border: 6px solid #DC2626;
      padding: 8px 32px;
      opacity: 0.35;
      pointer-events: none;
      z-index: 10;
    }
  </style>
</head>
<body>
  <div class="certificate">
    __ARTWORK__
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
        <div>Valid Until: <strong>__VALID_UNTIL__</strong></div>
      </div>
    </div>
    __EXPIRED_BADGE__
  </div>
</body>
</html>
""".replace("__BACKGROUND__", _BACKGROUND).replace("__TEXT_PRIMARY__", _TEXT_PRIMARY).replace("__TEXT_MUTED__", _TEXT_MUTED)

_EXPIRED_BADGE_HTML = '<div class="expired-stamp">Expired</div>'

# Decorative background artworks. Each SVG uses __PRIMARY__ / __SECONDARY__
# placeholders that are replaced with the certificate colours before rendering.
# Opacity is kept low so the artwork never competes with the certificate text.
_ARTWORK_SVGS = {
    "geometric": """
<svg viewBox="0 0 1100 850" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="geo" width="70" height="70" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="70" height="70" fill="none"/>
      <path d="M0 35 H70 M35 0 V70" stroke="__PRIMARY__" stroke-width="1" opacity="0.06"/>
      <circle cx="35" cy="35" r="3" fill="__SECONDARY__" opacity="0.05"/>
    </pattern>
  </defs>
  <rect width="1100" height="850" fill="url(#geo)"/>
  <polygon points="0,0 300,0 0,300" fill="__PRIMARY__" opacity="0.05"/>
  <polygon points="1100,850 800,850 1100,550" fill="__SECONDARY__" opacity="0.05"/>
</svg>
""",
    "waves": """
<svg viewBox="0 0 1100 850" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke-width="2" opacity="0.08">
    <path d="M0 120 Q 275 40 550 120 T 1100 120" stroke="__PRIMARY__"/>
    <path d="M0 180 Q 275 100 550 180 T 1100 180" stroke="__PRIMARY__"/>
    <path d="M0 240 Q 275 160 550 240 T 1100 240" stroke="__SECONDARY__"/>
  </g>
  <g fill="none" stroke-width="2" opacity="0.08">
    <path d="M0 730 Q 275 650 550 730 T 1100 730" stroke="__SECONDARY__"/>
    <path d="M0 670 Q 275 590 550 670 T 1100 670" stroke="__PRIMARY__"/>
    <path d="M0 610 Q 275 530 550 610 T 1100 610" stroke="__PRIMARY__"/>
  </g>
</svg>
""",
    "guilloche": """
<svg viewBox="0 0 1100 850" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="__PRIMARY__" stroke-width="0.8" opacity="0.07">
    <circle cx="550" cy="425" r="120"/>
    <circle cx="550" cy="425" r="170"/>
    <circle cx="550" cy="425" r="220"/>
    <circle cx="550" cy="425" r="270"/>
    <circle cx="550" cy="425" r="320"/>
  </g>
  <g fill="none" stroke="__SECONDARY__" stroke-width="0.8" opacity="0.06">
    <ellipse cx="550" cy="425" rx="360" ry="150"/>
    <ellipse cx="550" cy="425" rx="150" ry="360"/>
  </g>
</svg>
""",
    "corners": """
<svg viewBox="0 0 1100 850" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <g fill="none" stroke="__PRIMARY__" stroke-width="3" opacity="0.14">
    <path d="M60 160 Q60 60 160 60"/>
    <path d="M1040 160 Q1040 60 940 60"/>
    <path d="M60 690 Q60 790 160 790"/>
    <path d="M1040 690 Q1040 790 940 790"/>
  </g>
  <g fill="__SECONDARY__" opacity="0.10">
    <circle cx="60" cy="60" r="6"/>
    <circle cx="1040" cy="60" r="6"/>
    <circle cx="60" cy="790" r="6"/>
    <circle cx="1040" cy="790" r="6"/>
  </g>
</svg>
""",
}

