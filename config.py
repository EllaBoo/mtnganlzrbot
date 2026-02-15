import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

# Telegram API (for pyrogram - large files support)
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-1')

# Deepgram (alternative transcription)
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')

# Dronor (optional)
DRONOR_API_URL = os.getenv('DRONOR_API_URL', '')
DRONOR_API_TOKEN = os.getenv('DRONOR_API_TOKEN', '')

# Limits
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
MAX_TRANSCRIPT_LENGTH = int(os.getenv('MAX_TRANSCRIPT_LENGTH', '50000'))
