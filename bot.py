import os
import asyncio
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from processor import Processor

if Config.STRING_SESSION:
    app = Client(
        "smarty_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        session_string=Config.STRING_SESSION
    )
else:
    app = Client(
        "smarty_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )

processor = Processor()
user_states = {}

WELCOME_MESSAGE = """**Digital Smarty v4.0**

Hey! I'm your digital meeting analyst.

Send me audio or video recordings (MP3, M4A, WAV, MP4, MOV, WebM) and I'll give you:

- **Structured summary** with topics, decisions and tasks
- **Reality Check** - critical analysis of agreements
- **PDF report** - beautiful, for sharing
- **Text transcript** - full conversation text

I can process recordings up to 3+ hours. Just send a file or link!

_Yes, I'm a bit sarcastic. But that's because I'm smart_
"""

LANGUAGE_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Russian", callback_data="lang_ru"),
        InlineKeyboardButton("English", callback_data="lang_en")
    ],
    [
        InlineKeyboardButton("Kazakh", callback_data="lang_kk"),
        InlineKeyboardButton("Spanish", callback_data="lang_es")
    ],
    [
        InlineKeyboardButton("Original language", callback_data="lang_auto")
    ]
])


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply(WELCOME_MESSAGE, parse_mode="markdown")


@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def file_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    user_states[user_id] = {
        "file_message": message,
        "status": "waiting_language"
    }
    
    await message.reply(
        "Great file! What language do you want the result in?",
        reply_markup=LANGUAGE_KEYBOARD
    )


@app.on_message(filters.text & ~filters.command(["start", "help"]))
async def text_handler(client: Client, message: Message):
    text = message.text.strip()
    
    if text.startswith(("http://", "https://", "www.")):
        user_id = message.from_user.id
        user_states[user_id] = {
            "url": text,
            "status": "waiting_language"
        }
        
        await message.reply(
            "Link received! What language do you want the result in?",
            reply_markup=LANGUAGE_KEYBOARD
        )
    else:
        await message.reply(
            "Hmm, I didn't understand. Send me an audio/video file or a link to it.\n\n"
            "Supported: MP3, M4A, WAV, MP4, MOV, WebM, and cloud storage links."
        )


@app.on_callback_query(filters.regex(r"^lang_"))
async def language_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    language = callback.data.replace("lang_", "")
    
    if user_id not in user_states:
        await callback.answer("Session expired. Please send the file again.", show_alert=True)
        return
    
    state = user_states[user_id]
    
    await callback.answer("Got it!")
    
    lang_names = {"ru": "Russian", "en": "English", "kk": "Kazakh", "es": "Spanish", "auto": "Original"}
    await callback.message.edit_text(f"Processing started...\n\nResult language: {lang_names.get(language, language)}")
    
    asyncio.create_task(process_file(client, callback.message, state, language, user_id))


async def process_file(client: Client, status_message: Message, state: dict, language: str, user_id: int):
    try:
        temp_dir = Path(Config.TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        async def update_status(text: str):
            try:
                await status_message.edit_text(text)
            except:
                pass
        
        if "file_message" in state:
            file_message = state["file_message"]
            
            await update_status("Downloading file...")
            
            if file_message.audio:
                file = file_message.audio
            elif file_message.video:
                file = file_message.video
            elif file_message.document:
                file = file_message.document
            elif file_message.voice:
                file = file_message.voice
            elif file_message.video_note:
                file = file_message.video_note
            else:
                await update_status("Could not determine file type")
                return
            
            file_path = await client.download_media(
                file_message,
                file_name=str(temp_dir / f"{user_id}_{file.file_id[:8]}")
            )
            
        elif "url" in state:
            await update_status("Downloading file from link...")
            file_path = await processor.download_file(state["url"], update_status)
        else:
            await update_status("Error: file not found")
            return
        
        result = await processor.process(file_path, language, update_status)
        
        if not result["success"]:
            await update_status(f"Processing error: {result['error']}")
            return
        
        await update_status("Sending results...")
        
        analysis = result["analysis"]
        
        summary_text = format_summary_for_telegram(analysis)
        await status_message.reply(summary_text, parse_mode="markdown")
        
        await status_message.reply_document(
            document=result["pdf_path"],
            caption="PDF Report"
        )
        
        await status_message.reply_document(
            document=result["html_path"],
            caption="HTML Report (interactive)"
        )
        
        await status_message.reply_document(
            document=result["transcript_path"],
            caption="Full Transcript"
        )
        
        await status_message.reply(
            "**Done!**\n\n"
            "Want to know more? I can:\n"
            "- Dive deeper into a specific topic\n"
            "- Generate an email summary for your team\n"
            "- Redo the report in another language\n\n"
            "_Just tell me what you need!_",
            parse_mode="markdown"
        )
        
        try:
            await status_message.delete()
        except:
            pass
        
        try:
            os.remove(file_path)
            os.remove(result["pdf_path"])
            os.remove(result["html_path"])
            os.remove(result["transcript_path"])
        except:
            pass
        
    except Exception as e:
        await status_message.edit_text(f"An error occurred: {str(e)}")
    
    finally:
        if user_id in user_states:
            del user_states[user_id]


def format_summary_for_telegram(analysis: dict) -> str:
    lines = []
    
    lines.append(f"**{analysis.get('title', 'Meeting Summary')}**\n")
    
    meta = []
    if analysis.get("date_mentioned"):
        meta.append(f"{analysis['date_mentioned']}")
    if analysis.get("duration_minutes"):
        meta.append(f"{analysis['duration_minutes']} min")
    if analysis.get("participants_count"):
        meta.append(f"{analysis['participants_count']} participants")
    
    if meta:
        lines.append(" | ".join(meta) + "\n")
    
    if analysis.get("smarty_comment"):
        lines.append(f'_"{analysis["smarty_comment"]}"_\n')
    
    if analysis.get("key_topics"):
        lines.append("**Key Topics:**")
        for topic in analysis["key_topics"][:5]:
            lines.append(f"- **{topic['topic']}** - {topic['summary']}")
        lines.append("")
    
    if analysis.get("decisions"):
        lines.append("**Decisions:**")
        for i, d in enumerate(analysis["decisions"][:5], 1):
            lines.append(f"{i}. {d['decision']}")
        lines.append("")
    
    if analysis.get("action_items"):
        lines.append("**Tasks:**")
        for task in analysis["action_items"][:5]:
            lines.append(f"[ ] {task['task']} -> {task['responsible']}")
        lines.append("")
    
    if analysis.get("key_insights"):
        lines.append("**Key Insights:**")
        for i, insight in enumerate(analysis["key_insights"][:3], 1):
            lines.append(f"{i}. {insight}")
    
    return "\n".join(lines)


@app.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    await message.reply(
        "**How to use Digital Smarty:**\n\n"
        "1. Send an audio/video file or link\n"
        "2. Choose the result language\n"
        "3. Wait for processing (usually 2-5 min per hour of recording)\n"
        "4. Get summary, PDF and transcript\n\n"
        "**Supported formats:**\n"
        "Audio: MP3, M4A, WAV, OGG, FLAC\n"
        "Video: MP4, MOV, WebM, AVI, MKV\n"
        "Links: direct URLs, Google Drive, Dropbox\n\n"
        "**Limits:**\n"
        "Max size: 4 GB\n"
        "Max duration: unlimited (but >3h will take longer)\n\n"
        "_Questions? Just ask!_",
        parse_mode="markdown"
    )


if __name__ == "__main__":
    print("Digital Smarty v4.0 starting...")
    app.run()
