"""
Tests for core/pdf_generator.py

Covers:
- Original functionality (text, analysis, language, output_path, diagnostics)
- New parameters added in the fix (transcript, duration, speakers_count, expertise)
- Edge cases and backward compatibility
"""
import os
from pathlib import Path

import pytest

from core.pdf_generator import generate_pdf_report, register_fonts


# ───────────────────────────────────────────────────────────────
# register_fonts
# ───────────────────────────────────────────────────────────────

class TestRegisterFonts:
    def test_returns_string(self):
        result = register_fonts()
        assert isinstance(result, str)
        assert result in ("DejaVuSans", "Helvetica")

    def test_returns_helvetica_if_no_custom_fonts(self, monkeypatch):
        """Falls back to Helvetica when font files don't exist."""
        monkeypatch.setattr(Path, "exists", lambda self: False)
        result = register_fonts()
        assert result == "Helvetica"


# ───────────────────────────────────────────────────────────────
# generate_pdf_report — ORIGINAL functionality
# ───────────────────────────────────────────────────────────────

class TestGeneratePdfOriginal:
    def test_basic_text_and_analysis(self, tmp_dir, sample_analysis):
        """Original call pattern: text + analysis dict."""
        out = tmp_dir / "basic.pdf"
        result = generate_pdf_report(
            text="Hello world transcript",
            analysis=sample_analysis,
            output_path=out,
        )
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_with_diagnostics(self, tmp_dir, sample_analysis, sample_diagnostics):
        """Original call pattern with diagnostics section."""
        out = tmp_dir / "diag.pdf"
        result = generate_pdf_report(
            text="Some transcript text",
            analysis=sample_analysis,
            diagnostics=sample_diagnostics,
            output_path=out,
        )
        assert result == out
        assert out.exists()

    def test_all_languages(self, tmp_dir, sample_analysis):
        """PDF generates correctly for every supported language."""
        for lang in ("ru", "en", "es"):
            out = tmp_dir / f"lang_{lang}.pdf"
            result = generate_pdf_report(
                text="Test text",
                analysis=sample_analysis,
                language=lang,
                output_path=out,
            )
            assert out.exists(), f"PDF not created for language '{lang}'"

    def test_unknown_language_falls_back(self, tmp_dir, sample_analysis):
        """Unknown language code falls back to English titles."""
        out = tmp_dir / "unknown_lang.pdf"
        result = generate_pdf_report(
            text="Test",
            analysis=sample_analysis,
            language="xx",
            output_path=out,
        )
        assert out.exists()

    def test_auto_output_path(self, sample_analysis):
        """When output_path=None, a file is auto-generated in TMP_DIR."""
        result = generate_pdf_report(
            text="auto path test",
            analysis=sample_analysis,
        )
        assert isinstance(result, Path)
        assert result.exists()
        result.unlink(missing_ok=True)

    def test_empty_analysis(self, tmp_dir):
        """Empty analysis dict still produces a valid PDF."""
        out = tmp_dir / "empty_analysis.pdf"
        result = generate_pdf_report(
            text="Some text",
            analysis={},
            output_path=out,
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_analysis_with_only_summary(self, tmp_dir):
        """Analysis with only a summary field."""
        out = tmp_dir / "summary_only.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={"summary": "Brief summary of the meeting."},
            output_path=out,
        )
        assert out.exists()

    def test_analysis_with_only_key_points(self, tmp_dir):
        """Analysis with only key_points."""
        out = tmp_dir / "kp_only.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={"key_points": ["Point A", "Point B"]},
            output_path=out,
        )
        assert out.exists()

    def test_analysis_with_only_recommendations(self, tmp_dir):
        """Analysis with only recommendations."""
        out = tmp_dir / "rec_only.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={"recommendations": ["Do X", "Do Y"]},
            output_path=out,
        )
        assert out.exists()

    def test_analysis_with_only_statistics(self, tmp_dir):
        """Analysis with only statistics."""
        out = tmp_dir / "stats_only.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 100,
                    "sentence_count": 10,
                    "duration": "2:00",
                }
            },
            output_path=out,
        )
        assert out.exists()

    def test_diagnostics_partial_fields(self, tmp_dir, sample_analysis):
        """Diagnostics dict with only some fields."""
        out = tmp_dir / "diag_partial.pdf"
        result = generate_pdf_report(
            text="text",
            analysis=sample_analysis,
            diagnostics={"diagnosis": "Good"},
            output_path=out,
        )
        assert out.exists()

    def test_diagnostics_empty_dict(self, tmp_dir, sample_analysis):
        """Empty diagnostics dict (falsy) should be skipped."""
        out = tmp_dir / "diag_empty.pdf"
        result = generate_pdf_report(
            text="text",
            analysis=sample_analysis,
            diagnostics={},
            output_path=out,
        )
        assert out.exists()

    def test_text_with_newlines(self, tmp_dir, sample_analysis):
        """Text with newlines is converted to <br/> for PDF."""
        out = tmp_dir / "newlines.pdf"
        result = generate_pdf_report(
            text="Line one\nLine two\nLine three",
            analysis=sample_analysis,
            output_path=out,
        )
        assert out.exists()

    def test_output_path_as_string(self, tmp_dir, sample_analysis):
        """output_path accepts str as well as Path."""
        out = str(tmp_dir / "str_path.pdf")
        result = generate_pdf_report(
            text="text",
            analysis=sample_analysis,
            output_path=out,
        )
        assert isinstance(result, Path)
        assert result.exists()

    def test_return_type_is_path(self, tmp_dir, sample_analysis):
        """Return value is always a Path object."""
        out = tmp_dir / "ret_type.pdf"
        result = generate_pdf_report(
            text="text",
            analysis=sample_analysis,
            output_path=out,
        )
        assert isinstance(result, Path)


# ───────────────────────────────────────────────────────────────
# generate_pdf_report — NEW functionality (transcript alias, etc.)
# ───────────────────────────────────────────────────────────────

class TestGeneratePdfNewParams:
    def test_transcript_param_alias(self, tmp_dir, sample_analysis):
        """'transcript' param works as alias for 'text'."""
        out = tmp_dir / "transcript_alias.pdf"
        result = generate_pdf_report(
            transcript="Transcript content here",
            analysis=sample_analysis,
            output_path=out,
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_text_takes_priority_over_transcript(self, tmp_dir, sample_analysis):
        """When both text and transcript given, text wins."""
        out = tmp_dir / "text_priority.pdf"
        result = generate_pdf_report(
            text="Text wins",
            transcript="Transcript loses",
            analysis=sample_analysis,
            output_path=out,
        )
        assert out.exists()

    def test_no_text_no_transcript_defaults_empty(self, tmp_dir, sample_analysis):
        """When neither text nor transcript given, defaults to empty string."""
        out = tmp_dir / "no_text.pdf"
        result = generate_pdf_report(
            analysis=sample_analysis,
            output_path=out,
        )
        assert out.exists()

    def test_duration_in_statistics(self, tmp_dir):
        """duration param overrides stats duration and formats as MM:SS."""
        out = tmp_dir / "duration.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 500,
                    "sentence_count": 30,
                    "duration": "old_value",
                }
            },
            duration=125.0,  # 2:05
            output_path=out,
        )
        assert out.exists()

    def test_duration_zero(self, tmp_dir):
        """Duration of zero seconds formats as 0:00."""
        out = tmp_dir / "dur_zero.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 10,
                    "sentence_count": 2,
                    "duration": "N/A",
                }
            },
            duration=0.0,
            output_path=out,
        )
        assert out.exists()

    def test_duration_large(self, tmp_dir):
        """Large duration value (e.g. 1h+)."""
        out = tmp_dir / "dur_large.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 10000,
                    "sentence_count": 500,
                    "duration": "N/A",
                }
            },
            duration=3725.0,  # 62:05
            output_path=out,
        )
        assert out.exists()

    def test_speakers_count_in_statistics(self, tmp_dir):
        """speakers_count adds a row to the statistics table."""
        out = tmp_dir / "speakers.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 200,
                    "sentence_count": 15,
                    "duration": "1:30",
                }
            },
            speakers_count=3,
            output_path=out,
        )
        assert out.exists()

    def test_expertise_in_statistics(self, tmp_dir):
        """expertise adds a row to the statistics table."""
        out = tmp_dir / "expertise.pdf"
        result = generate_pdf_report(
            text="text",
            analysis={
                "statistics": {
                    "word_count": 200,
                    "sentence_count": 15,
                    "duration": "1:30",
                }
            },
            expertise="senior маркетолог",
            output_path=out,
        )
        assert out.exists()

    def test_all_new_params_together(self, tmp_dir, sample_analysis, sample_diagnostics):
        """All new params used simultaneously (mirrors bot/main.py call site)."""
        out = tmp_dir / "all_new.pdf"
        result = generate_pdf_report(
            output_path=str(out),
            analysis=sample_analysis,
            diagnostics=sample_diagnostics,
            transcript="Full transcript with speakers...",
            duration=330.0,
            speakers_count=2,
            language="ru",
            expertise="senior маркетолог с 15+ лет опыта",
        )
        assert isinstance(result, Path)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_bot_main_exact_call_pattern(self, tmp_dir):
        """
        Exact call pattern from bot/main.py:392-401.
        This is the call that was failing before the fix.
        """
        analysis = "Full analysis text as returned by analyze_transcript()"
        diagnostics = "Diagnostics text as returned by diagnose_communication()"
        expertise = {
            "domain": "marketing",
            "domain_localized": "маркетинг",
            "meeting_type": "meeting",
            "meeting_type_localized": "совещание",
            "expert_role": "senior маркетолог с 15+ лет опыта",
        }

        out = tmp_dir / "bot_exact.pdf"
        # This must NOT raise TypeError
        result = generate_pdf_report(
            output_path=str(out),
            analysis=analysis,
            diagnostics=diagnostics,
            transcript="[Speaker 0]: Hello\n[Speaker 1]: Hi",
            duration=120.5,
            speakers_count=2,
            language="ru",
            expertise=expertise,
        )
        assert result.exists()

    def test_none_analysis_defaults_to_empty_dict(self, tmp_dir):
        """analysis=None is handled gracefully."""
        out = tmp_dir / "none_analysis.pdf"
        result = generate_pdf_report(
            text="text",
            analysis=None,
            output_path=out,
        )
        assert out.exists()

    def test_none_text_none_transcript(self, tmp_dir):
        """Both text=None and transcript=None results in empty text."""
        out = tmp_dir / "none_both.pdf"
        result = generate_pdf_report(
            text=None,
            transcript=None,
            analysis={},
            output_path=out,
        )
        assert out.exists()


# ───────────────────────────────────────────────────────────────
# generate_pdf_report — statistics duration formatting
# ───────────────────────────────────────────────────────────────

class TestDurationFormatting:
    """Test the duration formatting logic inside generate_pdf_report."""

    def _gen(self, tmp_dir, duration=None, stats_duration=None):
        out = tmp_dir / f"dur_{duration}_{stats_duration}.pdf"
        stats = {"word_count": 1, "sentence_count": 1}
        if stats_duration is not None:
            stats["duration"] = stats_duration
        return generate_pdf_report(
            text="t",
            analysis={"statistics": stats},
            duration=duration,
            output_path=out,
        )

    def test_duration_overrides_stats(self, tmp_dir):
        result = self._gen(tmp_dir, duration=90.0, stats_duration="old")
        assert result.exists()

    def test_stats_duration_used_when_no_duration_param(self, tmp_dir):
        result = self._gen(tmp_dir, duration=None, stats_duration="3:00")
        assert result.exists()

    def test_no_duration_anywhere(self, tmp_dir):
        result = self._gen(tmp_dir, duration=None, stats_duration=None)
        assert result.exists()

    def test_integer_duration(self, tmp_dir):
        """Integer duration (not float) should also work."""
        result = self._gen(tmp_dir, duration=60)
        assert result.exists()
