import io

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor


def _hex(color: str, fallback: str = "#002FA7") -> HexColor:
    try:
        return HexColor(color)
    except Exception:
        return HexColor(fallback)


def generate_certificate_pdf(cert: dict) -> bytes:
    """Render a certificate PDF from a certificate document."""
    buffer = io.BytesIO()
    width, height = landscape(letter)
    c = canvas.Canvas(buffer, pagesize=(width, height))

    primary = _hex(cert.get("primary_color", "#002FA7"))
    secondary = _hex(cert.get("secondary_color", "#0A0B10"))

    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

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

    issued = cert.get("issued_at", "")[:10]
    cert_id = cert.get("certificate_id", "")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, margin + 0.6 * inch, f"Certificate ID: {cert_id}  ·  Issued: {issued}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
