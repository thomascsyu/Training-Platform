from certificate_pdf import generate_certificate_pdf
from certificate_template import CERTIFICATE_BACKGROUNDS


def test_generate_certificate_pdf_returns_bytes():
    pdf = generate_certificate_pdf({
        "course_title": "Intro to Python",
        "user_name": "Jane Doe",
        "score": 92,
        "certificate_id": "ABCD1234",
        "issued_at": "2026-06-08T12:00:00+00:00",
        "primary_color": "#002FA7",
        "secondary_color": "#0A0B10",
    })
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"


def test_generate_certificate_pdf_renders_every_background():
    for background in CERTIFICATE_BACKGROUNDS:
        pdf = generate_certificate_pdf({
            "course_title": "Intro to Python",
            "user_name": "Jane Doe",
            "score": 92,
            "certificate_id": "ABCD1234",
            "issued_at": "2026-06-08T12:00:00+00:00",
            "primary_color": "#002FA7",
            "secondary_color": "#0A0B10",
            "background": background,
        })
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"


def test_generate_certificate_pdf_renders_when_expired():
    pdf = generate_certificate_pdf({
        "course_title": "Intro to Python",
        "user_name": "Jane Doe",
        "score": 92,
        "certificate_id": "ABCD1234",
        "issued_at": "2020-01-01T12:00:00+00:00",
        "primary_color": "#002FA7",
        "secondary_color": "#0A0B10",
    })
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"
