import io
import textwrap

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader

from certificate_i18n import format_certificate_date, get_certificate_strings
from certificate_template import (
    DEFAULT_ORIENTATION,
    compute_valid_until,
    is_certificate_expired,
    normalize_orientation,
)
from upload_utils import resolve_certificate_background_path

# Helvetica has no CJK glyphs, so non-Latin certificate languages fall back to
# ReportLab's built-in (non-embedded) CID fonts, which every PDF viewer can
# substitute with a locally installed CJK font.
_CID_FONTS = {
    "zh-CN": "STSong-Light",
    "zh-TW": "MSung-Light",
    "ja": "HeiseiKakuGo-W5",
    "ko": "HYSMyeongJo-Medium",
}
_registered_cid_fonts: set[str] = set()


def _fonts_for_language(language: str | None) -> tuple[str, str]:
    """Return (regular, bold) font names usable for the given certificate language."""
    cid_font = _CID_FONTS.get(language)
    if not cid_font:
        return "Helvetica", "Helvetica-Bold"
    if cid_font not in _registered_cid_fonts:
        pdfmetrics.registerFont(UnicodeCIDFont(cid_font))
        _registered_cid_fonts.add(cid_font)
    # These CID fonts ship a single weight; reuse it in place of a bold variant.
    return cid_font, cid_font


def _hex(color: str, fallback: str = "#002FA7") -> HexColor:
    try:
        return HexColor(color)
    except Exception:
        return HexColor(fallback)


def _page_size(orientation: str | None) -> tuple[float, float]:
    if normalize_orientation(orientation) == "portrait":
        return letter
    return landscape(letter)


def _draw_background_image(c, width, height, background_image_url: str | None) -> bool:
    path = resolve_certificate_background_path(background_image_url)
    if not path:
        return False
    try:
        image = ImageReader(str(path))
        c.drawImage(image, 0, 0, width=width, height=height, preserveAspectRatio=False, mask="auto")
        return True
    except Exception:
        return False


def _draw_artwork(c, width, height, background: str, primary, secondary) -> None:
    """Draw a subtle background artwork behind the certificate frame."""
    if background not in {"geometric", "waves", "guilloche", "corners"}:
        return

    c.saveState()
    if background == "geometric":
        c.setStrokeColor(primary)
        c.setStrokeAlpha(0.06)
        c.setLineWidth(0.6)
        step = 0.55 * inch
        x = -height
        while x < width:
            c.line(x, 0, x + height, height)
            x += step
        c.setFillColor(primary)
        c.setFillAlpha(0.05)
        c.setStrokeAlpha(0)
        p = c.beginPath()
        p.moveTo(0, height)
        p.lineTo(2.6 * inch, height)
        p.lineTo(0, height - 2.6 * inch)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        p2 = c.beginPath()
        p2.moveTo(width, 0)
        p2.lineTo(width - 2.6 * inch, 0)
        p2.lineTo(width, 2.6 * inch)
        p2.close()
        c.drawPath(p2, fill=1, stroke=0)
    elif background == "waves":
        c.setStrokeColor(primary)
        c.setStrokeAlpha(0.08)
        c.setLineWidth(1.4)
        amp = 0.35 * inch
        for i in range(3):
            base = height - (1.1 + i * 0.35) * inch
            c.bezier(
                0, base,
                width / 3, base + amp,
                2 * width / 3, base - amp,
                width, base,
            )
        for i in range(3):
            base = (1.1 + i * 0.35) * inch
            c.bezier(
                0, base,
                width / 3, base + amp,
                2 * width / 3, base - amp,
                width, base,
            )
    elif background == "guilloche":
        c.setStrokeColor(primary)
        c.setStrokeAlpha(0.07)
        c.setLineWidth(0.6)
        cx, cy = width / 2, height / 2
        for r in range(1, 6):
            c.circle(cx, cy, r * 0.55 * inch, stroke=1, fill=0)
        c.setStrokeColor(secondary)
        c.setStrokeAlpha(0.06)
        c.ellipse(cx - 3.2 * inch, cy - 1.4 * inch, cx + 3.2 * inch, cy + 1.4 * inch, stroke=1, fill=0)
        c.ellipse(cx - 1.4 * inch, cy - 3.2 * inch, cx + 1.4 * inch, cy + 3.2 * inch, stroke=1, fill=0)
    elif background == "corners":
        c.setStrokeColor(primary)
        c.setStrokeAlpha(0.16)
        c.setLineWidth(2.4)
        off = 0.9 * inch
        length = 0.7 * inch
        corners = [
            (off, height - off, 1, -1),
            (width - off, height - off, -1, -1),
            (off, off, 1, 1),
            (width - off, off, -1, 1),
        ]
        for x, y, sx, sy in corners:
            c.line(x, y, x + sx * length, y)
            c.line(x, y, x, y + sy * length)
    c.restoreState()


def _substitute_body_text(body_text: str, cert: dict, language: str | None) -> str:
    issued = format_certificate_date(cert.get("issued_at"), language)
    user_name = cert.get("user_name", "Student")
    replacements = {
        "{{recipient_name}}": user_name,
        "{{user_name}}": user_name,
        "{{course_title}}": cert.get("course_title", "Course"),
        "{{completion_date}}": issued,
        "{{issued_at}}": issued,
        "{{score}}": str(cert.get("score", 0)),
        "{{certificate_id}}": cert.get("certificate_id", ""),
    }
    rendered = body_text
    for token, value in replacements.items():
        rendered = rendered.replace(token, str(value))
    return rendered


def generate_certificate_pdf(cert: dict) -> bytes:
    """Render a certificate PDF from a certificate document, in the certificate's language."""
    buffer = io.BytesIO()
    orientation = cert.get("orientation") or DEFAULT_ORIENTATION
    width, height = _page_size(orientation)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    language = cert.get("language")
    strings = get_certificate_strings(language)
    regular_font, bold_font = _fonts_for_language(language)

    primary = _hex(cert.get("primary_color", "#002FA7"))
    secondary = _hex(cert.get("secondary_color", "#0A0B10"))

    drew_image = _draw_background_image(c, width, height, cert.get("background_image_url"))
    if not drew_image:
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, width, height, fill=1, stroke=0)
        _draw_artwork(c, width, height, cert.get("background", "plain"), primary, secondary)

    margin = 0.75 * inch
    c.setStrokeColor(primary)
    c.setLineWidth(3)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)

    c.setStrokeColor(secondary)
    c.setLineWidth(1)
    c.rect(margin + 10, margin + 10, width - 2 * margin - 20, height - 2 * margin - 20, fill=0, stroke=1)

    body_text = cert.get("body_text")
    if body_text:
        c.setFillColor(secondary)
        c.setFont(bold_font, 14)
        c.drawCentredString(width / 2, height - 1.4 * inch, strings["pdf_title"])

        rendered_body = _substitute_body_text(body_text, cert, language)
        c.setFillColor(HexColor("#0A0B10"))
        c.setFont(regular_font, 14)
        max_chars = 70 if normalize_orientation(orientation) == "landscape" else 52
        lines = []
        for paragraph in rendered_body.split("\n"):
            wrapped = textwrap.wrap(paragraph, width=max_chars) or [""]
            lines.extend(wrapped)
        start_y = height / 2 + (len(lines) * 10)
        for index, line in enumerate(lines[:18]):
            c.drawCentredString(width / 2, start_y - index * 20, line)
    else:
        c.setFillColor(secondary)
        c.setFont(bold_font, 14)
        c.drawCentredString(width / 2, height - 1.4 * inch, strings["pdf_title"])

        c.setFillColor(primary)
        c.setFont(bold_font, 28)
        course_title = cert.get("course_title", "Course")
        if len(course_title) > 48:
            course_title = course_title[:45] + "..."
        c.drawCentredString(width / 2, height - 2.1 * inch, course_title)

        c.setFillColor(HexColor("#64748B"))
        c.setFont(regular_font, 12)
        c.drawCentredString(width / 2, height - 2.7 * inch, strings["pdf_intro"])

        c.setFillColor(primary)
        c.setFont(bold_font, 22)
        c.drawCentredString(width / 2, height - 3.3 * inch, cert.get("user_name", "Student"))

        c.setFillColor(HexColor("#64748B"))
        c.setFont(regular_font, 12)
        c.drawCentredString(
            width / 2,
            height - 3.9 * inch,
            strings["pdf_score_line"].format(score=cert.get("score", 0)),
        )

    issued_at = cert.get("issued_at", "")
    issued = format_certificate_date(issued_at, language)
    valid_until = cert.get("valid_until") or compute_valid_until(issued_at)
    valid_until_display = format_certificate_date(valid_until, language)
    cert_id = cert.get("certificate_id", "")
    c.setFillColor(HexColor("#64748B"))
    c.setFont(regular_font, 10)
    c.drawCentredString(
        width / 2,
        margin + 0.6 * inch,
        strings["pdf_meta_line"].format(
            cert_id=cert_id, issued=issued, valid_until=valid_until_display
        ),
    )

    if is_certificate_expired(valid_until):
        c.saveState()
        c.setFillColor(HexColor("#DC2626"))
        c.setFillAlpha(0.35)
        c.setFont(bold_font, 60)
        c.translate(width / 2, height / 2)
        c.rotate(25)
        c.drawCentredString(0, 0, strings["expired"].upper())
        c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
