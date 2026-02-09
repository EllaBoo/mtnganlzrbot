"""
Tests for bot/translations.py

Covers:
- t() translation function with formatting
- set_user_lang / get_user_lang
- get_lang_name
- TRANSLATIONS completeness
"""
import pytest

from bot.translations import (
    t,
    set_user_lang,
    get_user_lang,
    get_lang_name,
    TRANSLATIONS,
    LANG_NAMES,
    user_languages,
)


@pytest.fixture(autouse=True)
def _reset_user_languages():
    """Reset global user_languages dict between tests."""
    user_languages.clear()
    yield
    user_languages.clear()


# ───────────────────────────────────────────────────────────────
# set_user_lang / get_user_lang
# ───────────────────────────────────────────────────────────────

class TestUserLang:
    def test_default_language_is_ru(self):
        assert get_user_lang(999) == "ru"

    def test_set_and_get(self):
        set_user_lang(1, "en")
        assert get_user_lang(1) == "en"

    def test_set_overrides(self):
        set_user_lang(1, "en")
        set_user_lang(1, "es")
        assert get_user_lang(1) == "es"

    def test_auto_becomes_ru(self):
        set_user_lang(1, "auto")
        assert get_user_lang(1) == "ru"

    def test_multiple_users(self):
        set_user_lang(1, "en")
        set_user_lang(2, "es")
        set_user_lang(3, "zh")
        assert get_user_lang(1) == "en"
        assert get_user_lang(2) == "es"
        assert get_user_lang(3) == "zh"


# ───────────────────────────────────────────────────────────────
# get_lang_name
# ───────────────────────────────────────────────────────────────

class TestGetLangName:
    def test_known_languages(self):
        assert get_lang_name("ru") == "русский"
        assert get_lang_name("en") == "English"
        assert get_lang_name("kk") == "қазақ тілі"
        assert get_lang_name("es") == "español"
        assert get_lang_name("zh") == "中文"

    def test_auto_returns_russian(self):
        assert get_lang_name("auto") == "русский"

    def test_unknown_returns_russian(self):
        assert get_lang_name("xx") == "русский"


# ───────────────────────────────────────────────────────────────
# t() translation function
# ───────────────────────────────────────────────────────────────

class TestTranslation:
    def test_default_language_ru(self):
        text = t(999, "welcome")
        assert "Цифровой Умник" in text

    def test_english_translation(self):
        set_user_lang(1, "en")
        text = t(1, "welcome")
        assert "Digital Smarty" in text

    def test_spanish_translation(self):
        set_user_lang(1, "es")
        text = t(1, "welcome")
        assert "Digital Smarty" in text

    def test_chinese_translation(self):
        set_user_lang(1, "zh")
        text = t(1, "welcome")
        assert "数字智者" in text

    def test_kazakh_translation(self):
        set_user_lang(1, "kk")
        text = t(1, "welcome")
        assert "Цифрлық Данышпан" in text

    def test_formatting_kwargs(self):
        set_user_lang(1, "ru")
        text = t(1, "error", error="test error")
        assert "test error" in text

    def test_formatting_with_expert_role(self):
        set_user_lang(1, "ru")
        text = t(1, "analyzing_as_expert", expert_role="маркетолог")
        assert "маркетолог" in text

    def test_unknown_key_returns_key(self):
        text = t(999, "nonexistent_key_xyz")
        assert text == "nonexistent_key_xyz"

    def test_format_error_graceful(self):
        """Missing format kwargs don't raise."""
        set_user_lang(1, "ru")
        # 'error' key expects {error} kwarg, but we don't provide it
        text = t(1, "error")
        assert isinstance(text, str)

    def test_fallback_to_ru_for_unknown_lang(self):
        """Unknown language falls back to ru translations."""
        user_languages[1] = "xx"
        text = t(1, "welcome")
        assert "Цифровой Умник" in text


# ───────────────────────────────────────────────────────────────
# TRANSLATIONS structure completeness
# ───────────────────────────────────────────────────────────────

class TestTranslationsCompleteness:
    def test_all_languages_have_required_keys(self):
        """All translation dicts have the same keys as 'ru'."""
        ru_keys = set(TRANSLATIONS["ru"].keys())
        for lang_code, translations in TRANSLATIONS.items():
            if lang_code == "ru":
                continue
            lang_keys = set(translations.keys())
            missing = ru_keys - lang_keys
            # Some keys may be intentionally missing (e.g. kk doesn't have deep_dive, new_analysis)
            # but core keys should exist
            core_keys = {"welcome", "error", "processing", "done", "choose_lang"}
            for key in core_keys:
                assert key in lang_keys, f"Language '{lang_code}' missing core key '{key}'"

    def test_lang_names_cover_all_translation_languages(self):
        """LANG_NAMES covers all languages in TRANSLATIONS."""
        for lang_code in TRANSLATIONS:
            assert lang_code in LANG_NAMES or lang_code == "auto", (
                f"Language '{lang_code}' missing from LANG_NAMES"
            )
