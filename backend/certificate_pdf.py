import io

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from certificate_template import DEFAULT_BACKGROUND, compute_valid_until, is_certificate_expired


def _hex(color: str, fallback: str = "#002FA7") -> HexColor:
    try:
        return HexColor(color)
    except Exception:
        return HexColor(fallback)


def _draw_corner_mark(c, x: float, y: float, color: HexColor, size: float = 8) -> None:
    c.saveState()
    c.translate(x, y)
    c.rotate(45)
    c.setFillColor(color)
    c.rect(-size / 2, -size / 2, size, size, fill=1, stroke=0)
    c.restoreState()


def _draw_background(c, style: str, primary: HexColor, secondary: HexColor, width: float, height: float, margin: float) -> None:
    if style == "modern":
        c.saveState()
        c.setFillColor(secondary)
        c.setFillAlpha(0.08)
        p = c.beginPath()
        p.moveTo(0, height)
        p.lineTo(2 * inch, height)
        p.lineTo(0, height - 2 * inch)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(primary)
        p = c.beginPath()
        p.moveTo(width, 0)
        p.lineTo(width - 2 * inch, 0)
        p.lineTo(width, 2 * inch)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.restoreState()
        c.setStrokeColor(primary)
        c.setLineWidth(1)
        thin_margin = 0.4 * inch
        c.rect(thin_margin, thin_margin, width - 2 * thin_margin, height - 2 * thin_margin, fill=0, stroke=1)
        return

    if style == "elegant":
        c.setStrokeColor(primary)
        c.setLineWidth(2)
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)
        c.setStrokeColor(secondary)
        c.setLineWidth(1)
        c.setDash(4, 4)
        inner = margin + 14
        c.rect(inner, inner, width - 2 * inner, height - 2 * inner, fill=0, stroke=1)
        c.setDash()
        for x, y in [
            (margin, margin),
            (width - margin, margin),
            (margin, height - margin),
            (width - margin, height - margin),
        ]:
            _draw_corner_mark(c, x, y, primary)
        return

    if style == "minimal":
        c.setStrokeColor(primary)
        c.setLineWidth(2)
        c.line(margin + 0.4 * inch, margin + 0.9 * inch, width - margin - 0.4 * inch, margin + 0.9 * inch)
        c.setFillColor(secondary)
        c.rect(margin, height - margin - 0.1 * inch, 0.4 * inch, 0.08 * inch, fill=1, stroke=0)
        return

    if style == "bold":
        c.setStrokeColor(primary)
        c.setLineWidth(10)
        thick_margin = 0.55 * inch
        c.rect(thick_margin, thick_margin, width - 2 * thick_margin, height - 2 * thick_margin, fill=0, stroke=1)
        c.setFillColor(secondary)
        ribbon_width = 2.6 * inch
        c.rect(width / 2 - ribbon_width / 2, height - margin - 0.1 * inch, ribbon_width, 0.35 * inch, fill=1, stroke=0)
        return

    # classic (default)
    c.setStrokeColor(primary)
    c.setLineWidth(3)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin, fill=0, stroke=1)
    c.setStrokeColor(secondary)
    c.setLineWidth(1)
    c.rect(margin + 10, margin + 10, width - 2 * margin - 20, height - 2 * margin - 20, fill=0, stroke=1)


def generate_certificate_pdf(cert: dict) -> bytes:
    """Render a certificate PDF from a certificate document."""
    buffer = io.BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    primary = _hex(cert.get("primary_color", "#002FA7"))
    secondary = _hex(cert.get("secondary_color", "#0A0B10"))
    background_style = cert.get("background") or DEFAULT_BACKGROUND

    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    margin = 0.75 * inch
    _draw_background(c, background_style, primary, secondary, width, height, margin)

    c.setFillColor(secondary)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 1.4 * inch, "CERTIFICATE OF COMPLETION")

    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 28)
    course_title = cert.get("course_title", "Course")
    if len(course_title) > 48:
        course_title = course_title[:45] + "..."
    c.drawCentredString(width / 2, height - 2.1 * inch, course_title)

    c.setFillColor(HexColor("#64748B"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 2.7 * inch, "This is to certify that")

    c.setFillColor(primary)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 3.3 * inch, cert.get("user_name", "Student"))

    c.setFillColor(HexColor("#64748B"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(
        width / 2,
        height - 3.9 * inch,
        f"has successfully completed the course with a score of {cert.get('score', 0)}%",
    )

    issued_at = cert.get("issued_at", "")
    issued = issued_at[:10]
    valid_until = cert.get("valid_until") or compute_valid_until(issued_at)
    valid_until_display = valid_until[:10] if valid_until else "—"
    cert_id = cert.get("certificate_id", "")
    c.setFont("Helvetica", 10)
    c.drawCentredString(
        width / 2,
        margin + 0.6 * inch,
        f"Certificate ID: {cert_id}  ·  Issued: {issued}  ·  Valid Until: {valid_until_display}",
    )

    if is_certificate_expired(valid_until):
        c.saveState()
        c.setFillColor(HexColor("#DC2626"))
        c.setFillAlpha(0.35)
        c.setFont("Helvetica-Bold", 60)
        c.translate(width / 2, height / 2)
        c.rotate(25)
        c.drawCentredString(0, 0, "EXPIRED")
        c.restoreState()

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
