import os
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request

# Config
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DEEPGRAM_KEY = os.environ["DEEPGRAM_API_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

app = Client("meeting_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Download and register font with Cyrillic support
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Regular.ttf"
FONT_BOLD_URL = "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Bold.ttf"
FONT_PATH = "/tmp/Roboto-Regular.ttf"
FONT_BOLD_PATH = "/tmp/Roboto-Bold.ttf"

def setup_fonts():
    if not os.path.exists(FONT_PATH):
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    if not os.path.exists(FONT_BOLD_PATH):
        urllib.request.urlretrieve(FONT_BOLD_URL, FONT_BOLD_PATH)
    pdfmetrics.registerFont(TTFont('Roboto', FONT_PATH))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', FONT_BOLD_PATH))

setup_fonts()

ANALYSIS_PROMPT = """Ты — эксперт по анализу деловых переговоров и встреч. Проанализируй транскрипт и создай структурированный отчёт.

ВАЖНЫЕ ПРАВИЛА:
- НЕ указывай реальные имена участников
- Используй нейтральные обозначения: "Сторона А", "Сторона Б", "Первый участник", "Второй участник"
- Выявляй ПОЗИЦИИ и ИНТЕРЕСЫ, а не личности
- Будь объективным, анализируй обе/все стороны

СТРУКТУРА ОТЧЁТА:

## 1. СУТЬ ВСТРЕЧИ
Кратко (3-4 предложения): о чём встреча, ключевой вопрос/проблема

## 2. ВЫЯВЛЕННЫЕ ПОЗИЦИИ

### Сторона А (первая позиция):
- Основной тезис
- Аргументы
- Интересы (что стоит за позицией)

### Сторона Б (вторая позиция):
- Основной тезис  
- Аргументы
- Интересы

(добавь больше сторон если есть)

## 3. ТОЧКИ СОГЛАСИЯ
Где позиции сходятся, общие интересы

## 4. ТОЧКИ РАСХОЖДЕНИЯ
Ключевые противоречия и их причины

## 5. ПРИНЯТЫЕ РЕШЕНИЯ
Что конкретно решили (если есть)

## 6. ОТКРЫТЫЕ ВОПРОСЫ
Что осталось нерешённым

## 7. ACTION ITEMS
Конкретные задачи с указанием ответственной стороны и срока

## 8. РИСКИ И ПРЕДУПРЕЖДЕНИЯ
- Потенциальные проблемы
- На что обратить внимание

## 9. РЕКОМЕНДАЦИИ
Конкретные предложения по улучшению ситуации/процесса

## 10. ПЛАН ДАЛЬНЕЙШИХ ДЕЙСТВИЙ

### Ближайшие шаги (1-7 дней):
1. ...
2. ...

### Среднесрочные действия (1-4 недели):
1. ...
2. ...

### Долгосрочные цели (1-3 месяца):
1. ...

### Контрольные точки:
- Когда и что проверить
- Критерии успеха

## 11. СКРЫТАЯ ДИНАМИКА
Что осталось невысказанным, подтекст, эмоциональный фон
"""

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

def analyze_meeting(transcript: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": ANALYSIS_PROMPT},
            {"role": "user", "content": f"Вот транскрипт встречи:\n\n{transcript}"}
        ],
        max_tokens=6000,
        temperature=0.3
    )
    return response.choices[0].message.content

def create_pdf(analysis: str, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='RuTitle',
        fontName='Roboto-Bold',
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1a1a2e')
    ))
    
    styles.add(ParagraphStyle(
        name='RuHeading',
        fontName='Roboto-Bold',
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e')
    ))
    
    styles.add(ParagraphStyle(
        name='RuSubheading',
        fontName='Roboto-Bold',
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#1f4068')
    ))
    
    styles.add(ParagraphStyle(
        name='RuBody',
        fontName='Roboto',
        fontSize=11,
        spaceBefore=6,
        spaceAfter=6,
        leading=16
    ))
    
    story = []
    
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph("АНАЛИЗ ВСТРЕЧИ", styles['RuTitle']))
    story.append(Paragraph(f"Дата анализа: {date_str}", styles['RuBody']))
    story.append(Spacer(1, 20))
    
    lines = analysis.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 8))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].upper(), styles['RuHeading']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['RuSubheading']))
        elif line.startswith('- '):
            story.append(Paragraph(f"• {line[2:]}", styles['RuBody']))
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            story.append(Paragraph(line, styles['RuBody']))
        else:
            story.append(Paragraph(line, styles['RuBody']))
    
    doc.build(story)

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    welcome = """👋 Привет! Я анализирую встречи и переговоры.

📎 **Отправь мне аудио или видео** записи встречи (до 4GB)

📄 **Что ты получишь (PDF-отчёт):**
• Выявленные позиции сторон (без имён)
• Точки согласия и расхождения
• Принятые решения и action items
• Риски и рекомендации
• План дальнейших действий
• Скрытая динамика и подтекст

🔒 Файлы обрабатываются и сразу удаляются."""
    await message.reply(welcome)

@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def media_handler(client, message: Message):
    status = await message.reply("⏳ Скачиваю файл...")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download(tmp.name)
            tmp_path = tmp.name
        
        await status.edit_text("🎙 Транскрибирую аудио...")
        transcript = await transcribe_deepgram(tmp_path)
        
        if len(transcript) < 100:
            await status.edit_text("⚠️ Слишком короткая запись или не удалось распознать речь")
            os.unlink(tmp_path)
            return
        
        await status.edit_text("🧠 Анализирую содержание...")
        analysis = analyze_meeting(transcript)
        
        await status.edit_text("📄 Генерирую PDF-отчёт...")
        pdf_path = tmp_path.replace('.mp4', '.pdf')
        create_pdf(analysis, pdf_path)
        
        await status.edit_text("📤 Отправляю...")
        await message.reply_document(
            pdf_path,
            caption="📋 **Анализ встречи готов!**\n\nВ отчёте: позиции сторон, решения, план действий, риски и рекомендации."
        )
        
        await status.delete()
        
        os.unlink(tmp_path)
        os.unlink(pdf_path)
        
    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {str(e)}")

print("🤖 Meeting Analyzer Bot started!")
app.run()
