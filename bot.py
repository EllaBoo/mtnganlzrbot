#!/usr/bin/env python3
"""
MTNGanlzrBot — Standalone Meeting Analyzer
Audio/Video → Transcription → Expert Analysis
Direct ffmpeg + Deepgram + OpenAI (no external services)
"""
import asyncio
import logging
import os
import re
import json
import subprocess
import tempfile
import httpx
from openai import AsyncOpenAI

from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from telegram.constants import ChatAction, ParseMode

from pyrogram import Client as PyroClient

from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
)
logger = logging.getLogger("bot")

pyro_client = None
openai_client = None


async def on_startup(app: Application):
    global pyro_client, openai_client
    if config.API_ID and config.API_HASH:
        pyro_client = PyroClient(
            "bot_downloader",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            no_updates=True,
            in_memory=True,
        )
        await pyro_client.start()
        logger.info("Pyrogram started (large file support)")
    else:
        logger.warning("No API_ID/API_HASH — max 20MB files")
    if config.OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("OpenAI client ready")


async def on_shutdown(app: Application):
    global pyro_client
    if pyro_client:
        await pyro_client.stop()


async def download_file(file_id: str, dest: str, update: Update) -> bool:
    try:
        if pyro_client:
            await pyro_client.download_media(file_id, file_name=dest)
        else:
            f = await update.get_bot().get_file(file_id)
            await f.download_to_drive(dest)
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def extract_audio(input_path: str):
    output = input_path.rsplit(".", 1)[0] + "_audio.wav"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", output],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0 and os.path.exists(output):
            size_mb = os.path.getsize(output) / (1024 * 1024)
            logger.info(f"Audio extracted: {size_mb:.1f} MB")
            return output
        logger.error(f"ffmpeg error: {result.stderr[:500]}")
        return None
    except Exception as e:
        logger.error(f"ffmpeg failed: {e}")
        return None


async def transcribe_audio(audio_path: str, lang: str = "ru"):
    if not config.DEEPGRAM_API_KEY:
        logger.error("No DEEPGRAM_API_KEY!")
        return None
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "model": "nova-2",
        "language": lang if lang != "auto" else "ru",
        "smart_format": "true",
        "punctuate": "true",
        "paragraphs": "true",
    }
    try:
        file_size = os.path.getsize(audio_path)
        logger.info(f"Sending {file_size / 1024 / 1024:.1f} MB to Deepgram...")
        async with httpx.AsyncClient(timeout=600.0) as client:
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    url, params=params,
                    headers={
                        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
                        "Content-Type": "audio/wav",
                    },
                    content=f.read(),
                )
        if resp.status_code != 200:
            logger.error(f"Deepgram {resp.status_code}: {resp.text[:300]}")
            return None
        data = resp.json()
        channels = data.get("results", {}).get("channels", [])
        if not channels:
            return None
        alternatives = channels[0].get("alternatives", [])
        if not alternatives:
            return None
        paragraphs = alternatives[0].get("paragraphs", {})
        if paragraphs and paragraphs.get("paragraphs"):
            parts = []
            for p in paragraphs["paragraphs"]:
                for s in p.get("sentences", []):
                    parts.append(s.get("text", ""))
                parts.append("")
            text = "\n".join(parts).strip()
        else:
            text = alternatives[0].get("transcript", "")
        logger.info(f"Transcribed: {len(text)} chars, {len(text.split())} words")
        return text
    except Exception as e:
        logger.error(f"Deepgram error: {e}")
        return None


ANALYSIS_PROMPT = """Ты — экспертный аналитик. Проанализируй транскрипцию и дай структурированный анализ.

Определи область и адаптируй анализ.

Формат:

📋 КРАТКОЕ СОДЕРЖАНИЕ
(2-3 предложения)

📑 ОСНОВНЫЕ ТЕМЫ
(пронумерованный список)

📌 КЛЮЧЕВЫЕ РЕШЕНИЯ И ФАКТЫ
(только факты из записи)

✅ ACTION ITEMS
(задачи: что → кто → когда)

💡 РЕКОМЕНДАЦИИ
(экспертные рекомендации)

❓ ОТКРЫТЫЕ ВОПРОСЫ
(что осталось нерешённым)

Пиши на языке транскрипции. Будь конкретным."""


async def analyze_text(text: str):
    if not openai_client:
        return None
    max_chars = 100_000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...текст обрезан...]"
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT},
                {"role": "user", "content": f"Транскрипция:\n\n{text}"},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return None


async def process_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                          file_path: str):
    chat = update.effective_chat
    msg = await update.message.reply_text("⏳ Начинаю обработку...")
    audio_path = None
    try:
        await msg.edit_text("🎵 Извлекаю аудио...")
        await chat.send_action(ChatAction.TYPING)
        audio_path = await asyncio.get_event_loop().run_in_executor(
            None, extract_audio, file_path
        )
        if not audio_path:
            await msg.edit_text("❌ Не удалось извлечь аудио.")
            return

        await msg.edit_text("📝 Транскрибирую (Deepgram Nova-2)...")
        await chat.send_action(ChatAction.TYPING)
        lang = ctx.user_data.get("language", config.DEFAULT_LANG)
        text = await transcribe_audio(audio_path, lang)
        if not text or len(text) < 20:
            await msg.edit_text("🤔 Не удалось разобрать речь.")
            return

        word_count = len(text.split())
        await msg.edit_text(f"🧠 Анализирую ({word_count:,} слов)...")
        await chat.send_action(ChatAction.TYPING)
        analysis = await analyze_text(text)

        header = f"🧠 <b>Анализ завершён</b>\n📝 Слов: {word_count:,}\n"
        if analysis:
            full_msg = header + "\n" + analysis
            if len(full_msg) <= 4096:
                await msg.edit_text(full_msg, parse_mode=ParseMode.HTML)
            else:
                await msg.edit_text(header, parse_mode=ParseMode.HTML)
                for i in range(0, len(analysis), 4000):
                    await update.message.reply_text(analysis[i:i + 4000])
        else:
            await msg.edit_text(
                header + "\n⚠️ Анализ недоступен, транскрипция в файле ниже.",
                parse_mode=ParseMode.HTML
            )

        trans_file = tempfile.mktemp(suffix=".txt")
        with open(trans_file, "w", encoding="utf-8") as f:
            f.write(f"=== Транскрипция ({word_count} слов) ===\n\n{text}")
            if analysis:
                f.write(f"\n\n=== Анализ ===\n\n{analysis}")
        with open(trans_file, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename="analysis.txt"),
                caption=f"📄 Полный текст ({word_count:,} слов)"
            )
        os.unlink(trans_file)

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        await msg.edit_text(
            f"😅 Ошибка: <code>{str(e)[:300]}</code>",
            parse_mode=ParseMode.HTML
        )
    finally:
        for p in [file_path, audio_path]:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 <b>Meeting Analyzer Bot</b>\n\n"
        "Отправь мне:\n"
        "🎤 Голосовое сообщение\n"
        "🎵 Аудио файл\n"
        "🎬 Видео файл\n"
        "🔗 Ссылку на YouTube\n\n"
        "Я транскрибирую и сделаю экспертный анализ.\n"
        "Файлы до 2 GB.",
        parse_mode=ParseMode.HTML
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Как использовать:</b>\n\n"
        "1. Отправь аудио/видео/голосовое\n"
        "2. Deepgram транскрибирует\n"
        "3. GPT-4o анализирует\n"
        "4. Получаешь анализ + текст файлом\n\n"
        "Файлы до 2 GB через Pyrogram.",
        parse_mode=ParseMode.HTML
    )


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    if not voice:
        return
    ext = ".ogg" if update.message.voice else ".mp3"
    tmp = tempfile.mktemp(suffix=ext)
    if not await download_file(voice.file_id, tmp, update):
        await update.message.reply_text("❌ Не удалось скачать.")
        return
    await process_content(update, ctx, file_path=tmp)


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.video_note
    if not video:
        return
    tmp = tempfile.mktemp(suffix=".mp4")
    if not await download_file(video.file_id, tmp, update):
        await update.message.reply_text("❌ Не удалось скачать.")
        return
    await process_content(update, ctx, file_path=tmp)


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    mime = doc.mime_type or ""
    fname = (doc.file_name or "").lower()
    ok_mime = ("audio", "video", "ogg", "mp4", "mp3", "wav", "m4a",
               "webm", "mpeg", "flac", "aac", "opus")
    ok_ext = (".mp3", ".mp4", ".m4a", ".ogg", ".wav", ".webm", ".flac",
              ".aac", ".mov", ".avi", ".mkv", ".wma", ".opus", ".oga")
    if not (any(t in mime for t in ok_mime) or
            any(fname.endswith(e) for e in ok_ext)):
        await update.message.reply_text("🤔 Отправь аудио или видео файл.")
        return
    size_mb = (doc.file_size or 0) / (1024 * 1024)
    if size_mb > config.MAX_FILE_MB:
        await update.message.reply_text(f"📦 Макс. {config.MAX_FILE_MB} MB.")
        return
    logger.info(f"Downloading: {doc.file_name} ({size_mb:.1f} MB)")
    ext = os.path.splitext(doc.file_name or "file.mp4")[1] or ".mp4"
    tmp = tempfile.mktemp(suffix=ext)
    if not await download_file(doc.file_id, tmp, update):
        await update.message.reply_text("❌ Не удалось скачать.")
        return
    logger.info(f"Downloaded: {os.path.getsize(tmp) / 1024 / 1024:.1f} MB")
    await process_content(update, ctx, file_path=tmp)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    yt = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/\S+)', text)
    if yt:
        url = yt.group(1)
        msg = await update.message.reply_text("📥 Скачиваю с YouTube...")
        try:
            tmp = tempfile.mktemp(suffix=".m4a")
            r = subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "m4a", "-o", tmp, url],
                capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0 and os.path.exists(tmp):
                await msg.edit_text("✅ Скачано!")
                await process_content(update, ctx, file_path=tmp)
            else:
                await msg.edit_text(f"❌ Ошибка YouTube:\n<code>{r.stderr[:200]}</code>",
                                    parse_mode=ParseMode.HTML)
        except Exception as e:
            await msg.edit_text(f"❌ {str(e)[:200]}")
        return
    await update.message.reply_text(
        "🤔 Отправь аудио, видео, голосовое или ссылку на YouTube."
    )


async def error_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}", exc_info=ctx.error)


def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.post_init = on_startup
    app.post_shutdown = on_shutdown
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    logger.info("Bot started!")
    logger.info(f"  Pyrogram: {'yes' if config.API_ID else 'no'}")
    logger.info(f"  Deepgram: {'yes' if config.DEEPGRAM_API_KEY else 'NO!'}")
    logger.info(f"  OpenAI: {'yes' if config.OPENAI_API_KEY else 'NO!'}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
