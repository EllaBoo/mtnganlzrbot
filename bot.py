import os
import uuid
import tempfile
import markdown
import requests
from datetime import datetime
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI
from weasyprint import HTML, CSS

# === CONFIGURATION ===
API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DEEPGRAM_KEY = os.environ.get('DEEPGRAM_KEY')
OPENAI_KEY = os.environ.get('OPENAI_KEY')
LANGUAGE = os.environ.get('LANGUAGE', 'ru')

# === USER CACHE ===
user_cache = {}

def get_user_cache(user_id: int) -> dict:
    if user_id not in user_cache:
        user_cache[user_id] = {}
    return user_cache[user_id]

# === CSS STYLES ===
def get_css_styles(theme: str = "light") -> str:
    if theme == "dark":
        return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11pt; line-height: 1.6; color: #e4e4e7; background: #18181b; padding: 40px 50px;
}
h1 { font-size: 24pt; font-weight: 700; color: #fafafa; margin-bottom: 8px; padding-bottom: 16px; border-bottom: 3px solid #3b82f6; }
h2 { font-size: 16pt; font-weight: 600; color: #fafafa; margin-top: 32px; margin-bottom: 16px; padding: 12px 16px; background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; }
h3 { font-size: 13pt; font-weight: 600; color: #93c5fd; margin-top: 24px; margin-bottom: 12px; padding-left: 12px; border-left: 3px solid #60a5fa; }
h4 { font-size: 11pt; font-weight: 600; color: #a5b4fc; margin-top: 16px; margin-bottom: 8px; }
p { margin-bottom: 12px; text-align: justify; }
strong { color: #fafafa; font-weight: 600; }
ul, ol { margin: 12px 0; padding-left: 24px; }
li { margin-bottom: 6px; }
li::marker { color: #60a5fa; }
blockquote { margin: 16px 0; padding: 16px 20px; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-left: 4px solid #8b5cf6; border-radius: 0 8px 8px 0; font-style: italic; color: #c4b5fd; }
blockquote p { margin: 0; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 10pt; background: #1e293b; border-radius: 8px; overflow: hidden; }
th { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; font-weight: 600; padding: 12px 16px; text-align: left; }
td { padding: 10px 16px; border-bottom: 1px solid #334155; }
tr:last-child td { border-bottom: none; }
tr:hover { background: #334155; }
hr { border: none; height: 2px; background: linear-gradient(90deg, transparent, #3b82f6, transparent); margin: 32px 0; }
code { background: #1e293b; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 10pt; color: #fbbf24; }
@page { size: A4; margin: 20mm; }
"""
    else:
        return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11pt; line-height: 1.6; color: #1f2937; background: #ffffff; padding: 40px 50px;
}
h1 { font-size: 24pt; font-weight: 700; color: #111827; margin-bottom: 8px; padding-bottom: 16px; border-bottom: 3px solid #3b82f6; }
h2 { font-size: 16pt; font-weight: 600; color: #111827; margin-top: 32px; margin-bottom: 16px; padding: 12px 16px; background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; }
h3 { font-size: 13pt; font-weight: 600; color: #1d4ed8; margin-top: 24px; margin-bottom: 12px; padding-left: 12px; border-left: 3px solid #60a5fa; }
h4 { font-size: 11pt; font-weight: 600; color: #4f46e5; margin-top: 16px; margin-bottom: 8px; }
p { margin-bottom: 12px; text-align: justify; }
strong { color: #111827; font-weight: 600; }
ul, ol { margin: 12px 0; padding-left: 24px; }
li { margin-bottom: 6px; }
li::marker { color: #3b82f6; }
blockquote { margin: 16px 0; padding: 16px 20px; background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border-left: 4px solid #8b5cf6; border-radius: 0 8px 8px 0; font-style: italic; color: #6b21a8; }
blockquote p { margin: 0; }
table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 10pt; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; font-weight: 600; padding: 12px 16px; text-align: left; }
td { padding: 10px 16px; border-bottom: 1px solid #e5e7eb; }
tr:last-child td { border-bottom: none; }
tr:hover { background: #f9fafb; }
hr { border: none; height: 2px; background: linear-gradient(90deg, transparent, #3b82f6, transparent); margin: 32px 0; }
code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 10pt; color: #dc2626; }
@page { size: A4; margin: 20mm; }
"""

# === PDF/HTML GENERATION ===
def generate_pdf(markdown_content: str, theme: str = "light", title: str = "Meeting Summary") -> str:
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    html_content = md.convert(markdown_content)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    theme_label = "Тёмная" if theme == "dark" else "Светлая"
    meta_color = "#71717a" if theme == "dark" else "#6b7280"
    
    full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>{get_css_styles(theme)}</style>
</head>
<body>
    <div style="color: {meta_color}; font-size: 10pt; margin-bottom: 24px;">
        📅 Сгенерировано: {date_str} | 🎨 Тема: {theme_label}
    </div>
    {html_content}
</body>
</html>"""
    
    pdf_path = f"/tmp/meeting_summary_{uuid.uuid4().hex[:8]}.pdf"
    HTML(string=full_html).write_pdf(pdf_path)
    return pdf_path

def generate_html(markdown_content: str, theme: str = "light", title: str = "Meeting Summary") -> str:
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    html_content = md.convert(markdown_content)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    theme_label = "Тёмная" if theme == "dark" else "Светлая"
    meta_color = "#71717a" if theme == "dark" else "#6b7280"
    
    full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {get_css_styles(theme)}
        .collapsible {{ cursor: pointer; user-select: none; }}
        .collapsible:hover {{ opacity: 0.8; }}
        .collapsible::after {{ content: ' ▼'; font-size: 8pt; opacity: 0.5; }}
        .collapsible.collapsed::after {{ content: ' ▶'; }}
        .content {{ max-height: 5000px; overflow: hidden; transition: max-height 0.3s ease; }}
        .content.collapsed {{ max-height: 0; }}
    </style>
</head>
<body>
    <div style="color: {meta_color}; font-size: 10pt; margin-bottom: 24px;">
        📅 Сгенерировано: {date_str} | 🎨 Тема: {theme_label}
    </div>
    {html_content}
    <script>
        document.querySelectorAll('h2, h3').forEach(heading => {{
            heading.classList.add('collapsible');
            heading.addEventListener('click', function() {{
                this.classList.toggle('collapsed');
                let content = this.nextElementSibling;
                while(content && !content.matches('h2, h3')) {{
                    content.classList.toggle('collapsed');
                    content = content.nextElementSibling;
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    html_path = f"/tmp/meeting_summary_{uuid.uuid4().hex[:8]}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    return html_path

# === TRANSCRIPTION ===
def transcribe_file(file_path: str) -> tuple:
    headers = {"Authorization": f"Token {DEEPGRAM_KEY}"}
    params = f"model=nova-2&language={LANGUAGE}&diarize=true&smart_format=true&utterances=true&punctuate=true"
    url = f"https://api.deepgram.com/v1/listen?{params}"
    
    with open(file_path, "rb") as f:
        resp = requests.post(url, headers=headers, data=f, timeout=1800)
    
    if resp.status_code != 200:
        return None, f"Deepgram error: {resp.text}"
    
    result = resp.json()
    transcript_parts = []
    speakers_set = set()
    
    if "results" in result and "utterances" in result["results"]:
        for utt in result["results"]["utterances"]:
            speaker = f"Speaker {utt.get('speaker', '?')}"
            speakers_set.add(utt.get('speaker', 0))
            transcript_parts.append(f"**{speaker}:** {utt.get('transcript', '')}")
    
    if not transcript_parts and "results" in result:
        channels = result["results"].get("channels", [])
        if channels and channels[0].get("alternatives"):
            transcript_parts = [channels[0]["alternatives"][0].get("transcript", "")]
    
    duration = result.get("metadata", {}).get("duration", 0)
    return {
        "transcript": "\n\n".join(transcript_parts),
        "duration": duration,
        "speakers": len(speakers_set) if speakers_set else 1
    }, None

# === GPT ANALYSIS ===
ANALYSIS_PROMPT = """Ты — профессиональный аналитик деловых встреч. Создай ДЕТАЛЬНОЕ структурированное резюме.

# Резюме встречи

---

## Ключевые темы (с детализацией)

Для КАЖДОЙ темы создай подраздел:

### Тема 1: [Название]
**Суть:** [2-3 предложения]
**Контекст:** [Почему поднялась тема]
**Что обсуждалось:**
- [Пункт 1]
- [Пункт 2]
**Ключевые цитаты:** 
> "[Цитата]" — Speaker X
**Итог по теме:** [Решение/открытый вопрос]

---

## Позиции участников

### Speaker 0
**Роль:** [Если понятно]
**Основные тезисы:**
- [Тезис 1]
- [Тезис 2]
**Характерные высказывания:**
> "[Цитата]"

---

## Принятые решения

| # | Решение | Контекст | Ответственный | Срок |
|---|---------|----------|---------------|------|

### Решение 1: [Название]
- **Что решили:** [Детали]
- **Аргументы за:** [Почему]
- **Возражения:** [Если были]

---

## Задачи и следующие шаги

| # | Задача | Ответственный | Дедлайн | Приоритет |
|---|--------|---------------|---------|-----------|

---

## Открытые вопросы и риски

### Нерешённые вопросы:
1. **[Вопрос]** — [Почему не решили]

### Риски:
| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|

---

## Reality Check

### Что хорошо:
- [Позитив]

### Что вызывает вопросы:
- [Проблема]

### Скрытые течения:
- [Между строк]

---

## Главные выводы

1. **[Вывод 1]** — [Объяснение]
2. **[Вывод 2]** — [Объяснение]

---

## Полный список затронутых тем

| # | Тема | Глубина | Статус |
|---|------|---------|--------|
| 1 | [Тема] | Подробно/Кратко/Упоминание | Решено/Открыто |
"""

def analyze_transcript(transcript: str, duration: float, speakers: int) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": f"Проанализируй транскрипт:\n\n{transcript[:50000]}"}
        ],
        temperature=0.3,
        max_tokens=8000
    )
    
    analysis = resp.choices[0].message.content
    duration_str = f"{int(duration // 60)} мин {int(duration % 60)} сек"
    
    return f"""{analysis}

---
**Статистика:** {duration_str} | {speakers} участник(ов) | {len(transcript.split())} слов"""

def custom_analysis(transcript: str, user_criteria: str) -> str:
    client = OpenAI(api_key=OPENAI_KEY)
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Извлеки из транскрипта информацию по критериям:\n{user_criteria}\nБудь детальным, приводи цитаты."},
            {"role": "user", "content": f"ТРАНСКРИПТ:\n{transcript[:50000]}"}
        ],
        temperature=0.3,
        max_tokens=6000
    )
    return resp.choices[0].message.content

# === KEYBOARDS ===
def get_after_analysis_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF светлый", callback_data="pdf_light"),
         InlineKeyboardButton("🌙 PDF тёмный", callback_data="pdf_dark")],
        [InlineKeyboardButton("🌐 HTML светлый", callback_data="html_light"),
         InlineKeyboardButton("🌑 HTML тёмный", callback_data="html_dark")],
        [InlineKeyboardButton("📝 Свои критерии", callback_data="custom_criteria")],
        [InlineKeyboardButton("📜 Транскрипт", callback_data="get_transcript")],
        [InlineKeyboardButton("🔄 Перегенерировать", callback_data="regenerate")]
    ])

def get_retry_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Попробовать снова", callback_data="retry_transcribe")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])

def get_continue_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF светлый", callback_data="pdf_light_custom"),
         InlineKeyboardButton("🌙 PDF тёмный", callback_data="pdf_dark_custom")],
        [InlineKeyboardButton("📝 Ещё критерии", callback_data="custom_criteria")],
        [InlineKeyboardButton("✅ Готово", callback_data="done")]
    ])

# === BOT SETUP ===
app = Client(
    "meeting_bot_v3",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply("""👋 **Meeting Analyzer Bot v3**

Отправь аудио/видео встречи и получи:

📝 Детальное резюме с раскрытием каждой темы
👥 Позиции участников с цитатами  
✅ Решения с контекстом
📌 Action items с приоритетами
📚 Полный список всех тем
🔍 Reality check

**Форматы:** PDF/HTML (светлая/тёмная тема)
**Фичи:** Retry, свои критерии, до 4GB

Отправь файл! 🎙️""")

@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client, message):
    if message.document:
        mime = message.document.mime_type or ""
        if not ("audio" in mime or "video" in mime or "octet-stream" in mime):
            return
    
    user_id = message.from_user.id
    cache = get_user_cache(user_id)
    status_msg = await message.reply("⏳ Скачиваю файл...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = await message.download(file_name=f"{tmpdir}/media")
            cache["file_path"] = file_path
            
            await status_msg.edit_text("✅ Скачано!\n\n🎙️ Транскрибирую...")
            
            trans_result, error = transcribe_file(file_path)
            
            if error:
                await status_msg.edit_text(f"❌ Ошибка: {error}", reply_markup=get_retry_keyboard())
                return
            
            cache["transcript"] = trans_result["transcript"]
            cache["duration"] = trans_result["duration"]
            cache["speakers"] = trans_result["speakers"]
            
            await status_msg.edit_text(f"✅ Транскрипция готова!\n👥 Спикеров: {trans_result['speakers']}\n\n🧠 Анализирую...")
            
            summary = analyze_transcript(trans_result["transcript"], trans_result["duration"], trans_result["speakers"])
            cache["last_summary"] = summary
            
            await status_msg.delete()
            
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await message.reply(f"📋 **Превью:**\n\n{preview}")
            await message.reply("✨ **Выбери формат:**", reply_markup=get_after_analysis_keyboard())
                
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=get_retry_keyboard())

@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    cache = get_user_cache(user_id)
    
    if data.startswith("pdf_") or data.startswith("html_"):
        parts = data.split("_")
        format_type = parts[0]
        theme = parts[1]
        is_custom = len(parts) > 2
        
        content_key = "last_custom_result" if is_custom else "last_summary"
        if content_key not in cache:
            await callback_query.answer("❌ Контент не найден")
            return
        
        await callback_query.answer(f"📄 Генерирую {format_type.upper()}...")
        status_msg = await callback_query.message.edit_text(f"⏳ Генерирую {format_type.upper()}...")
        
        try:
            content = cache[content_key]
            if format_type == "pdf":
                file_path = generate_pdf(content, theme)
            else:
                file_path = generate_html(content, theme)
            
            await status_msg.delete()
            await callback_query.message.reply_document(
                document=file_path, 
                caption=f"{'📄 PDF' if format_type == 'pdf' else '🌐 HTML'} ({theme})"
            )
            os.remove(file_path)
            await callback_query.message.reply("✨ **Что ещё?**", reply_markup=get_after_analysis_keyboard())
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=get_after_analysis_keyboard())
    
    elif data == "custom_criteria":
        cache["stage"] = "waiting_criteria"
        await callback_query.answer()
        await callback_query.message.edit_text(
            "📝 **Введи критерии:**\n\n"
            "Примеры:\n"
            "• Какие бюджеты обсуждались?\n"
            "• Что сказал X про Y?\n"
            "• Список всех рисков"
        )
    
    elif data == "get_transcript":
        if "transcript" not in cache:
            await callback_query.answer("❌ Нет транскрипта")
            return
        await callback_query.answer("📄 Отправляю...")
        transcript = cache["transcript"]
        for i in range(0, len(transcript), 4000):
            await callback_query.message.reply(f"📜 **Транскрипт:**\n\n{transcript[i:i+4000]}")
        await callback_query.message.reply("✨ **Что дальше?**", reply_markup=get_after_analysis_keyboard())
    
    elif data == "regenerate":
        if "transcript" not in cache:
            await callback_query.answer("❌ Нет транскрипта")
            return
        await callback_query.answer("🔄 Генерирую...")
        status_msg = await callback_query.message.edit_text("🧠 Перегенерирую резюме...")
        try:
            summary = analyze_transcript(cache["transcript"], cache.get("duration", 0), cache.get("speakers", 1))
            cache["last_summary"] = summary
            await status_msg.delete()
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await callback_query.message.reply(f"📋 **Превью:**\n\n{preview}")
            await callback_query.message.reply("✨ **Формат:**", reply_markup=get_after_analysis_keyboard())
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=get_after_analysis_keyboard())
    
    elif data == "done":
        await callback_query.answer("✅ Готово!")
        await callback_query.message.edit_text("✅ **Готово!**\n\nОтправь новый файл для следующей встречи! 🎙️")
    
    elif data == "cancel":
        await callback_query.answer("❌ Отменено")
        await callback_query.message.edit_text("❌ Отменено. Отправь файл заново.")

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, message):
    user_id = message.from_user.id
    cache = get_user_cache(user_id)
    
    if cache.get("stage") == "waiting_criteria" and "transcript" in cache:
        status_msg = await message.reply("🧠 Анализирую по твоим критериям...")
        try:
            result = custom_analysis(cache["transcript"], message.text)
            cache["last_custom_result"] = result
            cache["stage"] = "done"
            await status_msg.delete()
            await message.reply(f"📋 **Результат:**\n\n{result}")
            await message.reply("✨ **Сохранить или продолжить?**", reply_markup=get_continue_keyboard())
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=get_continue_keyboard())
    else:
        await message.reply("🎙️ Отправь аудио/видео файл для анализа!")

if __name__ == "__main__":
    print("🚀 Starting Meeting Analyzer Bot v3...")
    app.run()
