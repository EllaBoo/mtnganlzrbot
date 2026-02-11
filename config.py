"""Configuration for MTNGanlzrBot — Цифровой Умник"""
import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MAX_FILE_MB: int = 2000
    DEFAULT_LANG: str = "ru"

    # Supported languages: code -> (display_name, deepgram_code, flag)
    LANGUAGES: Dict = field(default_factory=lambda: {
        "ru": ("Русский", "ru", "🇷🇺"),
        "en": ("English", "en", "🇬🇧"),
        "kk": ("Қазақша", "kk", "🇰🇿"),
        "es": ("Español", "es", "🇪🇸"),
        "auto": ("Авто (язык аудио)", None, "🔄"),
    })


config = Config()
