"""Helpers for AI translation prompts."""

from config import LANGUAGE_NAMES

HK_TRADITIONAL_CHINESE_CODE = "zh-TW"

HK_TRADITIONAL_CHINESE_GUIDANCE = (
    "Use Hong Kong Traditional Chinese (香港繁體中文). "
    "Do not use Taiwan (台灣) or Mainland (大陸) wording or characters. "
    "Prefer Hong Kong business, quality-management, and audit terminology. "
    "Examples: Audit → 審核 (not 稽核), Internal Audit → 內部審核, "
    "Management System → 管理系統, Quality → 品質."
)


def get_translation_target_name(lang_code: str) -> str:
    """Return the target language name used in AI translation prompts."""
    if lang_code == HK_TRADITIONAL_CHINESE_CODE:
        return "Hong Kong Traditional Chinese (香港繁體中文)"
    return LANGUAGE_NAMES.get(lang_code, lang_code)


def get_translation_source_name(lang_code: str) -> str:
    """Return the source language name used in AI translation prompts."""
    return LANGUAGE_NAMES.get(lang_code, lang_code)


def build_translation_system_prompt(
    source_lang: str,
    target_lang: str,
    *,
    role: str = "professional translator",
    content_label: str = "text",
    preserve_formatting: bool = False,
) -> str:
    """Build a system prompt for AI translation."""
    source_name = get_translation_source_name(source_lang)
    target_name = get_translation_target_name(target_lang)

    parts = [
        f"You are a {role}.",
        f"Translate the following {content_label} from {source_name} to {target_name}.",
    ]

    if target_lang == HK_TRADITIONAL_CHINESE_CODE:
        parts.append(HK_TRADITIONAL_CHINESE_GUIDANCE)

    if preserve_formatting:
        parts.append("Preserve formatting, line breaks, and paragraph breaks.")

    parts.append("Only output the translation, nothing else.")

    return " ".join(parts)
