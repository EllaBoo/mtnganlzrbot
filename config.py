import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
    API_HASH = os.getenv("TELEGRAM_API_HASH")
    STRING_SESSION = os.getenv("STRING_SESSION", "")
    
    # APIs
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Settings
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4GB
    CHUNK_SIZE = 20 * 1024 * 1024  # 20MB for Deepgram
    TEMP_DIR = "/tmp/smarty"
    
    # Languages
    LANGUAGES = {
        "ru": "🇷🇺 Русский",
        "en": "🇬🇧 English",
        "kk": "🇰🇿 Қазақша",
        "es": "🇪🇸 Español",
        "auto": "🌐 Язык оригинала"
    }