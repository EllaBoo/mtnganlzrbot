import os
import re
import json
import asyncio
import tempfile
from datetime import datetime
from typing import Optional
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from openai import OpenAI

# ============= CONFIG =============
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DEEPGRAM_KEY = os.environ.get("DEEPGRAM_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

app = Client("meeting_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_KEY)

# Хранилище данных пользователей
user_data = {}

# ============= LANGUAGES =============
LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "kk": "🇰🇿 Қазақша",
    "original": "🌐 Язык оригинала"
}

# ============= PROMPTS =============
ANALYSIS_PROMPT = """Ты — Цифровой Умник, senior бизнес-консультант и эксперт-аналитик с 20+ летним опытом.

ЗАДАЧА: Проанализируй транскрипт встречи/выступления и верни результат в формате JSON.

КРИТИЧЕСКИ ВАЖНО — НЕ ВЫДУМЫВАЙ:
- НЕ придумывай имена участников — используй только те, что явно названы
- НЕ придумывай конфликты или разные позиции, если их не было
- НЕ придумывай данные, которых нет в транскрипте
- Если все были согласны — так и напиши
- Если информации нет — пропусти поле или напиши null

ФОРМАТ ОТВЕТА — СТРОГО JSON:
{
    "summary": "Краткое резюме в 3-5 предложений",
    
    "topics": [
        {
            "id": 1,
            "title": "Название темы",
            "duration_percent": 25,
            "key_points": ["пункт 1", "пункт 2"],
            "quotes": [{"text": "цитата", "author": "кто сказал или null"}],
            "decisions": ["решение 1"],
            "open_questions": ["вопрос 1"],
            "expert_comment": "Комментарий Цифрового Умника по этой теме"
        }
    ],
    
    "participants": ["имя 1", "имя 2"],
    
    "overall_decisions": ["Общее решение 1", "Общее решение 2"],
    
    "action_items": [
        {"task": "задача", "responsible": "кто или null", "deadline": "срок или null"}
    ],
    
    "agreements": ["С чем все согласились"],
    
    "disagreements": ["Разногласия — ТОЛЬКО если реально были, иначе пустой массив"],
    
    "risks": ["риск 1"],
    
    "opportunities": ["возможность 1"],
    
    "expert_recommendations": [
        "Рекомендация 1 от Цифрового Умника",
        "Рекомендация 2"
    ],
    
    "next_steps": {
        "urgent": ["срочные действия 1-7 дней"],
        "medium": ["среднесрок 1-4 недели"],
        "long": ["долгосрок 1-3 месяца"]
    },
    
    "meeting_effectiveness": {
        "score": 8,
        "comment": "Комментарий об эффективности встречи"
    }
}

ВАЖНО:
1. Выдели ВСЕ темы, которые обсуждались — не пропускай ничего
2. duration_percent — примерная доля времени на тему (в сумме 100%)
3. Для каждой темы дай экспертный комментарий
4. В конце дай общие рекомендации от Цифрового Умника
5. Отвечай ТОЛЬКО валидным JSON, без markdown, без ```json```

ЯЗЫК ОТВЕТА: {output_language}
"""

# ============= HELPERS =============

async def download_youtube(url: str) -> Optional[str]:
    """Скачивает аудио с YouTube"""
    try:
        import yt_dlp
        
        output_path = tempfile.mktemp(suffix=".mp3")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path.replace('.mp3', ''),
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # yt-dlp добавляет расширение
        actual_path = output_path.replace('.mp3', '') + '.mp3'
        if os.path.exists(actual_path):
            return actual_path
        return output_path
        
    except Exception as e:
        print(f"YouTube download error: {e}")
        return None


async def download_from_url(url: str) -> Optional[str]:
    """Скачивает файл по прямой ссылке"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
            response = await client.get(url)
            
            suffix = ".mp3"
            if "video" in response.headers.get("content-type", ""):
                suffix = ".mp4"
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(response.content)
                return tmp.name
                
    except Exception as e:
        print(f"URL download error: {e}")
        return None


async def transcribe_audio(file_path: str) -> str:
    """Транскрибирует аудио через Deepgram"""
    
    url = "https://api.deepgram.com/v1/listen"
    params = {
        "model": "nova-2",
        "language": "ru",
        "punctuate": "true",
        "diarize": "true",
        "paragraphs": "true"
    }
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                url,
                params=params,
                headers={
                    "Authorization": f"Token {DEEPGRAM_KEY}",
                    "Content-Type": "audio/mpeg"
                },
                content=f.read()
            )
    
    result = response.json()
    
    # Пробуем получить текст с параграфами
    try:
        paragraphs = result["results"]["channels"][0]["alternatives"][0]["paragraphs"]["paragraphs"]
        transcript_parts = []
        for p in paragraphs:
            for s in p["sentences"]:
                transcript_parts.append(s["text"])
        transcript = " ".join(transcript_parts)
    except:
        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
    
    return transcript


async def analyze_meeting(transcript: str, output_language: str) -> dict:
    """Анализирует транскрипт через OpenAI"""
    
    lang_map = {
        "ru": "русский",
        "en": "English",
        "kk": "қазақ тілі",
        "original": "тот же язык, что и в транскрипте"
    }
    
    prompt = ANALYSIS_PROMPT.format(output_language=lang_map.get(output_language, "русский"))
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Транскрипт:\n\n{transcript}"}
        ],
        temperature=0.3,
        max_tokens=8000,
        response_format={"type": "json_object"}
    )
    
    content = response.choices[0].message.content
    
    # Логируем для отладки
    print("=== GPT RESPONSE START ===")
    print(content[:500])
    print("=== GPT RESPONSE END ===")
    
    # Очистка
    content = content.strip()
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'^```\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
        print(f"Content: {content[:200]}")
        
        # Пробуем найти JSON
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        
        # Возвращаем базовую структуру если всё сломалось
        return {
            "summary": "Не удалось проанализировать. Попробуй ещё раз.",
            "topics": [],
            "participants": [],
            "overall_decisions": [],
            "action_items": [],
            "agreements": [],
            "disagreements": [],
            "risks": [],
            "opportunities": [],
            "expert_recommendations": ["Попробуй загрузить файл ещё раз"],
            "next_steps": {"urgent": [], "medium": [], "long": []},
            "meeting_effectiveness": {"score": 0, "comment": "Ошибка анализа"}
        }

def format_summary(analysis: dict) -> str:
    """Форматирует краткое саммари"""
    
    text = "📋 **АНАЛИЗ ВСТРЕЧИ**\n\n"
    text += f"**Резюме:**\n{analysis.get('summary', 'Нет данных')}\n\n"
    
    # Участники
    participants = analysis.get('participants', [])
    if participants:
        text += f"**Участники:** {', '.join(participants)}\n\n"
    
    # Темы
    topics = analysis.get('topics', [])
    if topics:
        text += f"**Обсуждалось {len(topics)} тем:**\n"
        for t in topics:
            percent = t.get('duration_percent', 0)
            text += f"• {t['title']} ({percent}%)\n"
        text += "\n👇 Нажми на тему для подробностей"
    
    # Эффективность
    effectiveness = analysis.get('meeting_effectiveness', {})
    if effectiveness:
        score = effectiveness.get('score', '?')
        text += f"\n\n📊 **Эффективность:** {score}/10"
    
    return text


def format_topic_detail(topic: dict, topic_num: int) -> str:
    """Форматирует детальную информацию по теме"""
    
    text = f"📌 **ТЕМА {topic_num}: {topic['title']}**\n\n"
    
    # Ключевые тезисы
    key_points = topic.get('key_points', [])
    if key_points:
        text += "**Ключевые тезисы:**\n"
        for point in key_points:
            text += f"• {point}\n"
        text += "\n"
    
    # Цитаты
    quotes = topic.get('quotes', [])
    if quotes:
        text += "**Цитаты:**\n"
        for q in quotes:
            author = q.get('author') or 'Участник'
            text += f"💬 \"{q['text']}\" — {author}\n"
        text += "\n"
    
    # Решения по теме
    decisions = topic.get('decisions', [])
    if decisions:
        text += "**Решения:**\n"
        for d in decisions:
            text += f"✅ {d}\n"
        text += "\n"
    
    # Открытые вопросы
    open_q = topic.get('open_questions', [])
    if open_q:
        text += "**Открытые вопросы:**\n"
        for q in open_q:
            text += f"❓ {q}\n"
        text += "\n"
    
    # Комментарий эксперта
    expert = topic.get('expert_comment')
    if expert:
        text += f"🧠 **Цифровой Умник:**\n{expert}\n"
    
    return text


def format_full_analysis(analysis: dict) -> str:
    """Форматирует полный анализ"""
    
    text = "📊 **ПОЛНЫЙ АНАЛИЗ**\n\n"
    
    # Решения
    decisions = analysis.get('overall_decisions', [])
    if decisions:
        text += "**✅ Принятые решения:**\n"
        for d in decisions:
            text += f"• {d}\n"
        text += "\n"
    
    # Action items
    actions = analysis.get('action_items', [])
    if actions:
        text += "**📝 Задачи:**\n"
        for a in actions:
            resp = a.get('responsible') or 'Не назначен'
            deadline = a.get('deadline') or 'Не указан'
            text += f"• {a['task']}\n  → {resp} | {deadline}\n"
        text += "\n"
    
    # Согласия
    agreements = analysis.get('agreements', [])
    if agreements:
        text += "**🤝 Точки согласия:**\n"
        for a in agreements:
            text += f"• {a}\n"
        text += "\n"
    
    # Разногласия
    disagreements = analysis.get('disagreements', [])
    if disagreements:
        text += "**⚡ Разногласия:**\n"
        for d in disagreements:
            text += f"• {d}\n"
        text += "\n"
    
    # Риски
    risks = analysis.get('risks', [])
    if risks:
        text += "**⚠️ Риски:**\n"
        for r in risks:
            text += f"• {r}\n"
        text += "\n"
    
    # Возможности
    opportunities = analysis.get('opportunities', [])
    if opportunities:
        text += "**💡 Возможности:**\n"
        for o in opportunities:
            text += f"• {o}\n"
        text += "\n"
    
    return text


def format_recommendations(analysis: dict) -> str:
    """Форматирует рекомендации"""
    
    text = "🧠 **РЕКОМЕНДАЦИИ ЦИФРОВОГО УМНИКА**\n\n"
    
    # Рекомендации
    recs = analysis.get('expert_recommendations', [])
    if recs:
        for i, r in enumerate(recs, 1):
            text += f"{i}. {r}\n\n"
    
    # План действий
    next_steps = analysis.get('next_steps', {})
    if next_steps:
        text += "**📅 План действий:**\n\n"
        
        urgent = next_steps.get('urgent', [])
        if urgent:
            text += "🔴 **Срочно (1-7 дней):**\n"
            for u in urgent:
                text += f"• {u}\n"
            text += "\n"
        
        medium = next_steps.get('medium', [])
        if medium:
            text += "🟡 **Среднесрок (1-4 недели):**\n"
            for m in medium:
                text += f"• {m}\n"
            text += "\n"
        
        long = next_steps.get('long', [])
        if long:
            text += "🟢 **Долгосрок (1-3 месяца):**\n"
            for l in long:
                text += f"• {l}\n"
    
    return text


def get_topics_keyboard(analysis: dict, user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с темами"""
    
    buttons = []
    topics = analysis.get('topics', [])
    
    for i, topic in enumerate(topics):
        title = topic['title'][:30] + "..." if len(topic['title']) > 30 else topic['title']
        buttons.append([InlineKeyboardButton(
            f"📌 {i+1}. {title}",
            callback_data=f"topic_{user_id}_{i}"
        )])
    
    buttons.append([
        InlineKeyboardButton("📊 Полный анализ", callback_data=f"full_{user_id}"),
        InlineKeyboardButton("🧠 Советы", callback_data=f"recs_{user_id}")
    ])
    
    return InlineKeyboardMarkup(buttons)


def get_back_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ К списку тем", callback_data=f"back_{user_id}")]
    ])


def get_language_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    buttons = []
    for code, name in LANGUAGES.items():
        buttons.append([InlineKeyboardButton(name, callback_data=f"lang_{user_id}_{code}")])
    return InlineKeyboardMarkup(buttons)


# ============= HANDLERS =============

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply(
        "👋 Привет! Я **Цифровой Умник**.\n\n"
        "Отправь мне:\n"
        "• 🎤 Аудио или голосовое сообщение\n"
        "• 🎬 Видеофайл\n"
        "• 🔗 Ссылку на YouTube\n"
        "• 🌐 Прямую ссылку на аудио/видео\n\n"
        "Я проанализирую встречу и разобью на темы!"
    )


@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def link_handler(client: Client, message: Message):
    """Обработка ссылок"""
    
    text = message.text.strip()
    
    # Проверяем YouTube
    youtube_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
    is_youtube = re.match(youtube_pattern, text)
    
    # Проверяем прямую ссылку
    url_pattern = r'https?://[^\s]+'
    is_url = re.match(url_pattern, text)
    
    if is_youtube or is_url:
        user_data[message.from_user.id] = {
            "type": "youtube" if is_youtube else "url",
            "source": text,
            "message_id": message.id
        }
        
        await message.reply(
            "🌐 **Выбери язык результата:**",
            reply_markup=get_language_keyboard(message.from_user.id)
        )
    else:
        await message.reply(
            "Отправь мне аудио, видео или ссылку на YouTube 🎤"
        )


@app.on_message((filters.audio | filters.voice | filters.video | filters.video_note | filters.document) & filters.private)
async def media_handler(client: Client, message: Message):
    """Обработка медиафайлов"""
    
    user_data[message.from_user.id] = {
        "type": "file",
        "message": message,
        "message_id": message.id
    }
    
    await message.reply(
        "🌐 **На каком языке хочешь получить анализ?**",
        reply_markup=get_language_keyboard(message.from_user.id)
    )



@app.on_callback_query(filters.regex(r"^lang_"))
@app.on_callback_query(filters.regex(r"^lang_"))
async def language_callback(client: Client, callback: CallbackQuery):
    """Обработка выбора языка"""
    
    parts = callback.data.split("_")
    user_id = int(parts[1])
    lang_code = parts[2]
    
    if callback.from_user.id != user_id:
        await callback.answer("Это не твой запрос!", show_alert=True)
        return
    
    if user_id not in user_data:
        await callback.answer("Сессия истекла. Отправь файл заново.", show_alert=True)
        return
    
    data = user_data[user_id]
    data["language"] = lang_code
    
    await callback.message.edit_text(
        f"✅ Язык: {LANGUAGES[lang_code]}\n\n⏳ Начинаю обработку..."
    )
    
    file_path = None
    
    try:
        # Скачиваем файл
        if data["type"] == "youtube":
            await callback.message.edit_text(
                f"✅ Язык: {LANGUAGES[lang_code]}\n\n📥 Скачиваю с YouTube..."
            )
            file_path = await download_youtube(data["source"])
            if not file_path:
                await callback.message.edit_text("❌ Не удалось скачать видео с YouTube")
                return
                
        elif data["type"] == "url":
            await callback.message.edit_text(
                f"✅ Язык: {LANGUAGES[lang_code]}\n\n📥 Скачиваю файл..."
            )
            file_path = await download_from_url(data["source"])
            if not file_path:
                await callback.message.edit_text("❌ Не удалось скачать файл")
                return
                
        elif data["type"] == "file":
            await callback.message.edit_text(
                f"✅ Язык: {LANGUAGES[lang_code]}\n\n📥 Скачиваю файл..."
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                file_path = await data["message"].download(tmp.name)
        
        # Транскрибируем
        await callback.message.edit_text(
            f"✅ Язык: {LANGUAGES[lang_code]}\n\n🎤 Распознаю речь..."
        )
        transcript = await transcribe_audio(file_path)
        
        if not transcript or len(transcript) < 50:
            await callback.message.edit_text("❌ Не удалось распознать речь. Проверь качество аудио.")
            return
        
        # Анализируем
        await callback.message.edit_text(
            f"✅ Язык: {LANGUAGES[lang_code]}\n\n🧠 Анализирую содержание..."
        )
        analysis = await analyze_meeting(transcript, lang_code)
        
        # Сохраняем результат
        user_data[user_id]["analysis"] = analysis
        user_data[user_id]["transcript"] = transcript
        
        # Отправляем результат
        await callback.message.edit_text(
            format_summary(analysis),
            reply_markup=get_topics_keyboard(analysis, user_id),
            parse_mode="Markdown"
        )
        
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
        await callback.message.edit_text("❌ Ошибка анализа. Попробуй ещё раз.")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {type(e).__name__}")
    finally:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
@app.on_callback_query(filters.regex(r"^topic_"))
async def topic_callback(client: Client, callback: CallbackQuery):
    """Показать детали темы"""
    
    parts = callback.data.split("_")
    user_id = int(parts[1])
    topic_idx = int(parts[2])
    
    if callback.from_user.id != user_id:
        await callback.answer("Это не твой запрос!", show_alert=True)
        return
    
    if user_id not in user_data or "analysis" not in user_data[user_id]:
        await callback.answer("Сессия истекла", show_alert=True)
        return
    
    analysis = user_data[user_id]["analysis"]
    topics = analysis.get("topics", [])
    
    if topic_idx >= len(topics):
        await callback.answer("Тема не найдена", show_alert=True)
        return
    
    topic = topics[topic_idx]
    
    await callback.message.edit_text(
        format_topic_detail(topic, topic_idx + 1),
        reply_markup=get_back_keyboard(user_id),
        parse_mode="Markdown"
    )


@app.on_callback_query(filters.regex(r"^full_"))
async def full_callback(client: Client, callback: CallbackQuery):
    """Показать полный анализ"""
    
    user_id = int(callback.data.split("_")[1])
    
    if callback.from_user.id != user_id:
        await callback.answer("Это не твой запрос!", show_alert=True)
        return
    
    if user_id not in user_data or "analysis" not in user_data[user_id]:
        await callback.answer("Сессия истекла", show_alert=True)
        return
    
    analysis = user_data[user_id]["analysis"]
    
    await callback.message.edit_text(
        format_full_analysis(analysis),
        reply_markup=get_back_keyboard(user_id),
        parse_mode="Markdown"
    )


@app.on_callback_query(filters.regex(r"^recs_"))
async def recs_callback(client: Client, callback: CallbackQuery):
    """Показать рекомендации"""
    
    user_id = int(callback.data.split("_")[1])
    
    if callback.from_user.id != user_id:
        await callback.answer("Это не твой запрос!", show_alert=True)
        return
    
    if user_id not in user_data or "analysis" not in user_data[user_id]:
        await callback.answer("Сессия истекла", show_alert=True)
        return
    
    analysis = user_data[user_id]["analysis"]
    
    await callback.message.edit_text(
        format_recommendations(analysis),
        reply_markup=get_back_keyboard(user_id),
        parse_mode="Markdown"
    )


@app.on_callback_query(filters.regex(r"^back_"))
async def back_callback(client: Client, callback: CallbackQuery):
    """Вернуться к списку тем"""
    
    user_id = int(callback.data.split("_")[1])
    
    if callback.from_user.id != user_id:
        await callback.answer("Это не твой запрос!", show_alert=True)
        return
    
    if user_id not in user_data or "analysis" not in user_data[user_id]:
        await callback.answer("Сессия истекла", show_alert=True)
        return
    
    analysis = user_data[user_id]["analysis"]
    
    await callback.message.edit_text(
        format_summary(analysis),
        reply_markup=get_topics_keyboard(analysis, user_id),
        parse_mode="Markdown"
    )


# ============= RUN =============
if __name__ == "__main__":
    print("Starting Цифровой Умник...")
    app.run()
