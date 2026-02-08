import os
import uuid
import random
import tempfile
import re
import requests as http_requests
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI

API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DEEPGRAM_KEY = os.environ.get('DEEPGRAM_KEY')
OPENAI_KEY = os.environ.get('OPENAI_KEY')
LANGUAGE = os.environ.get('LANGUAGE', 'ru')

user_cache = {}

def get_user_cache(user_id):
    if user_id not in user_cache:
        user_cache[user_id] = {}
    return user_cache[user_id]

def generate_html(content, theme="light"):
    if theme == "dark":
        css = "body{font-family:'Segoe UI',sans-serif;font-size:14px;line-height:1.7;color:#e4e4e7;background:#18181b;padding:40px;max-width:900px;margin:0 auto}h1{font-size:26px;color:#fafafa;border-bottom:3px solid #3b82f6;padding-bottom:12px}h2{font-size:20px;color:#fafafa;background:linear-gradient(135deg,#1e3a5f,#1e293b);padding:12px 16px;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-top:28px}h3{font-size:16px;color:#93c5fd;border-left:3px solid #60a5fa;padding-left:12px}strong{color:#fafafa}ul,ol{padding-left:24px}li{margin-bottom:8px}blockquote{background:#1e293b;border-left:4px solid #8b5cf6;padding:12px 16px;margin:16px 0;color:#c4b5fd;border-radius:0 8px 8px 0}hr{border:none;height:2px;background:linear-gradient(90deg,transparent,#3b82f6,transparent);margin:24px 0}table{width:100%;border-collapse:collapse;background:#1e293b;border-radius:8px;overflow:hidden}th{background:#3b82f6;color:white;padding:10px 14px;text-align:left}td{padding:10px 14px;border-bottom:1px solid #334155}.meta{color:#71717a;font-size:12px;margin-bottom:20px}"
    else:
        css = "body{font-family:'Segoe UI',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;background:#fff;padding:40px;max-width:900px;margin:0 auto}h1{font-size:26px;color:#111827;border-bottom:3px solid #3b82f6;padding-bottom:12px}h2{font-size:20px;color:#111827;background:linear-gradient(135deg,#eff6ff,#dbeafe);padding:12px 16px;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-top:28px}h3{font-size:16px;color:#1d4ed8;border-left:3px solid #60a5fa;padding-left:12px}strong{color:#111827}ul,ol{padding-left:24px}li{margin-bottom:8px}blockquote{background:#faf5ff;border-left:4px solid #8b5cf6;padding:12px 16px;margin:16px 0;color:#6b21a8;border-radius:0 8px 8px 0}hr{border:none;height:2px;background:linear-gradient(90deg,transparent,#3b82f6,transparent);margin:24px 0}table{width:100%;border-collapse:collapse;box-shadow:0 1px 3px rgba(0,0,0,0.1);border-radius:8px;overflow:hidden}th{background:#3b82f6;color:white;padding:10px 14px;text-align:left}td{padding:10px 14px;border-bottom:1px solid #e5e7eb}tr:hover{background:#f9fafb}.meta{color:#6b7280;font-size:12px;margin-bottom:20px}"
    
    html = content
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>\n?)+', r'<ul>\g<0></ul>', html)
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = f'<p>{html}</p>'
    html = re.sub(r'<p>(<h[123]>)', r'\1', html)
    html = re.sub(r'(</h[123]>)</p>', r'\1', html)
    html = re.sub(r'<p>(<ul>)', r'\1', html)
    html = re.sub(r'(</ul>)</p>', r'\1', html)
    html = re.sub(r'<p>(<hr>)</p>', r'\1', html)
    html = re.sub(r'<p>(<blockquote>)', r'\1', html)
    html = re.sub(r'(</blockquote>)</p>', r'\1', html)
    html = html.replace('<p></p>', '')
    
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    theme_label = "Dark" if theme == "dark" else "Light"
    
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Meeting Summary</title><style>{css}</style></head><body><div class="meta">Date: {date_str} | Theme: {theme_label}</div>{html}</body></html>'

def save_html(content, theme):
    html = generate_html(content, theme)
    path = f"/tmp/meeting_{uuid.uuid4().hex[:8]}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return path

def save_txt(content):
    path = f"/tmp/meeting_{uuid.uuid4().hex[:8]}.txt"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

def transcribe_file(file_path):
    try:
        headers = {"Authorization": f"Token {DEEPGRAM_KEY}"}
        params = f"model=nova-2&language={LANGUAGE}&diarize=true&smart_format=true&utterances=true&punctuate=true"
        
        with open(file_path, "rb") as f:
            resp = http_requests.post(f"https://api.deepgram.com/v1/listen?{params}", headers=headers, data=f, timeout=1800)
        
        if resp.status_code != 200:
            return None, f"Deepgram error: {resp.status_code}"
        
        result = resp.json()
        parts = []
        speakers = set()
        
        if "results" in result and "utterances" in result["results"]:
            for u in result["results"]["utterances"]:
                spk = f"Speaker {u.get('speaker', '?')}"
                speakers.add(u.get('speaker', 0))
                parts.append(f"**{spk}:** {u.get('transcript', '')}")
        
        if not parts and "results" in result:
            ch = result["results"].get("channels", [])
            if ch and ch[0].get("alternatives"):
                parts = [ch[0]["alternatives"][0].get("transcript", "")]
        
        if not parts:
            return None, "Empty transcript"
        
        return {"transcript": "\n\n".join(parts), "duration": result.get("metadata", {}).get("duration", 0), "speakers": len(speakers) or 1}, None
    except Exception as e:
        return None, str(e)

PROMPT = """You are a meeting analyst. Create a detailed summary in Russian:

# Meeting Summary

## Key Topics
For each: title, essence, quotes, outcome.

## Participant Positions  
For each speaker: points, quotes.

## Decisions Made
List with context.

## Tasks
List with responsible persons.

## Open Questions
What was not resolved.

## Conclusions
Top-5 conclusions.

Be specific, provide quotes."""

def analyze(transcript, duration, speakers):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        text = transcript[:45000]
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": f"Transcript:\n\n{text}"}],
            temperature=0.3, max_tokens=6000
        )
        result = resp.choices[0].message.content
        mins, secs = int(duration // 60), int(duration % 60)
        return f"{result}\n\n---\n**Stats:** {mins} min {secs} sec | {speakers} speaker(s) | {len(transcript.split())} words"
    except Exception as e:
        return f"Analysis error: {e}"

def custom_analyze(transcript, criteria):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"Extract from transcript by criteria:\n{criteria}\nProvide quotes."}, {"role": "user", "content": transcript[:45000]}],
            temperature=0.3, max_tokens=4000
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("HTML Light", callback_data="html_light"), InlineKeyboardButton("HTML Dark", callback_data="html_dark")],
        [InlineKeyboardButton("TXT", callback_data="txt")],
        [InlineKeyboardButton("Custom Query", callback_data="custom")],
        [InlineKeyboardButton("Transcript", callback_data="transcript")],
        [InlineKeyboardButton("Regenerate", callback_data="regenerate")]
    ])

def help_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("How it works?", callback_data="help")],
        [InlineKeyboardButton("File formats", callback_data="formats")],
        [InlineKeyboardButton("Features", callback_data="features")]
    ])

def continue_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("HTML", callback_data="html_light_c"), InlineKeyboardButton("HTML Dark", callback_data="html_dark_c")],
        [InlineKeyboardButton("Another question", callback_data="custom")],
        [InlineKeyboardButton("Done", callback_data="done")]
    ])

app = Client("meeting_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH or "", bot_token=BOT_TOKEN or "")

@app.on_message(filters.command("start"))
async def start_cmd(client, msg):
    await msg.reply("Meeting Analyzer\n\nSend audio/video to get:\n- Summary\n- Participant positions\n- Decisions\n- Tasks\n\nWaiting for file!", reply_markup=help_kb())

@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client, msg):
    if msg.document:
        mime = msg.document.mime_type or ""
        if not any(t in mime for t in ["audio", "video", "octet"]):
            return
    
    uid = msg.from_user.id
    cache = get_user_cache(uid)
    status = await msg.reply("Downloading...")
    
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = await msg.download(file_name=f"{tmp}/media")
            await status.edit_text("Transcribing...")
            
            result, err = transcribe_file(path)
            if err:
                await status.edit_text(f"Error: {err}")
                return
            
            cache["transcript"] = result["transcript"]
            cache["duration"] = result["duration"]
            cache["speakers"] = result["speakers"]
            
            await status.edit_text(f"Done! Speakers: {result['speakers']}\n\nAnalyzing...")
            
            summary = analyze(result["transcript"], result["duration"], result["speakers"])
            cache["summary"] = summary
            
            await status.delete()
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await msg.reply(f"Analysis:\n\n{preview}")
            await msg.reply("Choose format:", reply_markup=main_kb())
    except Exception as e:
        await status.edit_text(f"Error: {e}")

@app.on_callback_query()
async def callback(client, cb):
    uid = cb.from_user.id
    data = cb.data
    cache = get_user_cache(uid)
    
    try:
        if data.startswith("html_"):
            parts = data.split("_")
            theme = parts[1]
            is_custom = len(parts) > 2
            key = "custom_result" if is_custom else "summary"
            
            if key not in cache:
                await cb.answer("Send file first!", show_alert=True)
                return
            
            await cb.answer("Generating...")
            path = save_html(cache[key], theme)
            await cb.message.reply_document(path, caption=f"HTML ({theme})")
            os.remove(path)
            await cb.message.reply("More?", reply_markup=main_kb())
        
        elif data == "txt":
            if "summary" not in cache:
                await cb.answer("Send file first!", show_alert=True)
                return
            await cb.answer("...")
            path = save_txt(cache["summary"])
            await cb.message.reply_document(path, caption="TXT")
            os.remove(path)
            await cb.message.reply("More?", reply_markup=main_kb())
        
        elif data == "custom":
            cache["stage"] = "waiting_criteria"
            await cb.answer()
            await cb.message.edit_text("Enter your question:\n\nExamples:\n- What budgets?\n- What did X say about Y?\n- List of risks")
        
        elif data == "transcript":
            if "transcript" not in cache:
                await cb.answer("No data!", show_alert=True)
                return
            await cb.answer()
            t = cache["transcript"]
            for i in range(0, len(t), 4000):
                await cb.message.reply(t[i:i+4000])
            await cb.message.reply("More?", reply_markup=main_kb())
        
        elif data == "regenerate":
            if "transcript" not in cache:
                await cb.answer("No data!", show_alert=True)
                return
            await cb.answer("Regenerating...")
            await cb.message.edit_text("Analyzing again...")
            summary = analyze(cache["transcript"], cache.get("duration", 0), cache.get("speakers", 1))
            cache["summary"] = summary
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await cb.message.reply(f"New analysis:\n\n{preview}")
            await cb.message.reply("Format:", reply_markup=main_kb())
        
        elif data == "done":
            await cb.answer("Done!")
            await cb.message.edit_text("Done!\n\nSend new file!")
        
        elif data == "help":
            await cb.answer()
            await cb.message.edit_text("How it works:\n\n1. Send audio/video\n2. Wait for transcription\n3. Get analysis\n4. Download HTML\n5. Ask custom questions!", reply_markup=help_kb())
        
        elif data == "formats":
            await cb.answer()
            await cb.message.edit_text("Formats:\n\nMP3, WAV, OGG, M4A\nMP4, MOV, AVI, MKV\nTelegram voice messages\n\nUp to 2GB (Premium 4GB)", reply_markup=help_kb())
        
        elif data == "features":
            await cb.answer()
            await cb.message.edit_text("Features:\n\n- Meeting summary\n- Participant positions\n- Decisions\n- Tasks\n- Custom questions\n\nExport: HTML (2 themes), TXT", reply_markup=help_kb())
    
    except Exception as e:
        await cb.message.reply(f"Error: {e}")

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, msg):
    uid = msg.from_user.id
    cache = get_user_cache(uid)
    
    if cache.get("stage") == "waiting_criteria" and "transcript" in cache:
        status = await msg.reply("Analyzing...")
        try:
            result = custom_analyze(cache["transcript"], msg.text)
            cache["custom_result"] = result
            cache["stage"] = None
            await status.delete()
            await msg.reply(f"Result:\n\n{result}")
            await msg.reply("Save?", reply_markup=continue_kb())
        except Exception as e:
            await status.edit_text(f"Error: {e}")
    else:
        await msg.reply("Send audio/video file to analyze!", reply_markup=help_kb())

if __name__ == "__main__":
    print("Starting bot...")
    app.run()
