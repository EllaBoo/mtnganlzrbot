import os
import asyncio
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from processor import Processor
from batch_processor import BatchProcessor

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
batch_processor = BatchProcessor()
user_states = {}

WELCOME_MESSAGE = """**Digital Smarty v4.1** 🎯

Hey! I'm your digital meeting analyst.

Send me audio or video recordings (MP3, M4A, WAV, MP4, MOV, WebM) and I'll give you:

- **Structured summary** with topics, decisions and tasks
- **Reality Check** - critical analysis of agreements
- **PDF report** - beautiful, for sharing
- **Text transcript** - full conversation text

✨ **NEW: Batch Mode** - send up to 5 files and get ONE combined result!

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

# New keyboard for single/batch choice
def get_mode_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📄 Process this file", callback_data="mode_single"),
        ],
        [
            InlineKeyboardButton("📚 Collect multiple (up to 5)", callback_data="mode_batch")
        ]
    ])

# Keyboard for batch mode
def get_batch_keyboard(count: int):
    buttons = []
    if count < 5:
        buttons.append([InlineKeyboardButton(f"➕ Add more ({count}/5)", callback_data="batch_add")])
    buttons.append([InlineKeyboardButton(f"✅ Process all {count} files", callback_data="batch_process")])
    buttons.append([InlineKeyboardButton("❌ Cancel batch", callback_data="batch_cancel")])
    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply(WELCOME_MESSAGE, parse_mode="markdown")


@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def file_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is in batch collection mode
    if user_id in user_states and user_states[user_id].get("status") == "collecting_batch":
        # Add file to batch
        batch_files = user_states[user_id].get("batch_files", [])
        
        if len(batch_files) >= 5:
            await message.reply("Maximum 5 files reached! Press 'Process all' to continue.")
            return
        
        batch_files.append({"file_message": message})
        user_states[user_id]["batch_files"] = batch_files
        
        await message.reply(
            f"✅ File {len(batch_files)}/5 added!\n\nSend more files or press button below:",
            reply_markup=get_batch_keyboard(len(batch_files))
        )
        return
    
    # New file - offer choice
    user_states[user_id] = {
        "file_message": message,
        "status": "waiting_mode"
    }
    
    await message.reply(
        "Got it! What would you like to do?",
        reply_markup=get_mode_keyboard()
    )


@app.on_message(filters.text & ~filters.command(["start", "help"]))
async def text_handler(client: Client, message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    
    if text.startswith(("http://", "https://", "www.")):
        # Check if user is in batch collection mode
        if user_id in user_states and user_states[user_id].get("status") == "collecting_batch":
            batch_files = user_states[user_id].get("batch_files", [])
            
            if len(batch_files) >= 5:
                await message.reply("Maximum 5 files reached! Press 'Process all' to continue.")
                return
            
            batch_files.append({"url": text})
            user_states[user_id]["batch_files"] = batch_files
            
            await message.reply(
                f"✅ Link {len(batch_files)}/5 added!\n\nSend more files/links or press button below:",
                reply_markup=get_batch_keyboard(len(batch_files))
            )
            return
        
        # New link - offer choice
        user_states[user_id] = {
            "url": text,
            "status": "waiting_mode"
        }
        
        await message.reply(
            "Link received! What would you like to do?",
            reply_markup=get_mode_keyboard()
        )
    else:
        await message.reply(
            "Hmm, I didn't understand. Send me an audio/video file or a link to it.\n\n"
            "Supported: MP3, M4A, WAV, MP4, MOV, WebM, and cloud storage links."
        )


# Handler for mode selection (single/batch)
@app.on_callback_query(filters.regex(r"^mode_"))
async def mode_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.replace("mode_", "")
    
    if user_id not in user_states:
        await callback.answer("Session expired. Please send the file again.", show_alert=True)
        return
    
    state = user_states[user_id]
    
    if mode == "single":
        # Single file mode - proceed to language selection
        state["status"] = "waiting_language"
        await callback.answer("Single file mode")
        await callback.message.edit_text(
            "Great! What language do you want the result in?",
            reply_markup=LANGUAGE_KEYBOARD
        )
    
    elif mode == "batch":
        # Batch mode - start collecting
        await callback.answer("Batch mode activated!")
        
        # Initialize batch with first file
        batch_files = []
        if "file_message" in state:
            batch_files.append({"file_message": state["file_message"]})
        elif "url" in state:
            batch_files.append({"url": state["url"]})
        
        user_states[user_id] = {
            "status": "collecting_batch",
            "batch_files": batch_files
        }
        
        await callback.message.edit_text(
            f"📚 **Batch Mode**\n\n"
            f"File 1/5 added!\n\n"
            f"Send more files or links (up to 5 total).\n"
            f"When ready, press 'Process all'.",
            reply_markup=get_batch_keyboard(len(batch_files))
        )


# Handler for batch actions
@app.on_callback_query(filters.regex(r"^batch_"))
async def batch_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.replace("batch_", "")
    
    if user_id not in user_states:
        await callback.answer("Session expired. Please start again.", show_alert=True)
        return
    
    state = user_states[user_id]
    
    if action == "add":
        await callback.answer("Send more files or links!")
        return
    
    elif action == "cancel":
        del user_states[user_id]
        await callback.answer("Batch cancelled")
        await callback.message.edit_text("Batch cancelled. Send a new file to start again.")
        return
    
    elif action == "process":
        batch_files = state.get("batch_files", [])
        if not batch_files:
            await callback.answer("No files to process!", show_alert=True)
            return
        
        state["status"] = "waiting_language_batch"
        await callback.answer("Select language")
        await callback.message.edit_text(
            f"📚 **{len(batch_files)} files ready**\n\n"
            f"What language do you want the combined result in?",
            reply_markup=LANGUAGE_KEYBOARD
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
    
    # Check if batch mode
    if state.get("status") == "waiting_language_batch":
        batch_files = state.get("batch_files", [])
        await callback.message.edit_text(
            f"🚀 Processing {len(batch_files)} files...\n\n"
            f"Result language: {lang_names.get(language, language)}\n\n"
            f"This may take a while. Please wait..."
        )
        asyncio.create_task(process_batch_files(client, callback.message, state, language, user_id))
    else:
        # Single file mode (original behavior)
        await callback.message.edit_text(f"Processing started...\n\nResult language: {lang_names.get(language, language)}")
        asyncio.create_task(process_file(client, callback.message, state, language, user_id))


# NEW: Batch processing function
async def process_batch_files(client: Client, status_message: Message, state: dict, language: str, user_id: int):
    try:
        temp_dir = Path(Config.TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        async def update_status(text: str):
            try:
                await status_message.edit_text(text)
            except:
                pass
        
        batch_files = state.get("batch_files", [])
        file_paths = []
        
        # Download all files first
        for i, item in enumerate(batch_files, 1):
            if "file_message" in item:
                file_message = item["file_message"]
                await update_status(f"Downloading file {i}/{len(batch_files)}...")
                
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
                    continue
                
                file_path = await client.download_media(
                    file_message,
                    file_name=str(temp_dir / f"{user_id}_{file.file_id[:8]}")
                )
                file_paths.append(file_path)
                
            elif "url" in item:
                await update_status(f"Downloading from link {i}/{len(batch_files)}...")
                file_path = await processor.download_file(item["url"], update_status)
                file_paths.append(file_path)
        
        if not file_paths:
            await update_status("Error: no files were downloaded")
            return
        
        # Process batch
        result = await batch_processor.process_batch(file_paths, language, update_status)
        
        if not result["success"]:
            await update_status(f"Processing error: {result['error']}")
            return
        
        await update_status("Sending combined results...")
        
        analysis = result["analysis"]
        
        # Send summary
        summary_text = format_summary_for_telegram(analysis)
        
        # Add batch info to summary
        batch_info = analysis.get("batch_info", {})
        if batch_info:
            summary_text = f"📚 **Combined from {batch_info.get('total_files', 0)} files**\n\n" + summary_text
        
        await status_message.reply(summary_text, parse_mode="markdown")
        
        # Send reports
        await status_message.reply_document(
            document=result["pdf_path"],
            caption="📄 Combined PDF Report"
        )
        
        await status_message.reply_document(
            document=result["html_path"],
            caption="🌐 Combined HTML Report"
        )
        
        await status_message.reply_document(
            document=result["transcript_path"],
            caption="📝 Combined Full Transcript"
        )
        
        await status_message.reply(
            f"**Done!** ✨\n\n"
            f"Processed {result.get('files_processed', 0)} files into one report.\n\n"
            f"Want to know more? I can:\n"
            f"- Dive deeper into a specific topic\n"
            f"- Generate an email summary for your team\n"
            f"- Redo the report in another language\n\n"
            f"_Just tell me what you need!_",
            parse_mode="markdown"
        )
        
        try:
            await status_message.delete()
        except:
            pass
        
        # Cleanup
        for fp in file_paths:
            try:
                os.remove(fp)
            except:
                pass
        try:
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


# Original single file processing (UNCHANGED)
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
        "**Single file:**\n"
        "1. Send an audio/video file or link\n"
        "2. Choose 'Process this file'\n"
        "3. Select result language\n"
        "4. Get summary, PDF and transcript\n\n"
        "**Multiple files (NEW!):**\n"
        "1. Send first file\n"
        "2. Choose 'Collect multiple'\n"
        "3. Send up to 5 files/links\n"
        "4. Press 'Process all'\n"
        "5. Get ONE combined result!\n\n"
        "**Supported formats:**\n"
        "Audio: MP3, M4A, WAV, OGG, FLAC\n"
        "Video: MP4, MOV, WebM, AVI, MKV\n"
        "Links: direct URLs, Google Drive, Dropbox\n\n"
        "**Limits:**\n"
        "Max size: 4 GB per file\n"
        "Max files in batch: 5\n"
        "Max duration: unlimited (but >3h will take longer)\n\n"
        "_Questions? Just ask!_",
        parse_mode="markdown"
    )


if __name__ == "__main__":
    print("Digital Smarty v4.1 starting...")
    app.run()
