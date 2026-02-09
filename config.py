"""
Конфигурация Digital Smarty / Цифровой Умник.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "sessions"
FONTS_DIR = BASE_DIR / "fonts"
TEMP_DIR = Path("/tmp/digital_smarty")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Telegram ───────────────────────────────────────────
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── AI ─────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── Transcription ──────────────────────────────────────
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

# ── Limits ─────────────────────────────────────────────
MAX_DURATION_SECONDS = int(os.getenv("MAX_DURATION_HOURS", "4")) * 3600
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_MB", "500")) * 1024 * 1024
MAX_TOPICS = 20
MAX_RECOMMENDATIONS = 15

# ── Defaults ───────────────────────────────────────────
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "ru")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ── Server ─────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
