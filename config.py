import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    DRONOR_API: str = os.getenv("DRONOR_API_URL", "http://localhost:4000")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")
    MAX_FILE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "2000"))
    MAX_HOURS: int = int(os.getenv("MAX_DURATION_HOURS", "4"))
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANGUAGE", "auto")
    DEFAULT_FORMAT: str = os.getenv("DEFAULT_REPORT_FORMAT", "html_dark")

config = Config()
