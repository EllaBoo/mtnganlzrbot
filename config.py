import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'whisper-1')

# Dronor (optional)
DRONOR_API_URL = os.getenv('DRONOR_API_URL', '')
DRONOR_API_TOKEN = os.getenv('DRONOR_API_TOKEN', '')

# Limits
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
MAX_TRANSCRIPT_LENGTH = int(os.getenv('MAX_TRANSCRIPT_LENGTH', '50000'))
