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

# Setup fonts
FONT_URL = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
FONT_BOLD_URL = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
FONT_PATH = "/tmp/Roboto-Regular.ttf"
FONT_BOLD_PATH = "/tmp/Roboto-Bold.ttf"

async def download_fonts():
    async with httpx.AsyncClient() as client:
        if not os.path.exists(FONT_PATH):
            r = await client.get(FONT_URL)
            with open(FONT_PATH, 'wb') as f:
                f.write(r.content)
        if not os.path.exists(FONT_BOLD_PATH):
            r = await client.get(FONT_BOLD_URL)
            with open(FONT_BOLD_PATH, 'wb') as f:
                f.write(r.content)
    pdfmetrics.registerFont(TTFont('Roboto', FONT_PATH))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', FONT_BOLD_PATH))

ANALYSIS_PROMPT = """Ты — senior бизнес-консультант, эксперт-аналитик и стратег с 20+ летним опытом. Твоё имя — Цифровой Умник.

При анализе встречи ты АВТОМАТИЧЕСКИ становишься экспертом в обсуждаемой области (IT, продажи, маркетинг, финансы, HR, производство, стартапы, инвестиции и т.д.) и используешь ВСЕ свои знания и опыт для рекомендаций.

ТВОЯ РОЛЬ:
- Ты не просто анализируешь — ты КОНСУЛЬТИРУЕШЬ
- Используй лучшие практики индустрии, фреймворки, методологии
- Приводи примеры из опыта (как это решают другие компании)
- Предлагай КОНКРЕТНЫЕ рабочие решения, инструменты, подходы
- Думай как партнёр, который заинтересован в успехе

ПРАВИЛА:
- НЕ указывай реальные имена — используй "Сторона А", "Сторона Б"
- Чётко разделяй: факты из встречи vs твои экспертные рекомендации
- Помечай свои рекомендации как [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]

СТРУКТУРА ОТЧЁТА:

## EXECUTIVE SUMMARY (САММАРИ)
Краткое содержание на 5-7 предложений:
- О чём встреча
- Ключевые решения
- Главные разногласия
- Критичные next steps
- Основная рекомендация от Цифрового Умника

## 1. КОНТЕКСТ И ОБЛАСТЬ
- Сфера/индустрия
- Тип встречи (переговоры, планирование, проблема, статус)
- Уровень сложности ситуации

## 2. ЦЕЛИ ВСТРЕЧИ

### Явные цели (озвучено):
- ...

### Скрытые цели (между строк):
- ...

### [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА] Как лучше формулировать цели:
- ...

## 3. КЛЮЧЕВЫЕ ЗАДАЧИ
Что пытались решить + насколько эффективно подошли к решению

## 4. ВЫЯВЛЕННЫЕ ПОЗИЦИИ

### Сторона А:
- Позиция и аргументы
- Истинные интересы
- Сильные/слабые стороны позиции

### Сторона Б:
- Позиция и аргументы
- Истинные интересы
- Сильные/слабые стороны позиции

## 5. ТОЧКИ СОГЛАСИЯ
Где интересы совпадают — это фундамент для решений

## 6. ТОЧКИ РАСХОЖДЕНИЯ
Противоречия и их корневые причины

### [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА] Как преодолеть расхождения:
Конкретные техники переговоров, подходы к компромиссу

## 7. ПРИНЯТЫЕ РЕШЕНИЯ
Что решено + оценка качества решений

## 8. ОТКРЫТЫЕ ВОПРОСЫ
Что не решено и почему это критично

## 9. ACTION ITEMS
| Задача | Срок | Ответственный |

## 10. СТРАТЕГИЧЕСКИЙ SWOT-АНАЛИЗ

### Сильные стороны:
- ...

### Слабые стороны:
- ...

### Возможности:
- ...

### Угрозы:
- ...

## 11. ЭКСПЕРТНЫЕ РЕКОМЕНДАЦИИ

### По существу вопроса (что делать):
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
Конкретные решения, основанные на лучших практиках индустрии:
1. ...
2. ...

### По процессу (как делать лучше):
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
1. ...
2. ...

### Инструменты и методологии:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
Какие фреймворки, инструменты, подходы применить:
- ...

### Бенчмарки и примеры:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
Как подобные задачи решают лидеры рынка:
- ...

## 12. РИСКИ И КАК ИХ ИЗБЕЖАТЬ

| Риск | Вероятность | Влияние | Как предотвратить |
| ... | Высокая/Средняя/Низкая | ... | [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА] |

## 13. ПЛАН ДАЛЬНЕЙШИХ ДЕЙСТВИЙ

### Срочно (1-7 дней):
1. ...

### Среднесрок (1-4 недели):
1. ...

### Долгосрок (1-3 месяца):
1. ...

### KPI и метрики успеха:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
Как измерить что всё идёт по плану:
- ...

## 14. СКРЫТАЯ ДИНАМИКА
- Невысказанные напряжения
- Эмоциональный фон
- Потенциальные конфликты

## 15. ЗАКЛЮЧЕНИЕ ЦИФРОВОГО УМНИКА

### Главный инсайт:
(1-2 предложения — самое важное)

### Ключевая рекомендация:
[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]
Если бы я был на этой встрече как консультант, я бы посоветовал...

### Прогноз:
Что произойдёт если следовать/не следовать рекомендациям

---
📌 Факты взяты из транскрипта
🧠 [РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА] — экспертное мнение на основе лучших практик
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
            {"role": "user", "content": f"Проанализируй эту встречу как эксперт-консультант:\n\n{transcript}"}
        ],
        max_tokens=8000,
        temperature=0.4
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
    
    styles.add(ParagraphStyle(
        name='RuExpert',
        fontName='Roboto',
        fontSize=11,
        spaceBefore=6,
        spaceAfter=6,
        leading=16,
        leftIndent=20,
        textColor=colors.HexColor('#0066cc'),
        backColor=colors.HexColor('#f0f7ff')
    ))
    
    styles.add(ParagraphStyle(
        name='RuSummary',
        fontName='Roboto',
        fontSize=12,
        spaceBefore=10,
        spaceAfter=10,
        leading=18,
        backColor=colors.HexColor('#f5f5f5'),
        borderPadding=10
    ))
    
    story = []
    
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    story.append(Paragraph("АНАЛИЗ ВСТРЕЧИ", styles['RuTitle']))
    story.append(Paragraph("Экспертный отчёт от Цифрового Умника", styles['RuBody']))
    story.append(Paragraph(f"Дата: {date_str}", styles['RuBody']))
    story.append(Spacer(1, 20))
    
    in_summary = False
    for line in analysis.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        
        if 'EXECUTIVE SUMMARY' in line or 'САММАРИ' in line:
            in_summary = True
            story.append(Paragraph("📋 EXECUTIVE SUMMARY", styles['RuHeading']))
            continue
        
        if line.startswith('## ') and in_summary:
            in_summary = False
        
        if in_summary and not line.startswith('#'):
            story.append(Paragraph(line, styles['RuSummary']))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:].upper(), styles['RuHeading']))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], styles['RuSubheading']))
        elif '[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]' in line:
            clean_line = line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '🧠')
            story.append(Paragraph(clean_line, styles['RuExpert']))
        elif line.startswith('- '):
            story.append(Paragraph(f"• {line[2:]}", styles['RuBody']))
        elif line.startswith('| '):
            story.append(Paragraph(line, styles['RuBody']))
        else:
            story.append(Paragraph(line, styles['RuBody']))
    
    doc.build(story)

async def save_to_notion(title: str, analysis: str) -> str:
    if not NOTION_KEY or not NOTION_DB:
        return None
    
    blocks = []
    for line in analysis.split('\n'):
        line = line.strip()
        if not line:
            continue
        elif line.startswith('## '):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
            })
        elif line.startswith('### '):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}
            })
        elif '[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]' in line:
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": line.replace('[РЕКОМЕНДАЦИЯ ОТ ЦИФРОВОГО УМНИКА]', '')}}],
                    "icon": {"emoji": "🧠"}
                }
            })
        elif line.startswith('- '):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": line[3:].strip()}}]}
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
            })
    
    async with httpx.AsyncClient() as client:
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
                    "Name": {"title": [{"text": {"content": title}}]},
                    "Meeting Date": {"date": {"start": datetime.now().isoformat()}}
                },
                "children": blocks[:100]
            }
        )
        if response.status_code == 200:
            return response.json().get("url")
        return None

@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    welcome = """👋 Привет! Я — Цифровой Умник, AI-консультант по анализу встреч.

📎 **Отправь аудио или видео** записи

📋 **Что ты получишь:**
• 📝 Executive Summary (краткое саммари)
• 🎯 Цели и задачи встречи
• ⚖️ Позиции сторон и точки согласия/расхождения
• 📊 SWOT-анализ ситуации
• 🧠 Рекомендации от Цифрового Умника
• 📅 План действий с KPI
• 📄 PDF-отчёт + страница в Notion

🎯 Анализирую как senior консультант — даю рабочие решения из лучших практик.

🔒 Файлы сразу удаляются."""
    await message.reply(welcome)

@app.on_message(filters.audio | filters.video | filters.document | filters.voice | filters.video_note)
async def media_handler(client, message: Message):
    status = await message.reply("⏳ Скачиваю...")
    
    try:
        await download_fonts()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            await message.download(tmp.name)
            tmp_path = tmp.name
        
        await status.edit_text("🎙 Транскрибирую...")
        transcript = await transcribe_deepgram(tmp_path)
        
        if len(transcript) < 100:
            await status.edit_text("⚠️ Слишком короткая запись")
            os.unlink(tmp_path)
            return
        
        await status.edit_text("🧠 Цифровой Умник анализирует...")
        analysis = analyze_meeting(transcript)
        
        await status.edit_text("📄 Создаю PDF...")
        pdf_path = tmp_path.replace('.mp4', '.pdf')
        create_pdf(analysis, pdf_path)
        
        await status.edit_text("📝 Сохраняю в Notion...")
        title = f"Встреча {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        notion_url = await save_to_notion(title, analysis)
        
        await status.edit_text("📤 Отправляю...")
        
        caption = "📋 **Экспертный анализ от Цифрового Умника готов!**\n\n🧠 Включает саммари, анализ и рекомендации"
        if notion_url:
            caption += f"\n\n🔗 [Открыть в Notion]({notion_url})"
        
        await message.reply_document(pdf_path, caption=caption)
        await status.delete()
        
        os.unlink(tmp_path)
        os.unlink(pdf_path)
        
    except Exception as e:
        await status.edit_text(f"❌ Ошибка: {str(e)}")

print("🧠 Цифровой Умник запущен!")
app.run()
