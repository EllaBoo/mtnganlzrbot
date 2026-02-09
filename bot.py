#!/usr/bin/env python3
"""
🧠 Digital Smarty v5.0 — Цифровой Умник
Telegram Bot + Mini App Hybrid
Built on Dronor Expert Architecture
"""
import asyncio
import logging
import os
import json
import tempfile
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, InputFile
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ChatAction, ParseMode

from config import config
from dronor_client import DronorClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("smarty_bot")

dronor = DronorClient(config.DRONOR_API)

# ========== CHARACTER: Цифровой Умник ==========
SMARTY = {
    "welcome": (
        "🧠 <b>Привет! Я Цифровой Умник</b>\n\n"
        "Кидай мне любой контент — я разберу его как эксперт:\n\n"
        "🎤 <b>Голосовые и аудио</b> — записи встреч, подкасты\n"
        "🎬 <b>Видео</b> — лекции, вебинары, созвоны\n"
        "🔗 <b>Ссылки</b> — YouTube, Google Drive, Dropbox\n\n"
        "Я сам определю тему и стану экспертом в ней 🎯\n"
        "Бизнес, маркетинг, медицина, право — что угодно!\n\n"
        "💡 <i>Попробуй: отправь ссылку на YouTube видео</i>"
    ),
    "processing_stages": [
        "🔍 Определяю источник...",
        "🎵 Извлекаю аудио...",
        "📝 Транскрибирую...",
        "🧩 Анализирую темы...",
        "🧠 Погружаюсь в экспертизу...",
        "📊 Формирую отчёт..."
    ],
    "done": "🎯 Готово! Вот что я нашёл:",
    "error": "😅 Упс, что-то пошло не так. Попробуй ещё раз!",
}

# ========== KEYBOARDS ==========
def main_keyboard():
    buttons = []
    if config.WEBAPP_URL:
        buttons.append([InlineKeyboardButton(
            "🚀 Открыть Mini App", web_app=WebAppInfo(url=config.WEBAPP_URL)
        )])
    buttons.extend([
        [
            InlineKeyboardButton("📋 Мои отчёты", callback_data="my_reports"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
        ],
        [InlineKeyboardButton("❓ Как использовать", callback_data="help")]
    ])
    return InlineKeyboardMarkup(buttons)

def format_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 PDF", callback_data="fmt_pdf"),
            InlineKeyboardButton("🌙 HTML Dark", callback_data="fmt_html_dark"),
        ],
        [
            InlineKeyboardButton("☀️ HTML Light", callback_data="fmt_html_light"),
            InlineKeyboardButton("📝 TXT", callback_data="fmt_txt"),
        ],
        [InlineKeyboardButton("🔧 JSON (API)", callback_data="fmt_json")]
    ])

def settings_keyboard(user_data: dict):
    lang = user_data.get("language", "auto")
    fmt = user_data.get("format", "html_dark")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🌐 Язык: {lang}", callback_data="set_language")],
        [InlineKeyboardButton(f"📊 Формат: {fmt}", callback_data="set_format")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")]
    ])

# ========== HANDLERS ==========
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        SMARTY["welcome"], parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard()
    )

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>Как использовать Цифрового Умника:</b>\n\n"
        "1️⃣ Отправь <b>голосовое/аудио/видео</b> сообщение\n"
        "2️⃣ Или кинь <b>ссылку</b> на YouTube, Google Drive\n"
        "3️⃣ Или открой <b>Mini App</b> для записи прямо в боте\n\n"
        "Я определю тему и дам экспертный анализ:\n"
        "📌 Факты из записи\n"
        "💡 Рекомендации эксперта\n"
        "📊 SWOT-анализ\n"
        "✅ Action Items\n\n"
        "Умник адаптируется к ЛЮБОЙ области 🎯"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def process_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE, 
                         url: str = None, file_path: str = None):
    """Main processing pipeline — calls Dronor experts step by step"""
    user_id = str(update.effective_user.id)
    msg = await update.message.reply_text(
        SMARTY["processing_stages"][0], parse_mode=ParseMode.HTML
    )
    
    try:
        # Stage 1: URL Resolve
        if url:
            await msg.edit_text(SMARTY["processing_stages"][0])
            resolved = dronor.resolve_url(url)
            result = resolved.get("result", {})
            source_type = result.get("source_type", "unknown") if isinstance(result, dict) else "unknown"
        
        # Stage 2: Audio Extract
        await msg.edit_text(SMARTY["processing_stages"][1])
        await update.message.chat.send_action(ChatAction.TYPING)
        audio = dronor.extract_audio(url=url or "", file_path=file_path or "", source_type=source_type if url else "telegram")
        audio_result = audio.get("result", {})
        audio_path = audio_result.get("audio_path", "") if isinstance(audio_result, dict) else ""
        
        if not audio_path:
            await msg.edit_text("❌ Не удалось извлечь аудио. Проверь ссылку или файл.")
            return
        
        # Stage 3: Transcribe
        await msg.edit_text(SMARTY["processing_stages"][2])
        lang = ctx.user_data.get("language", "auto")
        transcription = dronor.transcribe(audio_path, lang)
        trans_result = transcription.get("result", {})
        text = trans_result.get("transcription", "") if isinstance(trans_result, dict) else str(trans_result)
        
        if not text or len(text) < 20:
            await msg.edit_text("🤔 Не смог разобрать речь. Возможно, качество записи низкое.")
            return
        
        # Stage 4: Topic Extraction
        await msg.edit_text(SMARTY["processing_stages"][3])
        segments = json.dumps(trans_result.get("segments", []), ensure_ascii=False) if isinstance(trans_result, dict) else ""
        topics = dronor.extract_topics(text, segments)
        topic_json = json.dumps(topics.get("result", {}), ensure_ascii=False, default=str)
        
        # Stage 5: Expert Analysis
        await msg.edit_text(SMARTY["processing_stages"][4])
        expert = dronor.analyze_expert(text, topic_json)
        expert_json = json.dumps(expert.get("result", {}), ensure_ascii=False, default=str)
        
        # Stage 6: Report Generation
        await msg.edit_text(SMARTY["processing_stages"][5])
        fmt = ctx.user_data.get("format", config.DEFAULT_FORMAT)
        report = dronor.generate_report(text, topic_json, expert_json, fmt)
        report_result = report.get("result", {})
        
        # Send quick summary
        topic_data = topics.get("result", {})
        summary = ""
        if isinstance(topic_data, dict):
            domain = topic_data.get("domain", "general")
            meeting_type = topic_data.get("meeting_type", "")
            exec_summary = topic_data.get("executive_summary", "")
            topics_list = topic_data.get("topics", [])
            
            summary = f"🧠 <b>Цифровой Умник — {domain.upper()}</b>\n"
            if meeting_type:
                summary += f"📋 Тип: {meeting_type}\n"
            summary += f"\n{exec_summary}\n"
            
            if topics_list and isinstance(topics_list, list):
                summary += "\n<b>📑 Темы:</b>\n"
                for i, t in enumerate(topics_list[:5], 1):
                    name = t.get("name", t) if isinstance(t, dict) else str(t)
                    summary += f"  {i}. {name}\n"
        
        if not summary:
            summary = SMARTY["done"]
        
        await msg.edit_text(summary, parse_mode=ParseMode.HTML)
        
        # Send report file
        if isinstance(report_result, dict) and report_result.get("file_path"):
            fpath = report_result["file_path"]
            if os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    await update.message.reply_document(
                        InputFile(f, filename=os.path.basename(fpath)),
                        caption="📊 Полный отчёт Цифрового Умника"
                    )
        
        # Ask for other formats
        await update.message.reply_text(
            "📥 Хочешь отчёт в другом формате?",
            reply_markup=format_keyboard()
        )
        
        # Save context
        dronor.save_context(user_id, json.dumps({
            "topics": topic_json[:500],
            "domain": topic_data.get("domain", "") if isinstance(topic_data, dict) else "",
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        await msg.edit_text(f"{SMARTY['error']}\n\n<code>{str(e)[:200]}</code>", parse_mode=ParseMode.HTML)

# --- Message Handlers ---

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    voice = update.message.voice or update.message.audio
    if not voice:
        return
    
    file = await voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)

async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle video messages"""
    video = update.message.video or update.message.video_note
    if not video:
        return
    
    file = await video.get_file()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle audio/video file uploads"""
    doc = update.message.document
    if not doc:
        return
    
    mime = doc.mime_type or ""
    if not any(t in mime for t in ["audio", "video", "ogg", "mp4", "mp3", "wav", "m4a"]):
        await update.message.reply_text("🤔 Отправь аудио или видео файл. Документы пока не поддерживаю.")
        return
    
    file = await doc.get_file()
    ext = os.path.splitext(doc.file_name or "file.mp4")[1]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)

async def handle_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle URLs in text messages"""
    text = update.message.text or ""
    
    # Extract URL
    import re
    urls = re.findall(r'https?://\S+', text)
    if not urls:
        await update.message.reply_text(
            "🧠 Отправь мне:\n"
            "• 🎤 Голосовое сообщение\n"
            "• 🔗 Ссылку (YouTube, Google Drive)\n"
            "• 🎬 Видео файл\n\n"
            "Или открой Mini App! 👇",
            reply_markup=main_keyboard()
        )
        return
    
    await process_content(update, ctx, url=urls[0])

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "help":
        await query.message.reply_text(
            "📖 Отправь голосовое, видео или ссылку — я разберу!",
            parse_mode=ParseMode.HTML
        )
    elif data == "settings":
        await query.message.edit_text(
            "⚙️ <b>Настройки</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=settings_keyboard(ctx.user_data)
        )
    elif data == "back_main":
        await query.message.edit_text(
            "🧠 <b>Цифровой Умник</b> — готов к работе!",
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard()
        )
    elif data.startswith("fmt_"):
        fmt = data.replace("fmt_", "")
        ctx.user_data["format"] = fmt
        await query.message.edit_text(f"✅ Формат отчёта: <b>{fmt}</b>", parse_mode=ParseMode.HTML)
    elif data == "set_format":
        await query.message.edit_text(
            "📊 <b>Выбери формат отчёта:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=format_keyboard()
        )

# ========== MAIN ==========
def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    
    # Content handlers
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("🧠 Цифровой Умник v5.0 запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
