import pytest
from bson import ObjectId
from fastapi import HTTPException

from certificate_template import (
    compose_builder_certificate_html,
    normalize_orientation,
    page_size_css,
    render_certification_template,
)
from certificate_utils import apply_template_to_certificate, resolve_certificate_template
from models import CertificateTemplateCreate


def test_normalize_orientation_defaults_to_landscape():
    assert normalize_orientation(None) == "landscape"
    assert normalize_orientation("portrait") == "portrait"
    assert normalize_orientation("LANDSCAPE") == "landscape"
    assert normalize_orientation("sideways") == "landscape"


def test_page_size_css_for_orientations():
    page, width, height = page_size_css("landscape")
    assert "landscape" in page
    assert width == "11in"
    assert height == "8.5in"

    page, width, height = page_size_css("portrait")
    assert page == "8.5in 11in"
    assert width == "8.5in"
    assert height == "11in"


def test_compose_builder_html_uses_custom_background_and_body():
    html = compose_builder_certificate_html(
        orientation="portrait",
        background_image_url="/api/uploads/certificate-backgrounds/abc.png",
        body_text="Hello {{recipient_name}} — {{course_title}}",
    )
    assert "8.5in 11in" in html
    assert "background-image:url('/api/uploads/certificate-backgrounds/abc.png')" in html
    assert "{{recipient_name}}" in html
    assert "{{course_title}}" in html


def test_compose_builder_html_escapes_body_text_xss():
    html = compose_builder_certificate_html(
        body_text="<script>alert(1)</script> {{recipient_name}}",
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "{{recipient_name}}" in html


def test_render_supports_builder_placeholder_aliases():
    source = compose_builder_certificate_html(
        body_text="{{recipient_name}} finished {{course_title}} on {{completion_date}}"
    )
    rendered = render_certification_template(
        source,
        {
            "user_name": "Jane Doe",
            "course_title": "Security Training",
            "issued_at": "2026-07-14T12:00:00+00:00",
            "certificate_id": "CERT-1",
            "score": 92,
        },
    )
    assert "Jane Doe" in rendered
    assert "Security Training" in rendered
    assert "July 14, 2026" in rendered
    assert "{{recipient_name}}" not in rendered


def test_apply_template_prefers_body_text_composition():
    template = {
        "_id": ObjectId(),
        "name": "Builder Template",
        "primary_color": "#002fa7",
        "secondary_color": "#0a0b10",
        "background": "plain",
        "orientation": "portrait",
        "background_image_url": "/api/uploads/certificate-backgrounds/bg.png",
        "body_text": "{{recipient_name}} completed {{course_title}}",
        "html": "<html>ignored</html>",
    }
    cert = {
        "user_name": "Alex",
        "course_title": "Ops 101",
        "score": 88,
        "certificate_id": "C-1",
        "issued_at": "2026-07-14T12:00:00+00:00",
    }
    apply_template_to_certificate(cert, template)
    assert cert["orientation"] == "portrait"
    assert cert["background_image_url"].endswith("bg.png")
    assert "Alex" in cert["template_html"]
    assert "Ops 101" in cert["template_html"]
    assert "8.5in 11in" in cert["template_html"]


@pytest.mark.asyncio
async def test_resolve_certificate_template_prefers_course_link():
    course_id = str(ObjectId())
    template_id = ObjectId()
    course_template = {
        "_id": template_id,
        "name": "Course Cert",
        "course_id": course_id,
        "is_default": False,
    }
    default_template = {
        "_id": ObjectId(),
        "name": "Default",
        "is_default": True,
    }

    class FakeCourses:
        async def find_one(self, query, projection=None):
            return {"_id": ObjectId(course_id), "certificate_template_id": str(template_id)}

    class FakeTemplates:
        async def find_one(self, query):
            if "_id" in query:
                return course_template
            if query.get("is_default"):
                return default_template
            return None

    class FakeDb:
        courses = FakeCourses()
        certificate_templates = FakeTemplates()

    resolved = await resolve_certificate_template(FakeDb(), course_id=course_id)
    assert resolved["name"] == "Course Cert"


@pytest.mark.asyncio
async def test_resolve_certificate_template_falls_back_to_default():
    class FakeCourses:
        async def find_one(self, query, projection=None):
            return {"_id": ObjectId(), "certificate_template_id": None}

    class FakeTemplates:
        async def find_one(self, query):
            if query.get("course_id"):
                return None
            if query.get("is_default"):
                return {"_id": ObjectId(), "name": "Global Default", "is_default": True}
            return None

    class FakeDb:
        courses = FakeCourses()
        certificate_templates = FakeTemplates()

    resolved = await resolve_certificate_template(FakeDb(), course_id=str(ObjectId()))
    assert resolved["name"] == "Global Default"


def test_certificate_template_create_rejects_bad_orientation():
    with pytest.raises(Exception):
        CertificateTemplateCreate(name="Bad", orientation="diagonal")
