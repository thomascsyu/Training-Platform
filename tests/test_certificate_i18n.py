from certificate_i18n import (
    CERTIFICATE_STRINGS,
    DEFAULT_CERTIFICATE_LANGUAGE,
    format_certificate_date,
    get_certificate_strings,
    normalize_certificate_language,
)


def test_supported_languages_match_config_languages():
    assert set(CERTIFICATE_STRINGS.keys()) == {"en", "zh-TW", "zh-CN", "ja", "ko"}


def test_normalize_certificate_language_falls_back_to_english():
    assert normalize_certificate_language("ja") == "ja"
    assert normalize_certificate_language("fr") == DEFAULT_CERTIFICATE_LANGUAGE
    assert normalize_certificate_language(None) == DEFAULT_CERTIFICATE_LANGUAGE
    assert normalize_certificate_language("") == DEFAULT_CERTIFICATE_LANGUAGE


def test_get_certificate_strings_returns_full_table_for_each_language():
    required_keys = {
        "html_lang",
        "overline",
        "title",
        "intro",
        "completed",
        "score_line",
        "cert_id_label",
        "issued_label",
        "valid_until_label",
        "signature_label",
        "expired",
        "pdf_title",
        "pdf_intro",
        "pdf_score_line",
        "pdf_meta_line",
    }
    for lang in CERTIFICATE_STRINGS:
        strings = get_certificate_strings(lang)
        assert required_keys.issubset(strings.keys())
        assert "{score}" in strings["score_line"]
        assert "{score}" in strings["pdf_score_line"]
        assert "{cert_id}" in strings["pdf_meta_line"]
        assert "{issued}" in strings["pdf_meta_line"]
        assert "{valid_until}" in strings["pdf_meta_line"]


def test_get_certificate_strings_falls_back_for_unknown_language():
    assert get_certificate_strings("xx") == get_certificate_strings("en")


def test_format_certificate_date_localizes_by_language():
    value = "2026-07-14T00:00:00+00:00"
    assert format_certificate_date(value, "en") == "July 14, 2026"
    assert format_certificate_date(value, "zh-CN") == "2026年07月14日"
    assert format_certificate_date(value, "zh-TW") == "2026年07月14日"
    assert format_certificate_date(value, "ja") == "2026年07月14日"
    assert format_certificate_date(value, "ko") == "2026년 07월 14일"


def test_format_certificate_date_handles_missing_and_invalid_input():
    assert format_certificate_date(None) == "—"
    assert format_certificate_date("") == "—"
    assert format_certificate_date("not-a-date", "ja") == "not-a-date"
