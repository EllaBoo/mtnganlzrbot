import os
import uuid
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
        css = "body{font-family:'Segoe UI',sans-serif;font-size:14px;line-height:1.7;color:#e4e4e7;background:#18181b;padding:40px;max-width:900px;margin:0 auto}h1{font-size:26px;color:#fafafa;border-bottom:3px solid #3b82f6;padding-bottom:12px}h2{font-size:20px;color:#fafafa;background:linear-gradient(135deg,#1e3a5f,#1e293b);padding:12px 16px;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-top:28px}h3{font-size:16px;color:#93c5fd;border-left:3px solid #60a5fa;padding-left:12px}strong{color:#fafafa}ul,ol{padding-left:24px}li{margin-bottom:8px}blockquote{background:#1e293b;border-left:4px solid #8b5cf6;padding:12px 16px;margin:16px 0;color:#c4b5fd;border-radius:0 8px 8px 0}hr{border:none;height:2px;background:linear-gradient(90deg,transparent,#3b82f6,transparent);margin:24px 0}.meta{color:#71717a;font-size:12px;margin-bottom:20px}"
    else:
        css = "body{font-family:'Segoe UI',sans-serif;font-size:14px;line-height:1.7;color:#1f2937;background:#fff;padding:40px;max-width:900px;margin:0 auto}h1{font-size:26px;color:#111827;border-bottom:3px solid #3b82f6;padding-bottom:12px}h2{font-size:20px;color:#111827;background:linear-gradient(135deg,#eff6ff,#dbeafe);padding:12px 16px;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;margin-top:28px}h3{font-size:16px;color:#1d4ed8;border-left:3px solid #60a5fa;padding-left:12px}strong{color:#111827}ul,ol{padding-left:24px}li{margin-bottom:8px}blockquote{background:#faf5ff;border-left:4px solid #8b5cf6;padding:12px 16px;margin:16px 0;color:#6b21a8;border-radius:0 8px 8px 0}hr{border:none;height:2px;background:linear-gradient(90deg,transparent,#3b82f6,transparent);margin:24px 0}.meta{color:#6b7280;font-size:12px;margin-bottom:20px}"
    
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
    theme_label = "Темная тема" if theme == "dark" else "Светлая тема"
    
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Резюме встречи</title><style>{css}</style></head><body><div class="meta">{date_str} | {theme_label}</div>{html}</body></html>'

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
        dg_key = DEEPGRAM_KEY.strip() if DEEPGRAM_KEY else None
        if not dg_key:
            return None, "DEEPGRAM_KEY не установлен!"
        
        headers = {"Authorization": f"Token {dg_key}"}
        params = f"model=nova-2&language={LANGUAGE}&diarize=true&smart_format=true&utterances=true&punctuate=true"
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        resp = http_requests.post(
            f"https://api.deepgram.com/v1/listen?{params}",
            headers=headers,
            data=file_data,
            timeout=1800
        )
        
        if resp.status_code == 401:
            return None, "Неверный Deepgram ключ!"
        if resp.status_code != 200:
            return None, f"Deepgram ошибка: {resp.status_code}"
        
        result = resp.json()
        parts = []
        speakers = set()
        
        if "results" in result and "utterances" in result["results"]:
            for u in result["results"]["utterances"]:
                spk = f"Спикер {u.get('speaker', '?')}"
                speakers.add(u.get('speaker', 0))
                parts.append(f"**{spk}:** {u.get('transcript', '')}")
        
        if not parts and "results" in result:
            ch = result["results"].get("channels", [])
            if ch and ch[0].get("alternatives"):
                parts = [ch[0]["alternatives"][0].get("transcript", "")]
        
        if not parts:
            return None, "Не удалось распознать речь"
        
        return {"transcript": "\n\n".join(parts), "duration": result.get("metadata", {}).get("duration", 0), "speakers": len(speakers) or 1}, None
    except Exception as e:
        return None, str(e)

PROMPT = """Ты — профессиональный аналитик встреч. Создай детальное структурированное резюме на русском языке:

# Резюме встречи

## Ключевые темы
Для каждой темы: название, суть, цитаты, итог.

## Позиции участников
Для каждого спикера: тезисы и цитаты.

## Принятые решения
Список решений с контекстом.

## Задачи
Список с ответственными.

## Открытые вопросы
Что не решено.

## Выводы
Топ-5 выводов.

Приводи цитаты из транскрипта."""

def analyze(transcript, duration, speakers):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": f"Транскрипт:\n\n{transcript[:45000]}"}],
            temperature=0.3, max_tokens=6000
        )
        result = resp.choices[0].message.content
        mins, secs = int(duration // 60), int(duration % 60)
        return f"{result}\n\n---\n**Статистика:** {mins} мин {secs} сек | {speakers} спикер(ов) | {len(transcript.split())} слов"
    except Exception as e:
        return f"Ошибка: {e}"

def custom_analyze(transcript, criteria):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": f"Извлеки из транскрипта по критериям:\n{criteria}\nПриводи цитаты."}, {"role": "user", "content": transcript[:45000]}],
            temperature=0.3, max_tokens=4000
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F310 HTML светлая", callback_data="html_light"), InlineKeyboardButton("\U0001F311 HTML тёмная", callback_data="html_dark")],
        [InlineKeyboardButton("\U0001F4C4 TXT файл", callback_data="txt")],
        [InlineKeyboardButton("\U0000270F\U0000FE0F Свой вопрос", callback_data="custom")],
        [InlineKeyboardButton("\U0001F4DC Транскрипт", callback_data="transcript")],
        [InlineKeyboardButton("\U0001F504 Перегенерировать", callback_data="regenerate")]
    ])

def help_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F4A1 Как работает?", callback_data="help")],
        [InlineKeyboardButton("\U0001F3A4 Форматы файлов", callback_data="formats")],
        [InlineKeyboardButton("\U00002728 Возможности", callback_data="features")]
    ])

def continue_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F310 HTML", callback_data="html_light_c"), InlineKeyboardButton("\U0001F311 HTML тёмная", callback_data="html_dark_c")],
        [InlineKeyboardButton("\U0000270F\U0000FE0F Ещё вопрос", callback_data="custom")],
        [InlineKeyboardButton("\U00002705 Готово", callback_data="done")]
    ])

app = Client("meeting_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH or "", bot_token=BOT_TOKEN or "")

@app.on_message(filters.command("start"))
async def start_cmd(client, msg):
    await msg.reply("\U0001F44B **Meeting Analyzer**\n\nОтправь аудио/видео встречи и получи:\n\n\U0001F4DD Резюме\n\U0001F465 Позиции участников\n\U00002705 Решения\n\U0001F4CC Задачи\n\n\U0001F3A4 **Жду файл!**", reply_markup=help_kb())

@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client, msg):
    if msg.document:
        mime = msg.document.mime_type or ""
        if not any(t in mime for t in ["audio", "video", "octet"]):
            return
    
    uid = msg.from_user.id
    cache = get_user_cache(uid)
    status = await msg.reply("\U0000231B Скачиваю файл...")
    
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = await msg.download(file_name=f"{tmp}/media")
            await status.edit_text("\U0001F3A4 Транскрибирую...")
            
            result, err = transcribe_file(path)
            if err:
                await status.edit_text(f"\U0000274C Ошибка: {err}")
                return
            
            cache["transcript"] = result["transcript"]
            cache["duration"] = result["duration"]
            cache["speakers"] = result["speakers"]
            
            await status.edit_text(f"\U00002705 Распознано! Спикеров: {result['speakers']}\n\n\U0001F9E0 Анализирую...")
            
            summary = analyze(result["transcript"], result["duration"], result["speakers"])
            cache["summary"] = summary
            
            await status.delete()
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await msg.reply(f"\U0001F4CB **Анализ встречи:**\n\n{preview}")
            await msg.reply("\U00002728 **Выбери формат:**", reply_markup=main_kb())
    except Exception as e:
        await status.edit_text(f"\U0000274C Ошибка: {e}")

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
                await cb.answer("\U0000274C Сначала отправь файл!", show_alert=True)
                return
            
            await cb.answer("\U0000231B Генерирую...")
            path = save_html(cache[key], theme)
            theme_name = "тёмная" if theme == "dark" else "светлая"
            await cb.message.reply_document(path, caption=f"\U0001F310 HTML ({theme_name} тема)")
            os.remove(path)
            await cb.message.reply("\U00002728 Ещё что-нибудь?", reply_markup=main_kb())
        
        elif data == "txt":
            if "summary" not in cache:
                await cb.answer("\U0000274C Сначала отправь файл!", show_alert=True)
                return
            await cb.answer("\U0000231B")
            path = save_txt(cache["summary"])
            await cb.message.reply_document(path, caption="\U0001F4C4 TXT файл")
            os.remove(path)
            await cb.message.reply("\U00002728 Ещё?", reply_markup=main_kb())
        
        elif data == "custom":
            cache["stage"] = "waiting_criteria"
            await cb.answer()
            await cb.message.edit_text("\U0000270F\U0000FE0F **Введи свой вопрос:**\n\nПримеры:\n\U00002022 Какие бюджеты обсуждались?\n\U00002022 Что сказал X про Y?\n\U00002022 Список рисков")
        
        elif data == "transcript":
            if "transcript" not in cache:
                await cb.answer("\U0000274C Нет данных!", show_alert=True)
                return
            await cb.answer()
            t = cache["transcript"]
            for i in range(0, len(t), 4000):
                await cb.message.reply(t[i:i+4000])
            await cb.message.reply("\U00002728 Ещё?", reply_markup=main_kb())
        
        elif data == "regenerate":
            if "transcript" not in cache:
                await cb.answer("\U0000274C Нет данных!", show_alert=True)
                return
            await cb.answer("\U0001F504")
            await cb.message.edit_text("\U0001F9E0 Анализирую заново...")
            summary = analyze(cache["transcript"], cache.get("duration", 0), cache.get("speakers", 1))
            cache["summary"] = summary
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await cb.message.reply(f"\U0001F4CB **Новый анализ:**\n\n{preview}")
            await cb.message.reply("\U00002728 Формат:", reply_markup=main_kb())
        
        elif data == "done":
            await cb.answer("\U00002705")
            await cb.message.edit_text("\U00002705 Готово!\n\n\U0001F3A4 Отправь новый файл!")
        
        elif data == "help":
            await cb.answer()
            await cb.message.edit_text("\U0001F4A1 **Как работает:**\n\n1\U0000FE0F\U000020E3 Отправь аудио/видео\n2\U0000FE0F\U000020E3 Жди транскрибацию\n3\U0000FE0F\U000020E3 Получи анализ\n4\U0000FE0F\U000020E3 Скачай HTML/TXT\n5\U0000FE0F\U000020E3 Задавай вопросы!", reply_markup=help_kb())
        
        elif data == "formats":
            await cb.answer()
            await cb.message.edit_text("\U0001F3A4 **Форматы:**\n\n\U0001F3B5 MP3, WAV, OGG, M4A\n\U0001F3AC MP4, MOV, AVI, MKV\n\U0001F399 Голосовые Telegram\n\n\U0001F4E6 До 2GB (Premium 4GB)", reply_markup=help_kb())
        
        elif data == "features":
            await cb.answer()
            await cb.message.edit_text("\U00002728 **Возможности:**\n\n\U0001F4DD Резюме встречи\n\U0001F465 Позиции участников\n\U00002705 Решения\n\U0001F4CC Задачи\n\U00002753 Свои вопросы\n\n\U0001F4E5 Экспорт: HTML, TXT", reply_markup=help_kb())
    
    except Exception as e:
        await cb.message.reply(f"\U0000274C Ошибка: {e}")

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, msg):
    uid = msg.from_user.id
    cache = get_user_cache(uid)
    
    if cache.get("stage") == "waiting_criteria" and "transcript" in cache:
        status = await msg.reply("\U0001F9E0 Анализирую...")
        try:
            result = custom_analyze(cache["transcript"], msg.text)
            cache["custom_result"] = result
            cache["stage"] = None
            await status.delete()
            await msg.reply(f"\U0001F4CB **Результат:**\n\n{result}")
            await msg.reply("\U00002728 Сохранить?", reply_markup=continue_kb())
        except Exception as e:
            await status.edit_text(f"\U0000274C Ошибка: {e}")
    else:
        await msg.reply("\U0001F3A4 Отправь аудио или видео для анализа!", reply_markup=help_kb())

if __name__ == "__main__":
    print("Starting bot...")
    app.run()
