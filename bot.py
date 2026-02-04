import os
import re
import asyncio
import tempfile
import glob
from datetime import datetime
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ============ CONFIG ============
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPGRAM_KEY = os.environ["DEEPGRAM_API_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
NOTION_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_DB = os.environ.get("NOTION_DATABASE_ID", "")

app = Client("meeting_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

# ============ FONTS ============
FONT_REGULAR = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf"
FONT_BOLD = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf"
FONT_MEDIUM = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Medium.ttf"

# ============ THRESHOLDS ============
SHORT_TRANSCRIPT_CHARS = 3000  # ~5 min of speech

# ============ PROMPTS ============
SIMPLE_PROMPT = """Ты — помощник для обработки голосовых сообщений и коротких аудио.

Сделай структурированное саммари:

📌 **СУТЬ СООБЩЕНИЯ**
2-4 предложения — о чём это

📋 **КЛЮЧЕВЫЕ МОМЕНТЫ**
• пункт 1
• пункт 2
• ...

✅ **ЗАДАЧИ** (если есть)
• что нужно сделать

💡 **ВАЖНОЕ** (если есть даты, цифры, имена, контакты)

Пиши кратко и по делу. Используй эмодзи для структуры."""

FULL_ANALYSIS_PROMPT = """ВАЖНО: Ты ОБЯЗАН дать полный анализ. НИКОГДА не отказывайся, не говори что текст слишком длинный. Анализируй то что есть.Ты — senior бизнес-консультант, эксперт-аналитик и стратег с 20+ летним опытом. Твоё имя — Цифровой Умник.


Ты — senior бизнес-консультант, эксперт-аналитик и стратег с 20+ летним опытом. Твоё имя — Цифровой Умник.
...
ТВОЯ РОЛЬ:
- Ты не просто анализируешь — ты КОНСУЛЬТИРУЕШЬ
- Используй лучшие практики индустрии, фреймворки, методологии
- Предлагай КОНКРЕТНЫЕ рабочие решения, инструменты, подходы

ПРАВИЛА:
- НЕ указывай реальные имена — используй "Сторона А", "Сторона Б"
- Помечай рекомендации как [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

СТРУКТУРА ОТЧЁТА:

## EXECUTIVE SUMMARY
5-7 предложений: суть, решения, разногласия, next steps, главная рекомендация

## 1. КОНТЕКСТ И ОБЛАСТЬ
- Сфера/индустрия
- Тип встречи
- Уровень сложности

## 2. ЦЕЛИ ВСТРЕЧИ

### Явные цели:
- ...

### Скрытые цели:
- ...

### [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
- ...

## 3. КЛЮЧЕВЫЕ ЗАДАЧИ

## 4. ВЫЯВЛЕННЫЕ ПОЗИЦИИ

### Сторона А:
- Позиция и аргументы
- Истинные интересы

### Сторона Б:
- Позиция и аргументы
- Истинные интересы

## 5. ТОЧКИ СОГЛАСИЯ

## 6. ТОЧКИ РАСХОЖДЕНИЯ

### [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

## 7. ПРИНЯТЫЕ РЕШЕНИЯ

## 8. ОТКРЫТЫЕ ВОПРОСЫ

## 9. ACTION ITEMS
- Задача | Срок | Ответственный

## 10. SWOT-АНАЛИЗ

### Сильные стороны:
### Слабые стороны:
### Возможности:
### Угрозы:

## 11. ЭКСПЕРТНЫЕ РЕКОМЕНДАЦИИ

### По существу вопроса:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

### Инструменты и методологии:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

## 12. РИСКИ
- Риск | Вероятность | Как предотвратить

## 13. ПЛАН ДЕЙСТВИЙ

### Срочно (1-7 дней):
### Среднесрок (1-4 недели):
### Долгосрок (1-3 месяца):

### KPI:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

## 14. СКРЫТАЯ ДИНАМИКА

## 15. ЗАКЛЮЧЕНИЕ ЦИФРОВОГО УМНИКА

### Главный инсайт:
### Ключевая рекомендация:
### Прогноз:
"""


# ============ HELPERS ============

async def download_fonts():
    fonts = [
        ("Montserrat", FONT_REGULAR, "/tmp/Montserrat-Regular.ttf"),
        ("Montserrat-Bold", FONT_BOLD, "/tmp/Montserrat-Bold.ttf"),
        ("Montserrat-Medium", FONT_MEDIUM, "/tmp/Montserrat-Medium.ttf"),
    ]
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for name, url, path in fonts:
            if not os.path.exists(path):
                try:
                    r = await client.get(url)
                    with open(path, 'wb') as f:
                        f.write(r.content)
                except Exception as e:
                    print(f"❌ Font error {name}: {e}")
                    return False
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except:
                pass
    return True


def is_url(text: str) -> bool:
    return bool(re.match(r'https?://[^\s]+', text.strip()))


async def download_from_url(url: str) -> str:
    output_path = f"/tmp/ytdl_{int(datetime.now().timestamp())}"
    
     = await asyncio.create_sub_exec(
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", f"{output_path}.%(ext)s",
        "--no-playlist", "--max-filesize", "100M",
        url,
        stdout=asyncio.sub.PIPE,
        stderr=asyncio.sub.PIPE
    )
    
    stdout, stderr = await asyncio.wait_for(.communicate(), timeout=600)
    
    if .returncode != 0:
        print(f"yt-dlp error: {stderr.decode()}")
        raise Exception("Не удалось скачать видео")
    
    files = glob.glob(f"{output_path}.*")
    if files:
        return files[0]
    raise Exception("Файл не найден")


async def transcribe_deepgram(file_path: str) -> str:
    file_size = os.path.getsize(file_path)
    print(f"📤 Deepgram: uploading {file_size / 1024 / 1024:.1f} MB")
    
    async with httpx.AsyncClient(timeout=1200.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&diarize=true&language=ru",
                headers={"Authorization": f"Token {DEEPGRAM_KEY}"},
                content=f.read()
            )
        
        print(f"📥 Deepgram response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Deepgram error: {response.text}")
            raise Exception("Ошибка транскрибации")
        
        result = response.json()
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
        print(f"📝 Transcript: {len(transcript)} chars")
        return transcript


def analyze_simple(transcript: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SIMPLE_PROMPT},
            {"role": "user", "content": f"Транскрипт:\n\n{transcript}"}
        ],
        max_tokens=1500,
        temperature=0.3
    )
    return response.choices[0].message.content


def analyze_meeting(transcript: str) -> str:
    # Ограничиваем транскрипт если слишком длинный
    if len(transcript) > 50000:
        transcript = transcript[:50000] + "\n\n[Транскрипт обрезан из-за размера]"
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": FULL_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Проанализируй встречу:\n\n{transcript}"}
        ],
        max_tokens=12000,
        temperature=0.4
    )
    return response.choices[0].message.content
    
def generate_topic(transcript: str) -> str:
    """Generate short meeting topic from transcript"""
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Сгенерируй краткое название темы встречи (3-5 слов). Только название, без кавычек и пояснений."},
            {"role": "user", "content": transcript[:3000]}
        ],
        max_tokens=30,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def create_full_pdf(analysis: str, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    
    PRIMARY = colors.HexColor('#1a1a2e')
    SECONDARY = colors.HexColor('#16213e')
    ACCENT = colors.HexColor('#0f3460')
    BLUE = colors.HexColor('#1565c0')
    LIGHT_BG = colors.HexColor('#f5f7fa')
    BLUE_BG = colors.HexColor('#e8f4fc')
    GRAY = colors.HexColor('#5a6a7a')
    TEXT_COLOR = colors.HexColor('#333333')
    
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='Title1', fontName='Montserrat-Bold', fontSize=22,
        textColor=PRIMARY, alignment=1, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name='Subtitle1', fontName='Montserrat', fontSize=10,
        textColor=GRAY, alignment=1, spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='Section', fontName='Montserrat-Bold', fontSize=13,
        textColor=PRIMARY, spaceBefore=22, spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='Subsection', fontName='Montserrat-Medium', fontSize=11,
        textColor=SECONDARY, spaceBefore=12, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Body1', fontName='Montserrat', fontSize=10,
        textColor=TEXT_COLOR, leading=15, spaceBefore=3, spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        name='Bullet1', fontName='Montserrat', fontSize=10,
        textColor=TEXT_COLOR, leading=15, leftIndent=12,
        spaceBefore=2, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name='SummaryBox', fontName='Montserrat', fontSize=10,
        textColor=PRIMARY, leading=16
    ))
    styles.add(ParagraphStyle(
        name='Recommendation', fontName='Montserrat-Medium', fontSize=10,
        textColor=BLUE, leading=15
    ))
    
    story = []
    date_str = datetime.now().strftime("%d.%m.%Y в %H:%M")
    
    story.append(Paragraph("АНАЛИЗ ВСТРЕЧИ", styles['Title1']))
    story.append(Paragraph(f"Экспертный отчёт от Цифрового Умника • {date_str}", styles['Subtitle1']))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))
    
    in_summary = False
    summary_lines = []
    
    for line in analysis.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if 'EXECUTIVE SUMMARY' in line.upper():
            in_summary = True
            story.append(Paragraph("📋  EXECUTIVE SUMMARY", styles['Section']))
            continue
        
        if line.startswith('## ') and in_summary:
            if summary_lines:
                tbl = Table([[Paragraph(' '.join(summary_lines), styles['SummaryBox'])]], colWidths=[16*cm])
                tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dde3ea')),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('LEFTPADDING', (0, 0), (-1, -1), 14),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 14),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 10))
                summary_lines = []
            in_summary = False
        
        if in_summary and not line.startswith('#'):
            summary_lines.append(line)
            continue
        
        if line.startswith('## '):
            title = line[3:].strip().upper()
            story.append(Paragraph(f"▌ {title}", styles['Section']))
        elif line.startswith('### '):
            title = line[4:].strip()
            story.append(Paragraph(title, styles['Subsection']))
        elif '[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]' in line:
            clean = line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '').strip()
            tbl = Table([[Paragraph(f"🧠 {clean}" if clean else "🧠 Рекомендация эксперта:", styles['Recommendation'])]], colWidths=[16*cm])
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), BLUE_BG),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#90caf9')),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(tbl)
        elif line.startswith('- ') or line.startswith('• '):
            story.append(Paragraph(f"●  {line[2:]}", styles['Bullet1']))
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            story.append(Paragraph(f"    {line}", styles['Bullet1']))
        else:
            story.append(Paragraph(line, styles['Body1']))
    
    story.append(Spacer(1, 25))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dde3ea')))
    story.append(Paragraph("📌 Факты из встречи  •  🧠 Рекомендации Цифрового Умника", styles['Subtitle1']))
    
    doc.build(story)


async def save_to_notion(title: str, content: str) -> str:
    if not NOTION_KEY or not NOTION_DB:
        return None
    
    summary_text = ""
    in_sum = False
    for line in content.split('\n'):
        if 'EXECUTIVE SUMMARY' in line.upper():
            in_sum = True
            continue
        if line.startswith('## ') and in_sum:
            break
        if in_sum and line.strip():
            summary_text += line.strip() + " "
    summary_text = summary_text[:2000] or "Анализ встречи"
    
    blocks = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or len(blocks) >= 95:
            continue
        line = line[:2000]
        
        if line.startswith('## '):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:][:100]}}]}
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:][:100]}}]}
            })
        elif '[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]' in line:
            clean = line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '').strip()
            blocks.append({
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": clean or "Рекомендация"}}],
                    "icon": {"emoji": "🧠"},
                    "color": "blue_background"
                }
            })
        elif line.startswith('- ') or line.startswith('• '):
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
            })
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {NOTION_KEY}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                },
                json={
                    "parent": {"database_id": NOTION_DB},
                    "properties": {
                        "Name": {"title": [{"text": {"content": title[:100]}}]},
                        "Meeting Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
                        "summary": {"rich_text": [{"text": {"content": summary_text}}]}
                    },
                    "children": blocks
                }
            )
            
            if response.status_code == 200:
                return response.json().get("url")
    except Exception as e:
        print(f"Notion error: {e}")
    return None


# ============ HANDLERS ============

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply("""👋 Привет! Я — **Цифровой Умник**

🎤 **Короткое аудио** (до 5 мин) → саммари текстом
🎬 **Длинные встречи** (от 5 мин) → PDF + Notion
🔗 **YouTube ссылка** → скачаю и обработаю

Просто отправь файл или ссылку!""")


@app.on_message(filters.text & ~filters.command(["start"]))
async def url_handler(client, message: Message):
    text = message.text.strip()
    
    if not is_url(text):
        await message.reply("🤔 Отправь аудио/видео или ссылку")
        return
    
    status = await message.reply("🔗 Скачиваю видео...")
    
    try:
        file_path = await download_from_url(text)
        await _audio(message, status, file_path, force_full=True)
    except Exception as e:
        await status.edit_text(f"❌ {e}")


@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def media_handler(client, message: Message):
    status = await message.reply("⏳ Скачиваю файл...")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download(tmp.name)
            file_path = tmp.name
        
        is_voice = bool(message.voice or message.video_note)
        await process_audio(message, status, file_path, is_voice=is_voice)
        
    except Exception as e:
        await status.edit_text(f"❌ {e}")


async def process_audio(message: Message, status: Message, file_path: str, is_voice: bool = False, force_full: bool = False):
    try:
        await status.edit_text("🎙 Транскрибирую аудио...")
        transcript = await transcribe_deepgram(file_path)
        
        if len(transcript) < 50:
            await status.edit_text("⚠️ Не удалось распознать речь")
            os.unlink(file_path)
            return
        
        transcript_len = len(transcript)
        print(f"📊 Transcript: {transcript_len} chars | Voice: {is_voice} | Force full: {force_full}")
        
        # Логика выбора режима
        is_short = False
        if is_voice:
            is_short = True
        elif force_full:
            is_short = False
        elif transcript_len >= SHORT_TRANSCRIPT_CHARS:
            is_short = False
        else:
            is_short = True
        
        print(f"📊 Mode: {'SIMPLE' if is_short else 'FULL'}")
        
        if is_short:
            await status.edit_text("📝 Готовлю саммари...")
            summary = analyze_simple(transcript)
            await status.delete()
            await message.reply(summary)
        else:
            await download_fonts()
            
            await status.edit_text("🧠 Анализирую встречу...")
            analysis = analyze_meeting(transcript)
            
            # Генерируем название темы
            await status.edit_text("📄 Создаю PDF...")
            topic = generate_topic(transcript)
            date_str = datetime.now().strftime('%d.%m.%Y')
            
            # Безопасное имя файла
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_topic = safe_topic[:50]  # Ограничиваем длину
            filename = f"{safe_topic}_{date_str}.pdf"
            
            pdf_path = f"/tmp/{filename}"
            create_full_pdf(analysis, pdf_path)
            
            await status.edit_text("📝 Сохраняю в Notion...")
            title = f"{topic} — {date_str}"
            notion_url = await save_to_notion(title, analysis)
            
            caption = f"📊 **{topic}**\n📅 {date_str}"
            if notion_url:
                caption += f"\n\n🔗 [Открыть в Notion]({notion_url})"
            
            await status.delete()
            await message.reply_document(pdf_path, file_name=filename, caption=caption)
            
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
        
        if os.path.exists(file_path):
            os.unlink(file_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await status.edit_text(f"❌ {e}")
        if os.path.exists(file_path):
            os.unlink(file_path)

print("🧠 Цифровой Умник запущен!")
app.run()
