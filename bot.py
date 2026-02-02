import os
import asyncio
import tempfile
import httpx
from pyrogram import Client, filters
from openai import OpenAI

# Config from environment
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPGRAM_KEY = os.environ["DEEPGRAM_API_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

app = Client("meeting_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

async def transcribe_deepgram(file_path: str) -> str:
    """Transcribe audio using Deepgram API"""
    async with httpx.AsyncClient(timeout=600.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&diarize=true&language=ru",
                headers={"Authorization": f"Token {DEEPGRAM_KEY}"},
                content=f.read()
            )
        result = response.json()
        return result["results"]["channels"][0]["alternatives"][0]["transcript"]

def analyze_meeting(transcript: str) -> str:
    """Analyze transcript with GPT-4o"""
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": """Ты эксперт по анализу встреч. Создай структурированное саммари:

## 📋 Краткое содержание
(2-3 предложения о чём встреча)

## 👥 Участники и позиции
(кто что говорил/предлагал)

## ✅ Решения
(что решили)

## 📌 Action Items
(кто что должен сделать)

## ⚠️ Риски и открытые вопросы

## 💡 Инсайты
(что между строк, невысказанное)"""
        }, {
            "role": "user",
            "content": f"Вот транскрипт встречи:\n\n{transcript}"
        }],
        max_tokens=4000
    )
    return response.choices[0].message.content

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("👋 Привет! Отправь мне аудио или видео встречи, и я создам структурированное саммари.\n\n📎 Поддерживаю файлы до 4GB")

@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def media_handler(client, message):
    status = await message.reply("⏳ Скачиваю файл...")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download(tmp.name)
            tmp_path = tmp.name
        
        await status.edit_text("🎙 Транскрибирую (Deepgram)...")
        transcript = await transcribe_deepgram(tmp_path)
        
        await status.edit_text("🧠 Анализирую (GPT-4o)...")
        summary = analyze_meeting(transcript)
        
        await status.edit_text(f"## 📝 Саммари встречи\n\n{summary}")
        
        os.unlink(tmp_path)
        
    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {str(e)}")

print("🤖 Bot starting...")
app.run()
