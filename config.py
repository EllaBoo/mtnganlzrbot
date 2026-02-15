import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

load_dotenv()

@dataclass
class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN', '')
    WEBAPP_URL: str = os.getenv('WEBAPP_URL', '')
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    WHISPER_MODEL: str = os.getenv('WHISPER_MODEL', 'whisper-1')
    
    # Deepgram (alternative to Whisper)
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    
    # Pyrogram (for large files >20MB)
    API_ID: Optional[int] = int(os.getenv('API_ID', '0')) if os.getenv('API_ID') else None
    API_HASH: Optional[str] = os.getenv('API_HASH')
    
    # Dronor (optional)
    DRONOR_API_URL: str = os.getenv('DRONOR_API_URL', '')
    DRONOR_API_TOKEN: str = os.getenv('DRONOR_API_TOKEN', '')
    
    # Limits
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    MAX_TRANSCRIPT_LENGTH: int = int(os.getenv('MAX_TRANSCRIPT_LENGTH', '50000'))
    
    @property
    def pyrogram_available(self) -> bool:
        return bool(self.API_ID and self.API_HASH)

# Singleton instance
config = Config()

# Also export individual variables for backward compatibility
TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
OPENAI_API_KEY = config.OPENAI_API_KEY
OPENAI_MODEL = config.OPENAI_MODEL
WHISPER_MODEL = config.WHISPER_MODEL
DEEPGRAM_API_KEY = config.DEEPGRAM_API_KEY
API_ID = config.API_ID
API_HASH = config.API_HASH
MAX_FILE_SIZE_MB = config.MAX_FILE_SIZE_MB
MAX_TRANSCRIPT_LENGTH = config.MAX_TRANSCRIPT_LENGTH
