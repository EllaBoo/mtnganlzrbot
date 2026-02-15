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
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o')
    WHISPER_MODEL: str = os.getenv('WHISPER_MODEL', 'whisper-1')
    
    # Deepgram
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    
    # Pyrogram (for large files >20MB)
    API_ID: Optional[int] = int(os.getenv('API_ID', '0')) if os.getenv('API_ID') else None
    API_HASH: Optional[str] = os.getenv('API_HASH')
    
    # Limits
    MAX_FILE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '2000'))
    
    # Aliases for backward compatibility
    @property
    def BOT_TOKEN(self) -> str:
        return self.TELEGRAM_TOKEN
    
    @property
    def MAX_FILE_SIZE_MB(self) -> int:
        return self.MAX_FILE_MB

# Singleton instance
config = Config()
