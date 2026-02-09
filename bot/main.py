"""
Digital Smarty v4.0 - Main Bot
🧠 Адаптивный AI-эксперт, который становится профессионалом в теме записи
"""
import asyncio
import logging
import re
from pathlib import Path
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

import config
from bot.translations import t, set_user_lang, get_user_lang, get_lang_name
from bot.keyboards import language_keyboard, main_keyboard, back_keyboard

# Core modules
from core.transcription import transcribe_audio
from core.analysis import analyze_transcript, answer_question, detect_expertise
from core.diagnostics import diagnose_communication
from core.pdf_generator import generate_pdf_report
from core.topic_extractor import extract_main_topic

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot
app = Client(
    "digital_smarty_bot",
    api_id=config.TELEGRAM_API_ID,
    api_hash=config.TELEGRAM_API_HASH,
    bot_token=config.TELEGRAM_BOT_TOKEN,
    workdir=str(config.SESSIONS_DIR)
)

# User session cache
user_cache = {}


def get_cache(user_id: int) -> dict:
    """Get or create user cache"""
    if user_id not in user_cache:
        user_cache[user_id] = {}
    return user_cache[user_id]


def format_duration(seconds: float) -> str:
    """Format duration as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def extract_score(diagnostics: str) -> tuple:
    """Extract score and emoji from diagnostics"""
    score_match = re.search(r'(\d{1,3})/100', diagnostics)
    score = int(score_match.group(1)) if score_match else None
    
    if score is None:
        return "?", "⚪"
    elif score >= 90:
        return score, "🟢"
    elif score >= 70:
        return score, "🟡"
    elif score >= 50:
        return score, "🟠"
    else:
        return score, "🔴"


def extract_expert_tip(diagnostics: str, lang: str) -> str:
    """Extract expert tip from diagnostics"""
    # Try to find tip section
    patterns = [
        r'СОВЕТ ЦИФРОВОГО УМНИКА[:\s]*\n([^#]+)',
        r'DIGITAL SMARTY TIP[:\s]*\n([^#]+)',
        r'💡[^:]*:[^\n]*\n([^#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, diagnostics, re.IGNORECASE)
        if match:
            tip = match.group(1).strip()[:400]
            if tip:
                return f"\n\n_💡 {tip}_"
    
    return ""


# ═══════════════════════════════════════════════════════════════
# HANDLERS
# ═══════════════════════════════════════════════════════════════

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    """Handle /start command"""
    uid = message.from_user.id
    await message.reply(
        t(uid, "welcome"),
        parse_mode=ParseMode.MARKDOWN
    )


@app.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    """Handle /help command"""
    uid = message.from_user.id
    await message.reply(
        t(uid, "welcome"),
        parse_mode=ParseMode.MARKDOWN
    )


@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client: Client, message: Message):
    """Handle media files"""
    uid = message.from_user.id
    cache = get_cache(uid)
    
    # Check file size
    file_size = 0
    if message.audio:
        file_size = message.audio.file_size
    elif message.video:
        file_size = message.video.file_size
    elif message.voice:
        file_size = message.voice.file_size
    elif message.video_note:
        file_size = message.video_note.file_size
    elif message.document:
        file_size = message.document.file_size
        mime = message.document.mime_type or ""
        if not (mime.startswith("audio/") or mime.startswith("video/")):
            await message.reply(t(uid, "unsupported_format"))
            return
    
    if file_size > 100 * 1024 * 1024:  # 100 MB
        await message.reply(t(uid, "file_too_large"))
        return
    
    # Save pending message and ask for language
    cache["pending_message"] = message
    await message.reply(
        t(uid, "choose_lang"),
        reply_markup=language_keyboard()
    )


@app.on_callback_query()
async def callback_handler(client: Client, callback: CallbackQuery):
    """Handle callback queries"""
    uid = callback.from_user.id
    data = callback.data
    cache = get_cache(uid)
    
    try:
        # ═══════════════════════════════════════════════════════════
        # LANGUAGE SELECTION
        # ═══════════════════════════════════════════════════════════
        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_user_lang(uid, lang)
            await callback.answer()
            
            if "pending_message" in cache:
                await process_media(client, callback.message, cache["pending_message"], uid)
                del cache["pending_message"]
            return
        
        # ═══════════════════════════════════════════════════════════
        # ASK QUESTION
        # ═══════════════════════════════════════════════════════════
        elif data == "ask":
            if "transcript" not in cache:
                await callback.answer(t(uid, "no_data"), show_alert=True)
                return
            
            cache["waiting_question"] = True
            await callback.answer()
            
            expert_role = cache.get("expertise", {}).get("expert_role", "эксперт")
            await callback.message.reply(
                t(uid, "question_prompt", expert_role=expert_role),
                reply_markup=back_keyboard(uid)
            )
            return
        
        # ═══════════════════════════════════════════════════════════
        # GET TRANSCRIPT
        # ═══════════════════════════════════════════════════════════
        elif data == "transcript":
            if "transcript" not in cache:
                await callback.answer(t(uid, "no_data"), show_alert=True)
                return
            
            await callback.answer()
            
            # Generate filename
            topic = cache.get("main_topic", "transcript")
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename = f"{topic}_{timestamp}.txt"
            filename = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
            
            # Save and send
            transcript_path = config.TMP_DIR / filename
            transcript_path.write_text(cache["transcript"], encoding="utf-8")
            
            await callback.message.reply_document(
                document=str(transcript_path),
                caption=f"📜 {filename}"
            )
            
            transcript_path.unlink(missing_ok=True)
            return
        
        # ═══════════════════════════════════════════════════════════
        # NEW ANALYSIS
        # ═══════════════════════════════════════════════════════════
        elif data == "new":
            # Clear cache
            cache.clear()
            await callback.answer()
            await callback.message.reply(
                t(uid, "welcome"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # ═══════════════════════════════════════════════════════════
        # BACK
        # ═══════════════════════════════════════════════════════════
        elif data == "back":
            cache["waiting_question"] = False
            await callback.answer()
            
            if "analysis" in cache:
                # Show summary again
                expertise = cache.get("expertise", {})
                score, score_emoji = extract_score(cache.get("diagnostics", ""))
                tip = extract_expert_tip(cache.get("diagnostics", ""), get_user_lang(uid))
                
                summary = t(
                    uid, "analysis_complete",
                    score=score,
                    score_emoji=score_emoji,
                    meeting_type=expertise.get("meeting_type_localized", expertise.get("meeting_type", "")),
                    expert_role=expertise.get("expert_role", ""),
                    duration=format_duration(cache.get("duration", 0)),
                    speakers=cache.get("speakers_count", 1),
                    tip=tip
                )
                
                await callback.message.edit_text(
                    summary,
                    reply_markup=main_keyboard(uid, expertise.get("expert_role", "")),
                    parse_mode=ParseMode.MARKDOWN
                )
            return
    
    except Exception as e:
        logger.error(f"Callback error: {e}", exc_info=True)
        await callback.answer(t(uid, "error", error=str(e)[:50]), show_alert=True)


@app.on_message(filters.text & filters.private)
async def text_handler(client: Client, message: Message):
    """Handle text messages (questions)"""
    uid = message.from_user.id
    cache = get_cache(uid)
    
    # Check if waiting for question
    if cache.get("waiting_question") and "transcript" in cache:
        cache["waiting_question"] = False
        
        expertise = cache.get("expertise", {})
        expert_role = expertise.get("expert_role", "эксперт")
        
        status_msg = await message.reply(
            t(uid, "thinking", expert_role=expert_role)
        )
        
        try:
            # Answer as expert
            answer = await answer_question(
                question=message.text,
                transcript=cache["transcript"],
                analysis=cache.get("analysis", ""),
                language=get_user_lang(uid),
                expertise=expertise
            )
            
            await status_msg.edit_text(
                f"💬 **{expert_role}:**\n\n{answer}",
                reply_markup=main_keyboard(uid, expert_role),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Question error: {e}", exc_info=True)
            await status_msg.edit_text(t(uid, "error", error=str(e)[:100]))


# ═══════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ═══════════════════════════════════════════════════════════════

async def process_media(client: Client, status_message: Message, media_message: Message, uid: int):
    """Process media file and generate analysis"""
    cache = get_cache(uid)
    lang = get_user_lang(uid)
    
    try:
        # ═══════════════════════════════════════════════════════════
        # 1. DOWNLOAD
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(t(uid, "processing"))
        
        file_path = await media_message.download(
            file_name=str(config.TMP_DIR / f"{uid}_media")
        )
        file_path = Path(file_path)
        
        # ═══════════════════════════════════════════════════════════
        # 2. TRANSCRIBE
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(t(uid, "transcribing"))
        
        transcript_result = await transcribe_audio(str(file_path))
        cache["transcript"] = transcript_result["text"]
        cache["speakers"] = transcript_result.get("speakers", [])
        cache["duration"] = transcript_result.get("duration", 0)
        cache["speakers_count"] = transcript_result.get("speakers_count", 1)
        
        # ═══════════════════════════════════════════════════════════
        # 3. DETECT EXPERTISE
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(t(uid, "detecting_expertise"))
        
        expertise = await detect_expertise(cache["transcript"], lang)
        cache["expertise"] = expertise
        
        logger.info(f"User {uid}: Expert mode = {expertise['expert_role']} in {expertise['domain']}")
        
        # ═══════════════════════════════════════════════════════════
        # 4. ANALYZE AS EXPERT
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(
            t(uid, "analyzing_as_expert", expert_role=expertise["expert_role"])
        )
        
        analysis = await analyze_transcript(
            transcript=cache["transcript"],
            language=lang,
            expertise=expertise
        )
        cache["analysis"] = analysis
        
        # ═══════════════════════════════════════════════════════════
        # 5. DIAGNOSE
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(t(uid, "diagnosing"))
        
        diagnostics = await diagnose_communication(
            transcript=cache["transcript"],
            language=lang,
            expertise=expertise
        )
        cache["diagnostics"] = diagnostics
        
        # ═══════════════════════════════════════════════════════════
        # 6. EXTRACT TOPIC
        # ═══════════════════════════════════════════════════════════
        main_topic = await extract_main_topic(analysis, lang)
        cache["main_topic"] = main_topic
        
        # ═══════════════════════════════════════════════════════════
        # 7. GENERATE PDF
        # ═══════════════════════════════════════════════════════════
        await status_message.edit_text(t(uid, "generating_pdf"))
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        pdf_filename = f"{main_topic}_{timestamp}.pdf"
        pdf_filename = "".join(c if c.isalnum() or c in "._- " else "_" for c in pdf_filename)
        pdf_path = config.TMP_DIR / pdf_filename
        
        await generate_pdf_report(
            output_path=str(pdf_path),
            analysis=analysis,
            diagnostics=diagnostics,
            transcript=cache["transcript"],
            duration=cache["duration"],
            speakers_count=cache["speakers_count"],
            language=lang,
            expertise=expertise
        )
        
        # ═══════════════════════════════════════════════════════════
        # 8. SEND RESULTS
        # ═══════════════════════════════════════════════════════════
        await status_message.delete()
        
        # Send PDF
        await media_message.reply_document(
            document=str(pdf_path),
            caption=f"📄 {pdf_filename}"
        )
        
        # Send summary
        score, score_emoji = extract_score(diagnostics)
        tip = extract_expert_tip(diagnostics, lang)
        
        summary = t(
            uid, "analysis_complete",
            score=score,
            score_emoji=score_emoji,
            meeting_type=expertise.get("meeting_type_localized", expertise.get("meeting_type", "")),
            expert_role=expertise["expert_role"],
            duration=format_duration(cache["duration"]),
            speakers=cache["speakers_count"],
            tip=tip
        )
        
        await media_message.reply(
            summary,
            reply_markup=main_keyboard(uid, expertise["expert_role"]),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Cleanup
        file_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Processing error for user {uid}: {e}", exc_info=True)
        await status_message.edit_text(t(uid, "error", error=str(e)[:200]))


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("🚀 Starting Digital Smarty Bot v4.0...")
    logger.info("🧠 Adaptive Expert Mode enabled")
    
    # Ensure directories
    config.SESSIONS_DIR.mkdir(exist_ok=True)
    config.TMP_DIR.mkdir(exist_ok=True)
    
    app.run()
