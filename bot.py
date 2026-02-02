import os
import re
import asyncio
import tempfile
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

# Config
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPGRAM_KEY = os.environ["DEEPGRAM_API_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
NOTION_KEY = os.environ.get("NOTION_API_KEY", "")
NOTION_DB = os.environ.get("NOTION_DATABASE_ID", "")

app = Client("meeting_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Montserrat font - stylish & supports Cyrillic
FONT_REGULAR = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf"
FONT_BOLD = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf"
FONT_MEDIUM = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Medium.ttf"

SHORT_DURATION_SECONDS = 600  # 10 min

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
                    print(f"✅ Downloaded {name}")
                except Exception as e:
                    print(f"❌ Failed to download {name}: {e}")
                    return False
            
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception as e:
                print(f"❌ Failed to register {name}: {e}")
                return False
    
    return True

SIMPLE_PROMPT = """Ты — помощник для обработки голосовых сообщений.

Сделай структурированное саммари:

📌 **СУТЬ**
2-4 предложения — о чём это

📋 **КЛЮЧЕВЫЕ МОМЕНТЫ**
• пункт 1
• пункт 2

✅ **ЗАДАЧИ** (если есть)
• что нужно сделать

💡 **ВАЖНОЕ** (если есть даты, цифры, имена)

Кратко и по делу."""

FULL_ANALYSIS_PROMPT = """Ты — senior бизнес-консультант с 20+ летним опытом. Имя — Цифровой Умник.

ПРАВИЛА:
- Не указывай реальные имена — "Сторона А", "Сторона Б"
- Рекомендации помечай: [РЕКОМЕНДАЦИЯ]

СТРУКТУРА:

## EXECUTIVE SUMMARY
5-7 предложений

## 1. КОНТЕКСТ
• Сфера
• Тип встречи

## 2. ЦЕЛИ
### Явные:
### Скрытые:

## 3. ПОЗИЦИИ СТОРОН
### Сторона А:
### Сторона Б:

## 4. СОГЛАСИЕ

## 5. РАСХОЖДЕНИЯ
[РЕКОМЕНДАЦИЯ]

## 6. РЕШЕНИЯ

## 7. ACTION ITEMS
• Задача — Срок — Ответственный

## 8. SWOT
### Сильные:
### Слабые:
### Возможности:
### Угрозы:

## 9. РЕКОМЕНДАЦИИ
[РЕКОМЕНДАЦИЯ]

## 10. ПЛАН
### Срочно (1-7 дней):
### Среднесрок (1-4 недели):

## 11. РИСКИ

## 12. ВЫВОД
### Главный инсайт:
### Прогноз:
"""

def is_url(text: str) -> bool:
    return bool(re.match(r'https?://[^\s]+', text.strip()))

async def download_from_url(url: str) -> str:
    output_template = f"/tmp/ytdl_{datetime.now().timestamp()}.%(ext)s"
    
    process = await asyncio.create_subprocess_exec(
        "yt-dlp", "-x", "--audio-format", "mp3",
        "-o", output_template, "--no-playlist", "--max-filesize", "50M", url,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
    
    if process.returncode != 0:
        raise Exception("Не удалось скачать видео")
    
    import glob
    files = glob.glob(f"/tmp/ytdl_{datetime.now().timestamp()}*".replace(".%(ext)s", "") + "*")
    if not files:
        files = glob.glob("/tmp/ytdl_*")
    
    if files:
        return sorted(files, key=os.path.getmtime)[-1]
    raise Exception("Файл не найден")

async def get_audio_duration(file_path: str) -> int:
    try:
        process = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        return int(float(stdout.decode().strip()))
    except:
        return 0

async def transcribe_deepgram(file_path: str) -> str:
    async with httpx.AsyncClient(timeout=600.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&diarize=true&language=ru",
                headers={"Authorization": f"Token {DEEPGRAM_KEY}"},
                content=f.read()
            )
        result = response.json()
        return result["results"]["channels"][0]["alternatives"][0]["transcript"]

def analyze_simple(transcript: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SIMPLE_PROMPT},
            {"role": "user", "content": f"Транскрипт:\n\n{transcript}"}
        ],
        max_tokens=1500, temperature=0.3
    )
    return response.choices[0].message.content

def analyze_meeting(transcript: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": FULL_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Проанализируй:\n\n{transcript}"}
        ],
        max_tokens=8000, temperature=0.4
    )
    return response.choices[0].message.content

def create_full_pdf(analysis: str, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    
    # Colors
    PRIMARY = colors.HexColor('#1a1a2e')
    SECONDARY = colors.HexColor('#16213e')
    ACCENT = colors.HexColor('#0f3460')
    BLUE = colors.HexColor('#1565c0')
    LIGHT_BG = colors.HexColor('#f5f7fa')
    BLUE_BG = colors.HexColor('#e8f4fc')
    GRAY = colors.HexColor('#5a6a7a')
    
    styles = getSampleStyleSheet()
    
    # Title
    styles.add(ParagraphStyle(
        name='Title1', fontName='Montserrat-Bold', fontSize=22,
        textColor=PRIMARY, alignment=1, spaceAfter=8
    ))
    
    # Subtitle  
    styles.add(ParagraphStyle(
        name='Subtitle1', fontName='Montserrat', fontSize=10,
        textColor=GRAY, alignment=1, spaceAfter=20
    ))
    
    # Section header
    styles.add(ParagraphStyle(
        name='Section', fontName='Montserrat-Bold', fontSize=13,
        textColor=PRIMARY, spaceBefore=22, spaceAfter=10,
        borderPadding=(8, 0, 8, 0)
    ))
    
    # Subsection
    styles.add(ParagraphStyle(
        name='Subsection', fontName='Montserrat-Medium', fontSize=11,
        textColor=SECONDARY, spaceBefore=12, spaceAfter=6
    ))
    
    # Body
    styles.add(ParagraphStyle(
        name='Body1', fontName='Montserrat', fontSize=10,
        textColor=colors.HexColor('#333333'), leading=15,
        spaceBefore=3, spaceAfter=3
    ))
    
    # Bullet
    styles.add(ParagraphStyle(
        name='Bullet1', fontName='Montserrat', fontSize=10,
        textColor=colors.HexColor('#333333'), leading=15,
        leftIndent=12, spaceBefore=2, spaceAfter=2
    ))
    
    # Summary box text
    styles.add(ParagraphStyle(
        name='SummaryBox', fontName='Montserrat', fontSize=10,
        textColor=PRIMARY, leading=16, spaceBefore=5, spaceAfter=5
    ))
    
    # Recommendation
    styles.add(ParagraphStyle(
        name='Recommendation', fontName='Montserrat-Medium', fontSize=10,
        textColor=BLUE, leading=15, leftIndent=8, spaceBefore=8, spaceAfter=8
    ))
    
    story = []
    date_str = datetime.now().strftime("%d.%m.%Y в %H:%M")
    
    # Header
    story.append(Paragraph("АНАЛИЗ ВСТРЕЧИ", styles['Title1']))
    story.append(Paragraph(f"Экспертный отчёт • {date_str}", styles['Subtitle1']))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))
    
    in_summary = False
    summary_lines = []
    
    lines = analysis.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
        
        # Executive Summary
        if 'EXECUTIVE SUMMARY' in line.upper():
            in_summary = True
            story.append(Paragraph("📋  EXECUTIVE SUMMARY", styles['Section']))
            continue
        
        # End summary
        if line.startswith('## ') and in_summary:
            if summary_lines:
                summary_text = ' '.join(summary_lines)
                # Create summary box
                tbl = Table([[Paragraph(summary_text, styles['SummaryBox'])]], colWidths=[16*cm])
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
        
        # Section headers ##
        if line.startswith('## '):
            title = line[3:].strip().upper()
            story.append(Paragraph(f"▌ {title}", styles['Section']))
        
        # Subsection ###
        elif line.startswith('### '):
            title = line[4:].strip()
            story.append(Paragraph(title, styles['Subsection']))
        
        # Recommendation
        elif '[РЕКОМЕНДАЦИЯ]' in line or '[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]' in line:
            clean = line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '').replace('[РЕКОМЕНДАЦИЯ]', '').strip()
            # Recommendation box
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
        
        # Bullets
        elif line.startswith('- ') or line.startswith('• '):
            story.append(Paragraph(f"●  {line[2:]}", styles['Bullet1']))
        
        # Numbered
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            story.append(Paragraph(f"    {line}", styles['Bullet1']))
        
        # Regular text
        else:
            story.append(Paragraph(line, styles['Body1']))
    
    # Footer
    story.append(Spacer(1, 25))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dde3ea'), spaceBefore=10))
    story.append(Paragraph("📌 Факты из встречи  •  🧠 Рекомендации Цифрового Умника", styles['Subtitle1']))
    
    doc.build(story)

async def save_to_notion(title: str, content: str) -> str:
    print(f"📝 Notion: Starting save...")
    print(f"   NOTION_KEY present: {bool(NOTION_KEY)}")
    print(f"   NOTION_DB: {NOTION_DB[:20]}..." if NOTION_DB else "   NOTION_DB: empty")
    
    if not NOTION_KEY or not NOTION_DB:
        print("❌ Notion: Missing credentials")
        return None
    
    # Extract summary
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
    
    # Build blocks
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
        elif '[РЕКОМЕНДАЦИЯ' in line:
            clean = line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '').replace('[РЕКОМЕНДАЦИЯ]', '').strip()
            blocks.append({
                "object": "block", "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": clean or "Рекомендация"}}],
                    "icon": {"emoji": "🧠"}, "color": "blue_background"
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
    
    payload = {
        "parent": {"database_id": NOTION_DB},
        "properties": {
            "Name": {"title": [{"text": {"content": title[:100]}}]},
            "Meeting Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "summary": {"rich_text": [{"text": {"content": summary_text[:2000]}}]}
        },
        "children": blocks
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {NOTION_KEY}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                },
                json=payload
            )
            
            print(f"   Notion response: {response.status_code}")
            
            if response.status_code == 200:
                url = response.json().get("url")
                print(f"✅ Notion: Created {url}")
                return url
            else:
                print(f"❌ Notion error: {response.text[:500]}")
                return None
                
    except Exception as e:
        print(f"❌ Notion exception: {e}")
        return None

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply("""👋 Привет! Я — **Цифровой Умник**

🎤 **Голосовое / короткое аудио** (до 10 мин)
→ Саммари текстом

🎬 **Длинные встречи** (от 10 мин)
→ Полный анализ + PDF + Notion

🔗 **Ссылка YouTube**
→ Скачаю и обработаю

Просто отправь файл или ссылку!""")

@app.on_message(filters.text & ~filters.command(["start"]))
async def url_handler(client, message: Message):
    text = message.text.strip()
    
    if not is_url(text):
        await message.reply("🤔 Отправь аудио/видео или ссылку на YouTube")
        return
    
    status = await message.reply("🔗 Скачиваю...")
    
    try:
        file_path = await download_from_url(text)
        await process_audio(message, status, file_path)
    except Exception as e:
        await status.edit_text(f"❌ {e}")

@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def media_handler(client, message: Message):
    status = await message.reply("⏳ Скачиваю...")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download(tmp.name)
            file_path = tmp.name
        
        is_voice = bool(message.voice or message.video_note)
        await process_audio(message, status, file_path, is_voice=is_voice)
        
    except Exception as e:
        await status.edit_text(f"❌ {e}")

async def process_audio(message: Message, status: Message, file_path: str, is_voice: bool = False):
    try:
        duration = await get_audio_duration(file_path)
        print(f"📊 Duration: {duration}s, is_voice: {is_voice}")
        
        await status.edit_text("🎙 Транскрибирую...")
        transcript = await transcribe_deepgram(file_path)
        
        if len(transcript) < 50:
            await status.edit_text("⚠️ Не удалось распознать речь")
            os.unlink(file_path)
            return
        
        is_short = is_voice or duration < SHORT_DURATION_SECONDS
        
        if is_short:
            await status.edit_text("📝 Готовлю саммари...")
            summary = analyze_simple(transcript)
            
            await status.delete()
            await message.reply(summary)
            os.unlink(file_path)
            
        else:
            fonts_ok = await download_fonts()
            if not fonts_ok:
                await status.edit_text("❌ Ошибка загрузки шрифтов")
                return
            
            await status.edit_text("🧠 Анализирую встречу...")
            analysis = analyze_meeting(transcript)
            
            await status.edit_text("📄 Создаю PDF...")
            pdf_path = file_path + ".pdf"
            create_full_pdf(analysis, pdf_path)
            
            await status.edit_text("📝 Сохраняю в Notion...")
            title = f"Встреча {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            notion_url = await save_to_notion(title, analysis)
            
            caption = "📊 **Анализ от Цифрового Умника**"
            if notion_url:
                caption += f"\n\n🔗 [Открыть в Notion]({notion_url})"
            else:
                caption += "\n\n⚠️ Notion: не удалось сохранить"
            
            await status.delete()
            await message.reply_document(pdf_path, caption=caption)
            
            os.unlink(file_path)
            os.unlink(pdf_path)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await status.edit_text(f"❌ {e}")
        if os.path.exists(file_path):
            os.unlink(file_path)

print("🧠 Цифровой Умник запущен!")
app.run()
