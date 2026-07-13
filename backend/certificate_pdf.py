import io

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from certificate_template import compute_valid_until, is_certificate_expired


def _hex(color: str, fallback: str = "#002FA7") -> HexColor:
    try:
        return HexColor(color)
    except Exception:
        return HexColor(fallback)


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


def generate_certificate_pdf(cert: dict) -> bytes:
    """Render a certificate PDF from a certificate document."""
    buffer = io.BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    primary = _hex(cert.get("primary_color", "#002FA7"))
    secondary = _hex(cert.get("secondary_color", "#0A0B10"))

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
