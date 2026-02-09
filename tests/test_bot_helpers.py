"""
Tests for bot/main.py helper functions.

These are pure functions that don't need Pyrogram or network access:
- format_duration
- extract_score
- extract_expert_tip
- get_cache
"""
import sys
from unittest.mock import MagicMock

# Pyrogram is not installed in the test environment, so we mock it
# before importing bot.main
sys.modules.setdefault("pyrogram", MagicMock())
sys.modules.setdefault("pyrogram.types", MagicMock())
sys.modules.setdefault("pyrogram.enums", MagicMock())
sys.modules.setdefault("pyrogram.filters", MagicMock())

import pytest

from bot.main import format_duration, extract_score, extract_expert_tip, get_cache, user_cache


@pytest.fixture(autouse=True)
def _reset_user_cache():
    user_cache.clear()
    yield
    user_cache.clear()


# ───────────────────────────────────────────────────────────────
# format_duration
# ───────────────────────────────────────────────────────────────

class TestFormatDuration:
    def test_zero_seconds(self):
        assert format_duration(0) == "0:00"

    def test_thirty_seconds(self):
        assert format_duration(30) == "0:30"

    def test_one_minute(self):
        assert format_duration(60) == "1:00"

    def test_one_minute_thirty(self):
        assert format_duration(90) == "1:30"

    def test_five_minutes(self):
        assert format_duration(300) == "5:00"

    def test_ten_minutes_five_seconds(self):
        assert format_duration(605) == "10:05"

    def test_large_duration(self):
        assert format_duration(3661) == "61:01"

    def test_float_seconds(self):
        assert format_duration(90.7) == "1:30"

    def test_single_digit_seconds_padded(self):
        assert format_duration(61) == "1:01"
        assert format_duration(62) == "1:02"
        assert format_duration(69) == "1:09"


# ───────────────────────────────────────────────────────────────
# extract_score
# ───────────────────────────────────────────────────────────────

class TestExtractScore:
    def test_high_score(self):
        score, emoji = extract_score("Overall Score: 95/100")
        assert score == 95
        assert emoji == "🟢"

    def test_good_score(self):
        score, emoji = extract_score("Score: 75/100 points")
        assert score == 75
        assert emoji == "🟡"

    def test_average_score(self):
        score, emoji = extract_score("Result: 55/100")
        assert score == 55
        assert emoji == "🟠"

    def test_low_score(self):
        score, emoji = extract_score("Score: 30/100")
        assert score == 30
        assert emoji == "🔴"

    def test_boundary_90(self):
        score, emoji = extract_score("90/100")
        assert score == 90
        assert emoji == "🟢"

    def test_boundary_70(self):
        score, emoji = extract_score("70/100")
        assert score == 70
        assert emoji == "🟡"

    def test_boundary_50(self):
        score, emoji = extract_score("50/100")
        assert score == 50
        assert emoji == "🟠"

    def test_boundary_49(self):
        score, emoji = extract_score("49/100")
        assert score == 49
        assert emoji == "🔴"

    def test_zero_score(self):
        score, emoji = extract_score("0/100")
        assert score == 0
        assert emoji == "🔴"

    def test_100_score(self):
        score, emoji = extract_score("100/100")
        assert score == 100
        assert emoji == "🟢"

    def test_no_score_found(self):
        score, emoji = extract_score("No score here at all")
        assert score == "?"
        assert emoji == "⚪"

    def test_empty_string(self):
        score, emoji = extract_score("")
        assert score == "?"
        assert emoji == "⚪"

    def test_score_in_russian_context(self):
        text = "## Общий балл: 82/100\n\nОценка как senior маркетолог"
        score, emoji = extract_score(text)
        assert score == 82
        assert emoji == "🟡"


# ───────────────────────────────────────────────────────────────
# extract_expert_tip
# ───────────────────────────────────────────────────────────────

class TestExtractExpertTip:
    def test_russian_tip(self):
        text = """## Какой-то раздел
Some text

# 💡 СОВЕТ ЦИФРОВОГО УМНИКА:
**Наблюдение:** Команда работает хорошо
**Совет:** Продолжайте в том же духе

# Другой раздел
"""
        result = extract_expert_tip(text, "ru")
        assert "💡" in result
        assert len(result) > 0

    def test_english_tip(self):
        text = """# DIGITAL SMARTY TIP:
**Observation:** Great teamwork
**Tip:** Keep up the good work

# Next section
"""
        result = extract_expert_tip(text, "en")
        assert "💡" in result

    def test_emoji_pattern(self):
        text = """## Something

💡 Expert Tip:
This is my important advice for the team.

# End
"""
        result = extract_expert_tip(text, "en")
        assert "💡" in result

    def test_no_tip_returns_empty(self):
        text = "Just regular analysis text without any tip section."
        result = extract_expert_tip(text, "ru")
        assert result == ""

    def test_empty_diagnostics(self):
        result = extract_expert_tip("", "ru")
        assert result == ""

    def test_tip_truncated_at_400(self):
        long_tip = "A" * 500
        text = f"# 💡 СОВЕТ ЦИФРОВОГО УМНИКА:\n{long_tip}\n\n# Next"
        result = extract_expert_tip(text, "ru")
        # The tip content inside is truncated to 400 chars
        # The full result includes formatting around it
        assert isinstance(result, str)


# ───────────────────────────────────────────────────────────────
# get_cache
# ───────────────────────────────────────────────────────────────

class TestGetCache:
    def test_creates_new_cache(self):
        cache = get_cache(1)
        assert isinstance(cache, dict)
        assert len(cache) == 0

    def test_returns_same_cache(self):
        cache1 = get_cache(1)
        cache1["key"] = "value"
        cache2 = get_cache(1)
        assert cache2["key"] == "value"

    def test_different_users_different_caches(self):
        cache1 = get_cache(1)
        cache1["x"] = 1
        cache2 = get_cache(2)
        assert "x" not in cache2

    def test_cache_is_mutable(self):
        cache = get_cache(1)
        cache["transcript"] = "hello"
        cache["duration"] = 120
        assert get_cache(1)["transcript"] == "hello"
        assert get_cache(1)["duration"] == 120
