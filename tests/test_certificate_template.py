from certificate_template import create_certification_template


def test_create_certification_template_returns_styled_html():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "certificate_id": "ABCD1234",
        "issued_at": "2026-06-08T12:00:00+00:00",
        "primary_color": "#002FA7",
        "secondary_color": "#0A0B10",
    })

    assert isinstance(html, str)
    assert html.startswith("<!DOCTYPE html")
    assert "Advanced Security Training" in html
    assert "Jane Doe" in html
    assert "92%" in html
    assert "ABCD1234" in html
    assert "June 08, 2026" in html
    assert "Training Certificate" in html
    assert "Certificate of Completion" in html
    assert "#002fa7" in html
    assert "#0a0b10" in html


def test_create_certification_template_uses_defaults_and_escapes_input():
    html = create_certification_template({
        "course_title": "<script>alert('xss')</script>",
        "user_name": "Student <b>Name</b>",
        "score": "88",
        "primary_color": "not-a-color",
    })

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>" not in html
    assert "Student Name" not in html
    assert "Student &lt;b&gt;Name&lt;/b&gt;" in html
    assert "88%" in html
    assert "#002fa7" in html
    assert "#0a0b10" in html


def test_create_certification_template_handles_missing_fields():
    html = create_certification_template({})

    assert "Student" in html
    assert "Course" in html
    assert "0%" in html
    assert "Certificate ID: <strong>—</strong>" in html
    assert "Issued: <strong>—</strong>" in html
