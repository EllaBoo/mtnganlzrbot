"""
Digital Smarty v4.0 - Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")

# AI Services
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Paths
BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "fonts"
TMP_DIR = Path("/tmp")
SESSIONS_DIR = BASE_DIR / "sessions"

# Ensure directories exist
TMP_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)
