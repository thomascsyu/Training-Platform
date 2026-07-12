from translation_utils import (
    HK_TRADITIONAL_CHINESE_CODE,
    HK_TRADITIONAL_CHINESE_GUIDANCE,
    build_translation_system_prompt,
    get_translation_target_name,
)


def test_get_translation_target_name_for_hk_traditional_chinese():
    assert get_translation_target_name("zh-TW") == "Hong Kong Traditional Chinese (香港繁體中文)"


def test_get_translation_target_name_for_other_languages():
    assert get_translation_target_name("en") == "English"
    assert get_translation_target_name("ja") == "日本語"


def test_build_translation_system_prompt_includes_hk_guidance_for_zh_tw():
    prompt = build_translation_system_prompt("en", HK_TRADITIONAL_CHINESE_CODE)

    assert "Hong Kong Traditional Chinese (香港繁體中文)" in prompt
    assert HK_TRADITIONAL_CHINESE_GUIDANCE in prompt
    assert "Audit → 審核" in prompt
    assert "Quality → 品質" in prompt


def test_build_translation_system_prompt_omits_hk_guidance_for_other_targets():
    prompt = build_translation_system_prompt("en", "ja")

    assert "Hong Kong Traditional Chinese" not in prompt
    assert "Audit → 審核" not in prompt


def test_build_translation_system_prompt_preserves_formatting_flag():
    prompt = build_translation_system_prompt(
        "en",
        "zh-CN",
        preserve_formatting=True,
    )

    assert "Preserve formatting, line breaks, and paragraph breaks." in prompt
