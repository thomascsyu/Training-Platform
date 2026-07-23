import html
import re
from datetime import datetime

from certificate_i18n import (
    format_certificate_date,
    get_certificate_strings,
    normalize_certificate_language,
)

_PRIMARY_DEFAULT = "#002FA7"
_SECONDARY_DEFAULT = "#0A0B10"
_TEXT_MUTED = "#64748B"
_TEXT_PRIMARY = "#0A0B10"
_BACKGROUND = "#F4F5F7"

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_PLACEHOLDER_RE = re.compile(r"\{\{[a-z_]+\}\}")

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
# Maximum named certificate templates allowed on the platform (admin Templates tab).
MAX_CERTIFICATE_TEMPLATES = 5
DEFAULT_ORIENTATION = "landscape"
_ORIENTATIONS = {"landscape", "portrait"}
DEFAULT_BODY_TEXT = (
    "This certifies that {{recipient_name}} has successfully completed "
    "{{course_title}} on {{completion_date}}."
)


def normalize_background(value: str | None) -> str:
    """Return a valid background artwork key, falling back to the default."""
    if isinstance(value, str) and value.strip() in _BACKGROUND_KEYS:
        return value.strip()
    return DEFAULT_BACKGROUND


def normalize_orientation(value: str | None) -> str:
    """Return a valid orientation, falling back to landscape."""
    if isinstance(value, str) and value.strip().lower() in _ORIENTATIONS:
        return value.strip().lower()
    return DEFAULT_ORIENTATION


def page_size_css(orientation: str | None) -> tuple[str, str, str]:
    """Return (@page size, width, height) CSS values for the orientation."""
    if normalize_orientation(orientation) == "portrait":
        return "8.5in 11in", "8.5in", "11in"
    return "11in 8.5in landscape", "11in", "8.5in"


def _render_artwork(background: str, primary: str, secondary: str) -> str:
    """Return an SVG artwork layer (with colors already inlined) for a background."""
    key = normalize_background(background)
    svg = _ARTWORK_SVGS.get(key, "")
    if not svg:
        return ""
    svg = svg.replace("__PRIMARY__", primary).replace("__SECONDARY__", secondary)
    return f'<div class="artwork" aria-hidden="true">{svg}</div>'


def _background_image_layer(background_image_url: str | None) -> str:
    """Return an absolute-positioned background image layer when a URL is set."""
    if not background_image_url or not isinstance(background_image_url, str):
        return ""
    url = background_image_url.strip()
    if not url.startswith("/api/uploads/certificate-backgrounds/"):
        return ""
    safe_url = html.escape(url, quote=True)
    return (
        f'<div class="bg-image" aria-hidden="true" '
        f'style="background-image:url(\'{safe_url}\')"></div>'
    )


def _escape_body_text_preserving_placeholders(text: str) -> str:
    """Escape body text for HTML while leaving {{placeholders}} intact."""
    placeholders: list[str] = []

    def _stash(match: re.Match) -> str:
        placeholders.append(match.group(0))
        return f"__PH_{len(placeholders) - 1}__"

    stashed = _PLACEHOLDER_RE.sub(_stash, text)
    escaped = html.escape(stashed).replace("\n", "<br>\n")
    for index, token in enumerate(placeholders):
        escaped = escaped.replace(f"__PH_{index}__", token)
    return escaped


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


def _expired_badge_html(language: str | None) -> str:
    strings = get_certificate_strings(language)
    return f'<div class="expired-stamp">{html.escape(strings["expired"])}</div>'


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
    primary: str,
    secondary: str,
    background: str = DEFAULT_BACKGROUND,
    language: str | None = None,
    orientation: str = DEFAULT_ORIENTATION,
    background_image_url: str | None = None,
) -> str:
    # Insert the artwork (with real colors already inlined) before running the
    # placeholder colour substitution so the artwork colours are untouched.
    artwork = _render_artwork(background, primary, secondary)
    bg_image = _background_image_layer(background_image_url)
    page_size, width, height = page_size_css(orientation)
    strings = get_certificate_strings(language)
    score_prefix = strings["score_line"].split("{score}")[0]
    return (
        _CERTIFICATE_HTML.replace("__ARTWORK__", artwork)
        .replace("__BG_IMAGE__", bg_image)
        .replace("__PAGE_SIZE__", page_size)
        .replace("__CERT_WIDTH__", width)
        .replace("__CERT_HEIGHT__", height)
        .replace("__PRIMARY_COLOR__", primary)
        .replace("__SECONDARY_COLOR__", secondary)
        .replace("__HTML_LANG__", strings["html_lang"])
        .replace("__OVERLINE__", strings["overline"])
        .replace("__CERT_TITLE__", strings["title"])
        .replace("__INTRO__", strings["intro"])
        .replace("__COMPLETED_TEXT__", strings["completed"])
        .replace("__SCORE_PREFIX__", score_prefix)
        .replace("__CERT_ID_LABEL__", strings["cert_id_label"])
        .replace("__ISSUED_LABEL__", strings["issued_label"])
        .replace("__VALID_UNTIL_LABEL__", strings["valid_until_label"])
        .replace("__SIGNATURE_LABEL__", strings["signature_label"])
    )


def compose_builder_certificate_html(
    *,
    primary_color: str = _PRIMARY_DEFAULT,
    secondary_color: str = _SECONDARY_DEFAULT,
    background: str = DEFAULT_BACKGROUND,
    orientation: str = DEFAULT_ORIENTATION,
    background_image_url: str | None = None,
    body_text: str | None = None,
    language: str | None = None,
) -> str:
    """Compose certificate HTML from Certificate Builder fields.

    When ``body_text`` is provided, a simplified centered body layout is used.
    Otherwise the classic full certificate chrome is produced (with orientation
    and optional custom background image applied).
    """
    primary = _validate_color(primary_color, _PRIMARY_DEFAULT)
    secondary = _validate_color(secondary_color, _SECONDARY_DEFAULT)
    orientation = normalize_orientation(orientation)
    background = normalize_background(background)
    text = (body_text or "").strip() or DEFAULT_BODY_TEXT

    if body_text is not None:
        return _builder_body_html(
            primary=primary,
            secondary=secondary,
            background=background,
            orientation=orientation,
            background_image_url=background_image_url,
            body_text=text,
            language=language,
        )

    return (
        _base_certificate_html(
            primary,
            secondary,
            background,
            language,
            orientation,
            background_image_url,
        )
        .replace("__USER_NAME__", "{{user_name}}")
        .replace("__COURSE_TITLE__", "{{course_title}}")
        .replace("__SCORE__", "{{score}}")
        .replace("__CERTIFICATE_ID__", "{{certificate_id}}")
        .replace("__ISSUED_AT__", "{{issued_at}}")
        .replace("__VALID_UNTIL__", "{{valid_until}}")
    )


def _builder_body_html(
    *,
    primary: str,
    secondary: str,
    background: str,
    orientation: str,
    background_image_url: str | None,
    body_text: str,
    language: str | None,
) -> str:
    artwork = _render_artwork(background, primary, secondary)
    bg_image = _background_image_layer(background_image_url)
    page_size, width, height = page_size_css(orientation)
    strings = get_certificate_strings(language)
    safe_body = _escape_body_text_preserving_placeholders(body_text)
    return (
        _BUILDER_CERTIFICATE_HTML.replace("__ARTWORK__", artwork)
        .replace("__BG_IMAGE__", bg_image)
        .replace("__PAGE_SIZE__", page_size)
        .replace("__CERT_WIDTH__", width)
        .replace("__CERT_HEIGHT__", height)
        .replace("__PRIMARY_COLOR__", primary)
        .replace("__SECONDARY_COLOR__", secondary)
        .replace("__HTML_LANG__", strings["html_lang"])
        .replace("__OVERLINE__", strings["overline"])
        .replace("__CERT_TITLE__", strings["title"])
        .replace("__BODY_TEXT__", safe_body)
        .replace("__CERT_ID_LABEL__", strings["cert_id_label"])
        .replace("__ISSUED_LABEL__", strings["issued_label"])
        .replace("__VALID_UNTIL_LABEL__", strings["valid_until_label"])
        .replace("__SIGNATURE_LABEL__", strings["signature_label"])
        .replace("__CERTIFICATE_ID__", "{{certificate_id}}")
        .replace("__ISSUED_AT__", "{{issued_at}}")
        .replace("__VALID_UNTIL__", "{{valid_until}}")
    )


def create_certification_template_source(
    primary_color: str = _PRIMARY_DEFAULT,
    secondary_color: str = _SECONDARY_DEFAULT,
    background: str = DEFAULT_BACKGROUND,
    language: str | None = None,
    orientation: str = DEFAULT_ORIENTATION,
    background_image_url: str | None = None,
) -> str:
    """Return reusable certificate template HTML with user-data placeholders."""
    primary = _validate_color(primary_color, _PRIMARY_DEFAULT)
    secondary = _validate_color(secondary_color, _SECONDARY_DEFAULT)
    return (
        _base_certificate_html(
            primary,
            secondary,
            background,
            language,
            orientation,
            background_image_url,
        )
        .replace("__USER_NAME__", "{{user_name}}")
        .replace("__COURSE_TITLE__", "{{course_title}}")
        .replace("__SCORE__", "{{score}}")
        .replace("__CERTIFICATE_ID__", "{{certificate_id}}")
        .replace("__ISSUED_AT__", "{{issued_at}}")
        .replace("__VALID_UNTIL__", "{{valid_until}}")
    )


def render_certification_template(template_html: str, cert: dict) -> str:
    """Render certificate data into a reusable HTML certificate template."""
    language = cert.get("language")
    valid_until = cert.get("valid_until") or compute_valid_until(cert.get("issued_at"))
    expired = is_certificate_expired(valid_until)
    user_name = _safe(cert.get("user_name"), "Student")
    issued_display = format_certificate_date(cert.get("issued_at"), language)
    values = {
        "user_name": user_name,
        "recipient_name": user_name,
        "course_title": _safe(cert.get("course_title", cert.get("course", "Course"))),
        "score": str(_format_score(cert.get("score"))),
        "certificate_id": _safe(cert.get("certificate_id"), "—"),
        "issued_at": issued_display,
        "completion_date": issued_display,
        "valid_until": format_certificate_date(valid_until, language),
    }
    replacements = {
        "__USER_NAME__": values["user_name"],
        "__COURSE_TITLE__": values["course_title"],
        "__SCORE__": values["score"],
        "__CERTIFICATE_ID__": values["certificate_id"],
        "__ISSUED_AT__": values["issued_at"],
        "__VALID_UNTIL__": values["valid_until"],
        "__EXPIRED_BADGE__": _expired_badge_html(language) if expired else "",
        "{{user_name}}": values["user_name"],
        "{{recipient_name}}": values["recipient_name"],
        "{{course_title}}": values["course_title"],
        "{{score}}": values["score"],
        "{{certificate_id}}": values["certificate_id"],
        "{{issued_at}}": values["issued_at"],
        "{{completion_date}}": values["completion_date"],
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
    Renders in the certificate's ``language`` (course language at issuance time),
    falling back to English.
    """
    language = normalize_certificate_language(cert.get("language"))
    primary = _validate_color(cert.get("primary_color"), _PRIMARY_DEFAULT)
    secondary = _validate_color(cert.get("secondary_color"), _SECONDARY_DEFAULT)
    background = normalize_background(cert.get("background"))
    orientation = normalize_orientation(cert.get("orientation"))
    background_image_url = cert.get("background_image_url")
    body_text = cert.get("body_text")
    if body_text:
        source = compose_builder_certificate_html(
            primary_color=primary,
            secondary_color=secondary,
            background=background,
            orientation=orientation,
            background_image_url=background_image_url,
            body_text=body_text,
            language=language,
        )
        return render_certification_template(source, cert)
    return render_certification_template(
        _base_certificate_html(
            primary,
            secondary,
            background,
            language,
            orientation,
            background_image_url,
        ),
        cert,
    )


_CERTIFICATE_HTML = """<!DOCTYPE html>
<html lang="__HTML_LANG__">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__OVERLINE__ - __COURSE_TITLE__</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: __PAGE_SIZE__;
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
      width: __CERT_WIDTH__;
      height: __CERT_HEIGHT__;
      background: #FFFFFF;
      position: relative;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(10, 11, 16, 0.12);
    }
    .bg-image {
      position: absolute;
      inset: 0;
      z-index: 0;
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      pointer-events: none;
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
      z-index: 1;
    }
    .frame-outer {
      position: absolute;
      top: 0.5in;
      left: 0.5in;
      right: 0.5in;
      bottom: 0.5in;
      border: 4px solid __PRIMARY_COLOR__;
      z-index: 1;
    }
    .frame-inner {
      position: absolute;
      top: 0.65in;
      left: 0.65in;
      right: 0.65in;
      bottom: 0.65in;
      border: 1px solid __SECONDARY_COLOR__;
      z-index: 1;
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
      z-index: 2;
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
      z-index: 2;
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
    __BG_IMAGE__
    __ARTWORK__
    <div class="accent-bar"></div>
    <div class="frame-outer"></div>
    <div class="frame-inner"></div>
    <div class="content">
      <svg class="badge" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="8" r="6"></circle>
        <path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"></path>
      </svg>
      <div class="overline">__OVERLINE__</div>
      <h1>__CERT_TITLE__</h1>
      <div class="presented">__INTRO__</div>
      <div class="recipient">__USER_NAME__</div>
      <div class="presented">__COMPLETED_TEXT__</div>
      <div class="course">__COURSE_TITLE__</div>
      <div class="score">__SCORE_PREFIX__<strong>__SCORE__%</strong></div>
    </div>
    <div class="footer">
      <div class="signature">
        <div class="signature-line"></div>
        <div class="signature-label">__SIGNATURE_LABEL__</div>
      </div>
      <div class="meta">
        <div>__CERT_ID_LABEL__: <strong>__CERTIFICATE_ID__</strong></div>
        <div>__ISSUED_LABEL__: <strong>__ISSUED_AT__</strong></div>
        <div>__VALID_UNTIL_LABEL__: <strong>__VALID_UNTIL__</strong></div>
      </div>
    </div>
    __EXPIRED_BADGE__
  </div>
</body>
</html>
""".replace("__BACKGROUND__", _BACKGROUND).replace("__TEXT_PRIMARY__", _TEXT_PRIMARY).replace("__TEXT_MUTED__", _TEXT_MUTED)

_BUILDER_CERTIFICATE_HTML = """<!DOCTYPE html>
<html lang="__HTML_LANG__">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__OVERLINE__</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: __PAGE_SIZE__;
      margin: 0;
    }
    * { box-sizing: border-box; }
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
      width: __CERT_WIDTH__;
      height: __CERT_HEIGHT__;
      background: #FFFFFF;
      position: relative;
      overflow: hidden;
      box-shadow: 0 20px 60px rgba(10, 11, 16, 0.12);
    }
    .bg-image {
      position: absolute;
      inset: 0;
      z-index: 0;
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
      pointer-events: none;
    }
    .artwork {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
    }
    .artwork svg { width: 100%; height: 100%; display: block; }
    .accent-bar {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 14px;
      background: linear-gradient(90deg, __PRIMARY_COLOR__, __SECONDARY_COLOR__);
      z-index: 1;
    }
    .frame-outer {
      position: absolute;
      top: 0.5in; left: 0.5in; right: 0.5in; bottom: 0.5in;
      border: 4px solid __PRIMARY_COLOR__;
      z-index: 1;
    }
    .frame-inner {
      position: absolute;
      top: 0.65in; left: 0.65in; right: 0.65in; bottom: 0.65in;
      border: 1px solid __SECONDARY_COLOR__;
      z-index: 1;
    }
    .content {
      position: absolute;
      top: 0.85in; left: 0.85in; right: 0.85in; bottom: 1.6in;
      text-align: center;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 0 0.5in;
      z-index: 2;
    }
    .overline {
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: __TEXT_MUTED__;
      margin-bottom: 16px;
    }
    h1 {
      font-family: "Playfair Display", Georgia, serif;
      font-size: 42px;
      font-weight: 700;
      color: __SECONDARY_COLOR__;
      margin: 0 0 28px;
      letter-spacing: -0.02em;
      line-height: 1.1;
    }
    .body-text {
      font-size: 20px;
      line-height: 1.55;
      color: __TEXT_PRIMARY__;
      max-width: 8in;
    }
    .footer {
      position: absolute;
      left: 1.1in; right: 1.1in; bottom: 1.1in;
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 13px;
      color: __TEXT_MUTED__;
      z-index: 2;
    }
    .signature { text-align: center; }
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
    .meta { text-align: right; line-height: 1.6; }
    .meta strong { color: __TEXT_PRIMARY__; font-weight: 600; }
    .expired-stamp {
      position: absolute;
      top: 55%; left: 50%;
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
    __BG_IMAGE__
    __ARTWORK__
    <div class="accent-bar"></div>
    <div class="frame-outer"></div>
    <div class="frame-inner"></div>
    <div class="content">
      <div class="overline">__OVERLINE__</div>
      <h1>__CERT_TITLE__</h1>
      <div class="body-text">__BODY_TEXT__</div>
    </div>
    <div class="footer">
      <div class="signature">
        <div class="signature-line"></div>
        <div class="signature-label">__SIGNATURE_LABEL__</div>
      </div>
      <div class="meta">
        <div>__CERT_ID_LABEL__: <strong>__CERTIFICATE_ID__</strong></div>
        <div>__ISSUED_LABEL__: <strong>__ISSUED_AT__</strong></div>
        <div>__VALID_UNTIL_LABEL__: <strong>__VALID_UNTIL__</strong></div>
      </div>
    </div>
    __EXPIRED_BADGE__
  </div>
</body>
</html>
""".replace("__BACKGROUND__", _BACKGROUND).replace("__TEXT_PRIMARY__", _TEXT_PRIMARY).replace("__TEXT_MUTED__", _TEXT_MUTED)

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

