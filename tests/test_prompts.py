"""
Tests for core/prompts.py

Covers:
- DOMAIN_TO_EXPERT mapping integrity
- DOMAIN_KEYWORDS structure
- Prompt templates have required placeholders
"""
import pytest

from core.prompts import (
    DOMAIN_TO_EXPERT,
    DOMAIN_KEYWORDS,
    EXPERTISE_DETECTION_PROMPT,
    ANALYSIS_PROMPT,
    DIAGNOSTICS_PROMPT,
    QUESTION_PROMPT,
    TOPIC_EXTRACTION_PROMPT,
)


class TestDomainToExpert:
    def test_has_general_fallback(self):
        assert "general" in DOMAIN_TO_EXPERT

    def test_all_values_are_nonempty_strings(self):
        for domain, expert in DOMAIN_TO_EXPERT.items():
            assert isinstance(expert, str), f"Domain '{domain}' expert is not a string"
            assert len(expert) > 0, f"Domain '{domain}' has empty expert role"

    def test_known_domains_present(self):
        expected = [
            "marketing", "sales", "development", "product",
            "hr", "finance", "strategy", "management",
            "legal", "medicine", "education", "design", "general",
        ]
        for domain in expected:
            assert domain in DOMAIN_TO_EXPERT, f"Domain '{domain}' missing from DOMAIN_TO_EXPERT"


class TestDomainKeywords:
    def test_all_domains_have_keywords(self):
        for domain, keywords in DOMAIN_KEYWORDS.items():
            assert isinstance(keywords, list), f"Domain '{domain}' keywords is not a list"
            assert len(keywords) > 0, f"Domain '{domain}' has no keywords"

    def test_all_keywords_are_lowercase(self):
        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw in keywords:
                assert kw == kw.lower(), (
                    f"Keyword '{kw}' in domain '{domain}' should be lowercase"
                )

    def test_keyword_domains_overlap_with_expert_domains(self):
        """Domains in DOMAIN_KEYWORDS should have entries in DOMAIN_TO_EXPERT."""
        for domain in DOMAIN_KEYWORDS:
            assert domain in DOMAIN_TO_EXPERT, (
                f"Domain '{domain}' in DOMAIN_KEYWORDS but not in DOMAIN_TO_EXPERT"
            )


class TestPromptTemplates:
    def test_expertise_detection_prompt_placeholders(self):
        assert "{transcript_preview}" in EXPERTISE_DETECTION_PROMPT
        assert "{language}" in EXPERTISE_DETECTION_PROMPT

    def test_analysis_prompt_placeholders(self):
        required = [
            "{transcript}", "{language}", "{domain}",
            "{domain_localized}", "{meeting_type}",
            "{expert_role}",
        ]
        for placeholder in required:
            assert placeholder in ANALYSIS_PROMPT, (
                f"Missing '{placeholder}' in ANALYSIS_PROMPT"
            )

    def test_diagnostics_prompt_placeholders(self):
        required = [
            "{transcript}", "{language}", "{domain}",
            "{meeting_type}", "{meeting_type_localized}",
            "{expert_role}",
        ]
        for placeholder in required:
            assert placeholder in DIAGNOSTICS_PROMPT, (
                f"Missing '{placeholder}' in DIAGNOSTICS_PROMPT"
            )

    def test_question_prompt_placeholders(self):
        required = [
            "{transcript}", "{analysis}", "{question}",
            "{language}", "{domain}", "{expert_role}",
        ]
        for placeholder in required:
            assert placeholder in QUESTION_PROMPT, (
                f"Missing '{placeholder}' in QUESTION_PROMPT"
            )

    def test_topic_extraction_prompt_placeholders(self):
        assert "{analysis}" in TOPIC_EXTRACTION_PROMPT
        assert "{language}" in TOPIC_EXTRACTION_PROMPT

    def test_prompts_are_nonempty(self):
        for name, prompt in [
            ("EXPERTISE_DETECTION_PROMPT", EXPERTISE_DETECTION_PROMPT),
            ("ANALYSIS_PROMPT", ANALYSIS_PROMPT),
            ("DIAGNOSTICS_PROMPT", DIAGNOSTICS_PROMPT),
            ("QUESTION_PROMPT", QUESTION_PROMPT),
            ("TOPIC_EXTRACTION_PROMPT", TOPIC_EXTRACTION_PROMPT),
        ]:
            assert len(prompt.strip()) > 50, f"{name} seems too short"
