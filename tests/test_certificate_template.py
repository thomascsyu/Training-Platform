from certificate_template import (
    CERTIFICATE_BACKGROUNDS,
    DEFAULT_BACKGROUND,
    compute_valid_until,
    create_certification_template,
    create_certification_template_source,
    is_certificate_expired,
    normalize_background,
    render_certification_template,
)


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
    assert "June 08, 2027" in html
    assert 'class="expired-stamp"' not in html


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
    assert "Valid Until: <strong>—</strong>" in html
    assert 'class="expired-stamp"' not in html


def test_compute_valid_until_adds_one_year():
    assert compute_valid_until("2026-06-08T12:00:00+00:00") == "2027-06-08T12:00:00+00:00"


def test_compute_valid_until_handles_leap_day():
    assert compute_valid_until("2024-02-29T00:00:00+00:00") == "2025-02-28T00:00:00+00:00"


def test_compute_valid_until_handles_missing_input():
    assert compute_valid_until(None) is None
    assert compute_valid_until("") is None


def test_is_certificate_expired():
    assert is_certificate_expired("2020-01-01T00:00:00+00:00") is True
    assert is_certificate_expired("2099-01-01T00:00:00+00:00") is False
    assert is_certificate_expired(None) is False


def test_create_certification_template_shows_expired_badge_past_validity():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "certificate_id": "ABCD1234",
        "issued_at": "2020-01-01T12:00:00+00:00",
    })

    assert "Valid Until: <strong>January 01, 2021</strong>" in html
    assert 'class="expired-stamp"' in html
    assert ">Expired<" in html


def test_certificate_backgrounds_has_five_options():
    assert len(CERTIFICATE_BACKGROUNDS) == 5
    assert DEFAULT_BACKGROUND in CERTIFICATE_BACKGROUNDS


def test_create_certification_template_renders_each_background_distinctly():
    rendered = {}
    for background in CERTIFICATE_BACKGROUNDS:
        html = create_certification_template({
            "course_title": "Advanced Security Training",
            "user_name": "Jane Doe",
            "score": 92,
            "certificate_id": "ABCD1234",
            "issued_at": "2026-06-08T12:00:00+00:00",
            "background": background,
        })
        assert "Jane Doe" in html
        assert "Advanced Security Training" in html
        rendered[background] = html

    # Each background produces visibly different markup.
    assert len(set(rendered.values())) == len(CERTIFICATE_BACKGROUNDS)


def test_create_certification_template_falls_back_to_default_for_invalid_background():
    html = create_certification_template({"background": "not-a-real-style"})
    default_html = create_certification_template({"background": DEFAULT_BACKGROUND})
    assert html == default_html


def test_create_certification_template_source_accepts_background():
    source = create_certification_template_source("#002FA7", "#0A0B10", "modern")
    assert "bg-corner" in source
    assert "{{user_name}}" in source


def test_create_source_and_render_template():
    source = create_certification_template_source("#002FA7", "#0A0B10")
    assert "{{user_name}}" in source
    assert "{{course_title}}" in source
    assert "{{score}}" in source

    rendered = render_certification_template(
        source,
        {
            "course_title": "Security Training",
            "user_name": "Jane Doe",
            "score": 92,
            "certificate_id": "ABCD1234",
            "issued_at": "2026-06-08T12:00:00+00:00",
        },
    )

    assert "{{user_name}}" not in rendered
    assert "Jane Doe" in rendered
    assert "Security Training" in rendered
    assert "92%" in rendered
    assert "June 08, 2027" in rendered


def test_there_are_five_selectable_backgrounds():
    assert len(CERTIFICATE_BACKGROUNDS) == 5
    keys = [bg["key"] for bg in CERTIFICATE_BACKGROUNDS]
    assert keys[0] == DEFAULT_BACKGROUND == "plain"
    assert set(keys) == {"plain", "geometric", "waves", "guilloche", "corners"}


def test_normalize_background_falls_back_to_default():
    assert normalize_background("waves") == "waves"
    assert normalize_background("nonsense") == "plain"
    assert normalize_background(None) == "plain"


def test_plain_background_has_no_artwork_layer():
    html = create_certification_template({"course_title": "X", "background": "plain"})
    assert 'class="artwork"' not in html


def test_selected_background_injects_artwork_svg():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "background": "waves",
        "primary_color": "#002FA7",
    })
    assert 'class="artwork"' in html
    assert "<svg" in html


def test_template_source_accepts_background():
    source = create_certification_template_source("#002FA7", "#0A0B10", "geometric")
    assert 'class="artwork"' in source
    assert "{{user_name}}" in source


def test_create_certification_template_defaults_to_english():
    html = create_certification_template({"course_title": "X", "user_name": "Jane"})
    assert '<html lang="en">' in html
    assert "Certificate of Completion" in html
    assert "Training Certificate" in html


def test_create_certification_template_renders_in_japanese():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "certificate_id": "ABCD1234",
        "issued_at": "2026-06-08T12:00:00+00:00",
        "language": "ja",
    })
    assert '<html lang="ja">' in html
    assert "修了証明書" in html
    assert "証明書番号: <strong>ABCD1234</strong>" in html
    assert "2026年06月08日" in html
    assert "Certificate of Completion" not in html


def test_create_certification_template_renders_in_korean():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "language": "ko",
    })
    assert '<html lang="ko">' in html
    assert "수료증" in html
    assert "점수 <strong>92%</strong>" in html


def test_create_certification_template_renders_in_simplified_chinese():
    html = create_certification_template({
        "course_title": "Security Training",
        "user_name": "Jane Doe",
        "score": 88,
        "language": "zh-CN",
    })
    assert '<html lang="zh-CN">' in html
    assert "结业证书" in html
    assert "证书编号" in html


def test_create_certification_template_unsupported_language_falls_back_to_english():
    html = create_certification_template({
        "course_title": "X",
        "user_name": "Jane",
        "language": "fr",
    })
    assert '<html lang="en">' in html
    assert "Certificate of Completion" in html


def test_create_certification_template_expired_badge_is_localized():
    html = create_certification_template({
        "course_title": "Advanced Security Training",
        "user_name": "Jane Doe",
        "score": 92,
        "issued_at": "2020-01-01T12:00:00+00:00",
        "language": "ja",
    })
    assert 'class="expired-stamp"' in html
    assert ">期限切れ<" in html


def test_create_certification_template_source_accepts_language():
    source = create_certification_template_source("#002FA7", "#0A0B10", "plain", "zh-TW")
    assert "結業證書" in source
    assert "{{user_name}}" in source
    assert "{{score}}" in source
