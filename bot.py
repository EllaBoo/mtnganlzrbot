#!/usr/bin/env python3
"""
🧠 Digital Smarty v5.0 — Цифровой Умник
Telegram Bot + Mini App Hybrid
Built on Dronor Expert Architecture

Каждый шаг обработки = вызов Dronor эксперта через API:
  1. ds_url_resolver      → определить источник
  2. ds_audio_extractor   → извлечь аудио
  3. ds_transcriber       → транскрибировать
  4. ds_topic_extractor   → извлечь темы
  5. ds_expert_analyzer   → экспертный анализ
  6. ds_report_generator  → сгенерировать отчёт
  7. ds_context_manager   → сохранить контекст
"""
import asyncio
import logging
import os
import re
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
)
logger = logging.getLogger("smarty")

# Dronor Expert Client
dronor = DronorClient(config.DRONOR_API)


# ══════════════════════════════════════════════════════════
# CHARACTER: Цифровой Умник
# ══════════════════════════════════════════════════════════

MSGS = {
    "welcome": (
        "🧠 <b>Привет! Я Цифровой Умник</b>\n\n"
        "Кидай мне любой контент — я разберу его как эксперт:\n\n"
        "🎤 <b>Голосовые и аудио</b> — записи встреч, подкасты\n"
        "🎬 <b>Видео</b> — лекции, вебинары, созвоны\n"
        "🔗 <b>Ссылки</b> — YouTube, Google Drive, Dropbox\n\n"
        "Я <b>сам определю тему</b> и стану экспертом в ней 🎯\n"
        "Бизнес, маркетинг, медицина, право — что угодно!\n\n"
        "💡 <i>Попробуй: отправь ссылку на YouTube видео</i>"
    ),

    "help": (
        "📖 <b>Как использовать Цифрового Умника:</b>\n\n"
        "1️⃣ Отправь <b>голосовое/аудио/видео</b> сообщение\n"
        "2️⃣ Или кинь <b>ссылку</b> на YouTube, Google Drive, Dropbox\n"
        "3️⃣ Или открой <b>Mini App</b> для записи прямо в боте\n\n"
        "Я определю тему и дам экспертный анализ:\n"
        "📌 Факты из записи (только то, что реально сказано!)\n"
        "💡 Рекомендации эксперта (помечены отдельно)\n"
        "📊 SWOT-анализ ситуации\n"
        "✅ Action Items с ответственными и сроками\n"
        "❓ Открытые вопросы для проработки\n\n"
        "⚡ <b>Умник адаптируется к ЛЮБОЙ области</b> — бизнес, "
        "маркетинг, продукт, HR, юриспруденция, медицина, "
        "образование, дизайн, психология..."
    ),

    "stages": [
        "🔍 Определяю источник...",
        "🎵 Извлекаю аудио...",
        "📝 Транскрибирую (Deepgram Nova-2)...",
        "🧩 Анализирую темы и структуру...",
        "🧠 Погружаюсь в экспертизу...",
        "📊 Формирую отчёт..."
    ],

    "done": "🎯 <b>Готово!</b> Вот что я нашёл:",
    "error": "😅 Упс, что-то пошло не так. Попробуй ещё раз!",
    "no_audio": "🤔 Не смог разобрать речь. Возможно, качество записи низкое.",
    "bad_url": "❌ Не удалось извлечь аудио. Проверь ссылку — она публичная?",
    "unsupported": (
        "🤔 Отправь мне:\n"
        "• 🎤 Голосовое сообщение\n"
        "• 🔗 Ссылку (YouTube, Google Drive)\n"
        "• 🎬 Видео файл\n\n"
        "Или открой Mini App! 👇"
    ),
}


# ══════════════════════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════════════════════

def kb_main():
    rows = []
    if config.WEBAPP_URL:
        rows.append([InlineKeyboardButton(
            "🚀 Открыть Mini App",
            web_app=WebAppInfo(url=config.WEBAPP_URL)
        )])
    rows.extend([
        [
            InlineKeyboardButton("📋 Мои отчёты", callback_data="history"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        ],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")],
    ])
    return InlineKeyboardMarkup(rows)


def kb_formats():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 PDF", callback_data="fmt:pdf"),
            InlineKeyboardButton("🌙 HTML Dark", callback_data="fmt:html_dark"),
        ],
        [
            InlineKeyboardButton("☀️ HTML Light", callback_data="fmt:html_light"),
            InlineKeyboardButton("📝 TXT", callback_data="fmt:txt"),
        ],
        [InlineKeyboardButton("🔧 JSON (API)", callback_data="fmt:json")],
    ])


def kb_settings(user_data: dict):
    lang = user_data.get("language", "auto")
    fmt = user_data.get("format", config.DEFAULT_FORMAT)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🌐 Язык: {lang}", callback_data="set:language")],
        [InlineKeyboardButton(f"📊 Формат: {fmt}", callback_data="set:format")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")],
    ])


def kb_languages():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 Auto", callback_data="lang:auto"),
            InlineKeyboardButton("🇷🇺 RU", callback_data="lang:ru"),
        ],
        [
            InlineKeyboardButton("🇺🇸 EN", callback_data="lang:en"),
            InlineKeyboardButton("🇰🇿 KZ", callback_data="lang:kk"),
        ],
    ])


# ══════════════════════════════════════════════════════════
# PROCESSING PIPELINE — calls Dronor experts step by step
# ══════════════════════════════════════════════════════════

async def update_stage(msg, stage_idx: int):
    """Update progress message with current stage"""
    stages = MSGS["stages"]
    if stage_idx < len(stages):
        # Build progress bar
        dots = ""
        for i in range(len(stages)):
            if i < stage_idx:
                dots += "✅ "
            elif i == stage_idx:
                dots += "⏳ "
            else:
                dots += "⬜ "

        text = f"{dots}\n\n{stages[stage_idx]}"
        try:
            await msg.edit_text(text)
        except Exception:
            pass


async def process_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                          url: str = None, file_path: str = None):
    """
    Main processing pipeline.
    Each step = Dronor expert call.
    """
    user_id = str(update.effective_user.id)
    chat = update.effective_chat

    # Progress message
    msg = await update.message.reply_text("⏳ Запускаю анализ...")

    try:
        # ── Stage 1: URL Resolve ──
        source_type = "telegram"
        if url:
            await update_stage(msg, 0)
            await chat.send_action(ChatAction.TYPING)
            resolved = dronor.resolve_url(url)
            r = resolved.get("result", {})
            source_type = r.get("source_type", "unknown") if isinstance(r, dict) else "unknown"

        # ── Stage 2: Audio Extraction ──
        await update_stage(msg, 1)
        await chat.send_action(ChatAction.TYPING)
        audio = dronor.extract_audio(
            url=url or "",
            file_path=file_path or "",
            source_type=source_type
        )
        audio_r = audio.get("result", {})
        audio_path = audio_r.get("audio_path", "") if isinstance(audio_r, dict) else ""

        if not audio_path:
            await msg.edit_text(MSGS["bad_url"])
            return

        # ── Stage 3: Transcription (Deepgram) ──
        await update_stage(msg, 2)
        await chat.send_action(ChatAction.TYPING)
        lang = ctx.user_data.get("language", config.DEFAULT_LANG)
        trans = dronor.transcribe(audio_path, lang)
        trans_r = trans.get("result", {})
        text = trans_r.get("transcription", "") if isinstance(trans_r, dict) else str(trans_r)

        if not text or len(text) < 20:
            await msg.edit_text(MSGS["no_audio"])
            return

        word_count = trans_r.get("word_count", len(text.split())) if isinstance(trans_r, dict) else len(text.split())

        # ── Stage 4: Topic Extraction (GPT-4o) ──
        await update_stage(msg, 3)
        await chat.send_action(ChatAction.TYPING)
        segments_str = ""
        if isinstance(trans_r, dict) and trans_r.get("segments"):
            segments_str = json.dumps(trans_r["segments"], ensure_ascii=False)
        topics = dronor.extract_topics(text, segments_str)
        topic_data = topics.get("result", {})
        topic_json = json.dumps(topic_data, ensure_ascii=False, default=str)

        # ── Stage 5: Expert Analysis (GPT-4o) ──
        await update_stage(msg, 4)
        await chat.send_action(ChatAction.TYPING)
        expert = dronor.analyze_expert(text, topic_json)
        expert_data = expert.get("result", {})
        expert_json = json.dumps(expert_data, ensure_ascii=False, default=str)

        # ── Stage 6: Report Generation ──
        await update_stage(msg, 5)
        await chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        fmt = ctx.user_data.get("format", config.DEFAULT_FORMAT)
        report = dronor.generate_report(text, topic_json, expert_json, fmt)
        report_r = report.get("result", {})

        # ═══ BUILD SUMMARY MESSAGE ═══
        summary = build_summary(topic_data, expert_data, word_count)
        await msg.edit_text(summary, parse_mode=ParseMode.HTML)

        # Send report file
        if isinstance(report_r, dict) and report_r.get("file_path"):
            fpath = report_r["file_path"]
            if os.path.exists(fpath):
                with open(fpath, 'rb') as f:
                    await update.message.reply_document(
                        InputFile(f, filename=os.path.basename(fpath)),
                        caption="📊 Полный отчёт Цифрового Умника"
                    )

        # Format switcher
        await update.message.reply_text(
            "📥 Другой формат отчёта?",
            reply_markup=kb_formats()
        )

        # ── Save context ──
        ctx_data = {
            "domain": topic_data.get("domain", "") if isinstance(topic_data, dict) else "",
            "meeting_type": topic_data.get("meeting_type", "") if isinstance(topic_data, dict) else "",
            "topics_count": len(topic_data.get("topics", [])) if isinstance(topic_data, dict) else 0,
            "word_count": word_count,
            "format": fmt,
            "timestamp": datetime.now().isoformat(),
        }
        dronor.save_context(user_id, json.dumps(ctx_data, ensure_ascii=False))

        # Save for re-export
        ctx.user_data["last_transcription"] = text[:5000]
        ctx.user_data["last_topic_json"] = topic_json[:5000]
        ctx.user_data["last_expert_json"] = expert_json[:5000]

    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        await msg.edit_text(
            f"{MSGS['error']}\n\n<code>{str(e)[:300]}</code>",
            parse_mode=ParseMode.HTML
        )


def build_summary(topic_data: dict, expert_data: dict, word_count: int) -> str:
    """Build concise summary message from expert results"""
    lines = []

    # Header
    domain = "General"
    meeting_type = ""
    if isinstance(topic_data, dict):
        domain = topic_data.get("domain", "General")
        meeting_type = topic_data.get("meeting_type", "")

    expert_role = ""
    if isinstance(expert_data, dict):
        expert_role = expert_data.get("expert_role", "")

    lines.append(f"🧠 <b>Цифровой Умник — {domain.upper()}</b>")
    if expert_role:
        lines.append(f"👤 Эксперт: <i>{expert_role}</i>")
    if meeting_type:
        lines.append(f"📋 Тип: {meeting_type}")
    lines.append(f"📝 Слов: {word_count:,}")
    lines.append("")

    # Executive summary
    if isinstance(topic_data, dict):
        summary = topic_data.get("executive_summary", "")
        if summary:
            lines.append(f"📌 {summary}")
            lines.append("")

    # Topics
    if isinstance(topic_data, dict):
        topics = topic_data.get("topics", [])
        if topics:
            lines.append("<b>📑 Темы:</b>")
            for i, t in enumerate(topics[:6], 1):
                name = t.get("name", str(t)) if isinstance(t, dict) else str(t)
                lines.append(f"  {i}. {name}")
            lines.append("")

    # Decisions
    if isinstance(topic_data, dict):
        decisions = topic_data.get("decisions", [])
        if decisions:
            lines.append("<b>📌 Решения:</b>")
            for d in decisions[:4]:
                txt = d.get("text", str(d)) if isinstance(d, dict) else str(d)
                lines.append(f"  • {txt}")
            lines.append("")

    # Action items
    if isinstance(topic_data, dict):
        actions = topic_data.get("action_items", [])
        if actions:
            lines.append("<b>✅ Action Items:</b>")
            for a in actions[:4]:
                if isinstance(a, dict):
                    task = a.get("task", "")
                    who = a.get("assignee", "")
                    deadline = a.get("deadline", "")
                    line = f"  • {task}"
                    if who:
                        line += f" → {who}"
                    if deadline:
                        line += f" ({deadline})"
                    lines.append(line)
                else:
                    lines.append(f"  • {a}")
            lines.append("")

    # SWOT preview
    if isinstance(expert_data, dict):
        assess = expert_data.get("assessment", {})
        if isinstance(assess, dict):
            strengths = assess.get("strengths", [])
            weaknesses = assess.get("weaknesses", [])
            if strengths or weaknesses:
                lines.append("<b>📊 SWOT (краткий):</b>")
                if strengths:
                    s = strengths[0] if isinstance(strengths[0], str) else str(strengths[0])
                    lines.append(f"  💪 {s[:80]}")
                if weaknesses:
                    w = weaknesses[0] if isinstance(weaknesses[0], str) else str(weaknesses[0])
                    lines.append(f"  ⚠️ {w[:80]}")
                lines.append("")

    # Top recommendation
    if isinstance(expert_data, dict):
        recs = expert_data.get("recommendations", [])
        if recs:
            lines.append("<b>💡 Главная рекомендация:</b>")
            rec = recs[0]
            if isinstance(rec, dict):
                lines.append(f"  {rec.get('recommendation', str(rec))[:120]}")
            else:
                lines.append(f"  {str(rec)[:120]}")

    lines.append("\n📊 <i>Полный отчёт — в файле ниже</i>")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# MESSAGE HANDLERS
# ══════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Load user context from Dronor
    user_id = str(update.effective_user.id)
    history = dronor.load_context(user_id)
    if isinstance(history.get("result"), dict):
        enriched = history["result"].get("context_summary", "")
        if enriched:
            ctx.user_data["has_history"] = True

    await update.message.reply_text(
        MSGS["welcome"],
        parse_mode=ParseMode.HTML,
        reply_markup=kb_main()
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MSGS["help"],
        parse_mode=ParseMode.HTML,
        reply_markup=kb_main()
    )


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Voice messages and audio files"""
    voice = update.message.voice or update.message.audio
    if not voice:
        return

    file = await voice.get_file()
    ext = ".ogg" if update.message.voice else ".mp3"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Video messages and video notes"""
    video = update.message.video or update.message.video_note
    if not video:
        return

    file = await video.get_file()
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Audio/video file uploads"""
    doc = update.message.document
    if not doc:
        return

    mime = doc.mime_type or ""
    supported = ("audio", "video", "ogg", "mp4", "mp3", "wav", "m4a", "webm", "mpeg")
    if not any(t in mime for t in supported):
        await update.message.reply_text(
            "🤔 Отправь аудио или видео файл — документы пока не поддерживаю."
        )
        return

    file = await doc.get_file()
    ext = os.path.splitext(doc.file_name or "file.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        await process_content(update, ctx, file_path=tmp.name)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Text messages — check for URLs"""
    text = (update.message.text or "").strip()
    if not text:
        return

    urls = re.findall(r'https?://\S+', text)
    if urls:
        await process_content(update, ctx, url=urls[0])
    else:
        await update.message.reply_text(
            MSGS["unsupported"],
            parse_mode=ParseMode.HTML,
            reply_markup=kb_main()
        )


# ══════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ══════════════════════════════════════════════════════════

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # ── Format selection ──
    if data.startswith("fmt:"):
        fmt = data.split(":")[1]
        ctx.user_data["format"] = fmt

        # Re-generate report if we have cached data
        last_trans = ctx.user_data.get("last_transcription")
        last_topic = ctx.user_data.get("last_topic_json")
        last_expert = ctx.user_data.get("last_expert_json")

        if last_trans and last_topic and last_expert:
            await q.message.edit_text(f"📊 Генерирую отчёт в формате <b>{fmt}</b>...",
                                      parse_mode=ParseMode.HTML)
            report = dronor.generate_report(last_trans, last_topic, last_expert, fmt)
            report_r = report.get("result", {})
            if isinstance(report_r, dict) and report_r.get("file_path"):
                fpath = report_r["file_path"]
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        await q.message.reply_document(
                            InputFile(f, filename=os.path.basename(fpath)),
                            caption=f"📊 Отчёт ({fmt})"
                        )
            else:
                await q.message.edit_text(f"✅ Формат: <b>{fmt}</b>. Отправь контент для анализа.",
                                          parse_mode=ParseMode.HTML)
        else:
            await q.message.edit_text(f"✅ Формат: <b>{fmt}</b>. Отправь контент для анализа.",
                                      parse_mode=ParseMode.HTML)

    # ── Settings ──
    elif data == "settings":
        await q.message.edit_text(
            "⚙️ <b>Настройки Цифрового Умника</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_settings(ctx.user_data)
        )

    elif data == "set:language":
        await q.message.edit_text(
            "🌐 <b>Выбери язык транскрипции:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_languages()
        )

    elif data.startswith("lang:"):
        lang = data.split(":")[1]
        ctx.user_data["language"] = lang
        await q.message.edit_text(
            f"✅ Язык: <b>{lang}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_settings(ctx.user_data)
        )

    elif data == "set:format":
        await q.message.edit_text(
            "📊 <b>Выбери формат отчёта:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_formats()
        )

    # ── History ──
    elif data == "history":
        user_id = str(q.from_user.id)
        history = dronor.get_user_history(user_id)
        hist_r = history.get("result", {})

        if isinstance(hist_r, dict):
            sessions = hist_r.get("sessions", [])
            if sessions:
                lines = ["📋 <b>Последние анализы:</b>\n"]
                for s in sessions[:5]:
                    ts = s.get("timestamp", "")[:16]
                    domain = s.get("domain", "?")
                    lines.append(f"  • {ts} — {domain}")
                await q.message.edit_text(
                    "\n".join(lines),
                    parse_mode=ParseMode.HTML
                )
            else:
                await q.message.edit_text("📋 Пока нет анализов. Отправь контент!")
        else:
            await q.message.edit_text("📋 Пока нет анализов. Отправь контент!")

    # ── Help ──
    elif data == "help":
        await q.message.reply_text(MSGS["help"], parse_mode=ParseMode.HTML)

    # ── Back ──
    elif data == "back":
        await q.message.edit_text(
            "🧠 <b>Цифровой Умник</b> — готов к работе!",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_main()
        )


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

def main():
    if not config.BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not set!")
        return

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))

    # Content handlers
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("🧠 Цифровой Умник v5.0 запущен!")
    logger.info(f"   Dronor API: {config.DRONOR_API}")
    logger.info(f"   Mini App: {config.WEBAPP_URL or 'disabled'}")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
