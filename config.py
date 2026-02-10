"""Digital Smarty v5.0 — Configuration"""
import os

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

# APIs
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Limits
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "500"))
MAX_DURATION_HOURS = int(os.environ.get("MAX_DURATION_HOURS", "4"))

# Report defaults
DEFAULT_REPORT_FORMAT = os.environ.get("DEFAULT_REPORT_FORMAT", "html_dark")
DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "auto")

# OpenAI model
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
