"""
Shared fixtures for Digital Smarty tests.
"""
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set dummy env vars before any project module is imported
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test_token")
os.environ.setdefault("TELEGRAM_API_ID", "12345")
os.environ.setdefault("TELEGRAM_API_HASH", "test_hash")
os.environ.setdefault("DEEPGRAM_API_KEY", "test_deepgram")
os.environ.setdefault("OPENAI_API_KEY", "test_openai")

import pytest
import tempfile


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def sample_analysis():
    """A realistic analysis dict with all sections populated."""
    return {
        "summary": "This was a productive marketing strategy meeting.",
        "key_points": [
            "Q2 budget was approved",
            "New campaign launches next month",
            "Social media strategy needs revision",
        ],
        "recommendations": [
            "Increase social media budget by 20%",
            "Hire a dedicated content creator",
        ],
        "statistics": {
            "word_count": 1500,
            "sentence_count": 85,
            "duration": "5:30",
        },
    }


@pytest.fixture
def sample_diagnostics():
    """A realistic diagnostics dict."""
    return {
        "diagnosis": "Productive discussion with clear outcomes",
        "confidence": 85,
        "indicators": [
            "Clear agenda followed",
            "All participants contributed",
            "Action items assigned",
        ],
    }


@pytest.fixture
def sample_transcript():
    """A realistic transcript string."""
    return (
        "[Speaker 0]: Good morning everyone. Let's discuss our Q2 marketing strategy.\n"
        "[Speaker 1]: I think we should focus on social media campaigns.\n"
        "[Speaker 0]: Great idea. What budget do we need?\n"
        "[Speaker 1]: Around 50 thousand dollars should be enough for the initial phase.\n"
        "[Speaker 0]: Let's approve that and move forward."
    )


@pytest.fixture
def sample_expertise():
    """A realistic expertise detection result."""
    return {
        "domain": "marketing",
        "domain_localized": "маркетинг",
        "meeting_type": "meeting",
        "meeting_type_localized": "совещание",
        "participants_level": "middle-management",
        "context": "internal meeting",
        "expert_role": "senior маркетолог с 15+ лет опыта",
    }
