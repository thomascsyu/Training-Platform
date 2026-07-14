"""Localized strings for the certificate module.

Certificates are generated in the language of the course they belong to
(``course.language``), so a learner in a Japanese-taught course receives a
Japanese-language certificate even though the LearnHub admin UI itself may be
in English. This module centralizes those translations so both the HTML
template (``certificate_template.py``) and the PDF renderer
(``certificate_pdf.py``) stay in sync.

Supported languages mirror ``config.SUPPORTED_LANGUAGES``: en, zh-TW, zh-CN,
ja, ko. Unknown/missing languages fall back to English.
"""

from datetime import datetime

DEFAULT_CERTIFICATE_LANGUAGE = "en"

CERTIFICATE_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "html_lang": "en",
        "overline": "Training Certificate",
        "title": "Certificate of Completion",
        "intro": "This certifies that",
        "completed": "has successfully completed",
        "score_line": "with a score of {score}%",
        "cert_id_label": "Certificate ID",
        "issued_label": "Issued",
        "valid_until_label": "Valid Until",
        "signature_label": "LearnHub",
        "expired": "Expired",
        "pdf_title": "CERTIFICATE OF COMPLETION",
        "pdf_intro": "This is to certify that",
        "pdf_score_line": "has successfully completed the course with a score of {score}%",
        "pdf_meta_line": "Certificate ID: {cert_id}  ·  Issued: {issued}  ·  Valid Until: {valid_until}",
    },
    "zh-CN": {
        "html_lang": "zh-CN",
        "overline": "培训证书",
        "title": "结业证书",
        "intro": "兹证明",
        "completed": "已成功完成",
        "score_line": "成绩为 {score}%",
        "cert_id_label": "证书编号",
        "issued_label": "颁发日期",
        "valid_until_label": "有效期至",
        "signature_label": "LearnHub",
        "expired": "已过期",
        "pdf_title": "结业证书",
        "pdf_intro": "兹证明",
        "pdf_score_line": "已成功完成课程，成绩为 {score}%",
        "pdf_meta_line": "证书编号：{cert_id}　·　颁发日期：{issued}　·　有效期至：{valid_until}",
    },
    "zh-TW": {
        "html_lang": "zh-TW",
        "overline": "培訓證書",
        "title": "結業證書",
        "intro": "茲證明",
        "completed": "已成功完成",
        "score_line": "成績為 {score}%",
        "cert_id_label": "證書編號",
        "issued_label": "頒發日期",
        "valid_until_label": "有效期至",
        "signature_label": "LearnHub",
        "expired": "已過期",
        "pdf_title": "結業證書",
        "pdf_intro": "茲證明",
        "pdf_score_line": "已成功完成課程，成績為 {score}%",
        "pdf_meta_line": "證書編號：{cert_id}　·　頒發日期：{issued}　·　有效期至：{valid_until}",
    },
    "ja": {
        "html_lang": "ja",
        "overline": "トレーニング証明書",
        "title": "修了証明書",
        "intro": "これは",
        "completed": "が以下のコースを修了したことを証明します",
        "score_line": "スコア {score}%",
        "cert_id_label": "証明書番号",
        "issued_label": "発行日",
        "valid_until_label": "有効期限",
        "signature_label": "LearnHub",
        "expired": "期限切れ",
        "pdf_title": "修了証明書",
        "pdf_intro": "これは、下記の通り証明します。",
        "pdf_score_line": "本コースをスコア{score}%で修了したことを証明します",
        "pdf_meta_line": "証明書番号: {cert_id}  ·  発行日: {issued}  ·  有効期限: {valid_until}",
    },
    "ko": {
        "html_lang": "ko",
        "overline": "교육 수료증",
        "title": "수료증",
        "intro": "이 증서는",
        "completed": "님이 다음 과정을 성공적으로 수료하였음을 증명합니다",
        "score_line": "점수 {score}%",
        "cert_id_label": "증서 번호",
        "issued_label": "발급일",
        "valid_until_label": "유효 기간",
        "signature_label": "LearnHub",
        "expired": "만료됨",
        "pdf_title": "수료증",
        "pdf_intro": "이는 다음과 같이 증명합니다.",
        "pdf_score_line": "점수 {score}%로 과정을 성공적으로 수료하였음을 증명합니다",
        "pdf_meta_line": "증서 번호: {cert_id}  ·  발급일: {issued}  ·  유효 기간: {valid_until}",
    },
}


def normalize_certificate_language(language: str | None) -> str:
    """Return a supported certificate language, falling back to English."""
    if isinstance(language, str) and language in CERTIFICATE_STRINGS:
        return language
    return DEFAULT_CERTIFICATE_LANGUAGE


def get_certificate_strings(language: str | None) -> dict[str, str]:
    """Return the localized string table for a certificate language."""
    return CERTIFICATE_STRINGS[normalize_certificate_language(language)]


def format_certificate_date(value: str | None, language: str | None = None) -> str:
    """Format a certificate date in a locale-appropriate way."""
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        import html as _html

        return _html.escape(str(value)[:10])

    lang = normalize_certificate_language(language)
    if lang in {"zh-CN", "zh-TW"}:
        return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日"
    if lang == "ja":
        return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日"
    if lang == "ko":
        return f"{dt.year}년 {dt.month:02d}월 {dt.day:02d}일"
    return dt.strftime("%B %d, %Y")
