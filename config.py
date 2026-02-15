import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Telegram Bot (reads TELEGRAM_BOT_TOKEN from Railway)
    TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    # Telegram API for pyrogram (reads TELEGRAM_API_ID, TELEGRAM_API_HASH)
    API_ID: Optional[int] = int(os.getenv('TELEGRAM_API_ID', '0')) if os.getenv('TELEGRAM_API_ID') else None
    API_HASH: Optional[str] = os.getenv('TELEGRAM_API_HASH')
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # Deepgram
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    
    # File limits
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
    
    # Supported formats
    SUPPORTED_AUDIO: tuple = ('.mp3', '.m4a', '.wav', '.ogg', '.flac', '.aac', '.wma')
    SUPPORTED_VIDEO: tuple = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    
    @property
    def BOT_TOKEN(self) -> str:
        """Alias for TELEGRAM_TOKEN"""
        return self.TELEGRAM_TOKEN
    
    @property
    def MAX_FILE_MB(self) -> int:
        """Alias for MAX_FILE_SIZE_MB"""
        return self.MAX_FILE_SIZE_MB
    
    @property
    def PYROGRAM_ENABLED(self) -> bool:
        """Check if pyrogram can be used"""
        return bool(self.API_ID and self.API_HASH)

# Singleton instance
config = Config()
