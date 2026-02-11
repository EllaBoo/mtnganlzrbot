#!/usr/bin/env python3
"""
MTNGanlzrBot — Standalone Meeting Analyzer
Audio/Video → Transcription → Expert Analysis → Dynamics
Direct ffmpeg + Deepgram + OpenAI (no external services)

Версия с интеграцией:
- Железные правила (не выдумывать, не создавать ложных конфликтов)
- Анализ динамики беседы (для 2+ участников)
- Диаризация (определение спикеров)
"""
import asyncio
import logging
import os
import re
import json
import subprocess
import tempfile
import httpx
from datetime import datetime
from openai import AsyncOpenAI

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ChatAction, ParseMode

from pyrogram import Client as PyroClient

from config import config
from report_generator import generate_pdf_report, generate_html_report, safe_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
)
logger = logging.getLogger("bot")

pyro_client = None
openai_client = None

# ==========================================
# ТЁПЛЫЕ СООБЩЕНИЯ
# ==========================================
BOT_MESSAGES = {
    "ru": {
        "file_received": "💪 Тащу файл...",
        "extracting": "🎵 Извлекаю аудио...",
        "transcribing": "🎧 Слушаю внимательно...",
        "analyzing": "🧠 Повезло, я как раз в этом профи...",
        "analyzing_dynamics": "🔮 Анализирую динамику беседы...",
        "generating": "✨ Собираю мысли...",
        "done": "🎁 Вуаля! Ваш отчёт готов",
        "error": "😅 Упс, что-то пошло не так",
        "language_prompt": "🌍 На каком языке хотите получить результат?",
        "language_selected": "👍 Отлично! Готовлю отчёт",
        "no_speech": "🤔 Не удалось разобрать речь",
        "audio_failed": "❌ Не удалось извлечь аудио",
        "download_failed": "❌ Не удалось скачать",
        "yt_downloading": "📥 Скачиваю с YouTube...",
        "yt_done": "✅ Скачано!",
    },
    "en": {
        "file_received": "💪 Grabbing the file...",
        "extracting": "🎵 Extracting audio...",
        "transcribing": "🎧 Listening carefully...",
        "analyzing": "🧠 Lucky you, I'm a pro at this...",
        "analyzing_dynamics": "🔮 Analyzing conversation dynamics...",
        "generating": "✨ Gathering my thoughts...",
        "done": "🎁 Voilà! Your report is ready",
        "error": "😅 Oops, something went wrong",
        "language_prompt": "🌍 What language would you like the result in?",
        "language_selected": "👍 Great! Preparing your report",
        "no_speech": "🤔 Couldn't recognize speech",
        "audio_failed": "❌ Failed to extract audio",
        "download_failed": "❌ Failed to download",
        "yt_downloading": "📥 Downloading from YouTube...",
        "yt_done": "✅ Downloaded!",
    },
    "kk": {
        "file_received": "💪 Файлды алып жатырмын...",
        "extracting": "🎵 Аудио шығарып жатырмын...",
        "transcribing": "🎧 Мұқият тыңдап жатырмын...",
        "analyzing": "🧠 Сәттілік, мен бұл салада маманмын...",
        "analyzing_dynamics": "🔮 Әңгіме динамикасын талдау...",
        "generating": "✨ Ойларымды жинап жатырмын...",
        "done": "🎁 Міне! Есебіңіз дайын",
        "error": "😅 Қап, бірдеңе дұрыс болмады",
        "language_prompt": "🌍 Нәтижені қай тілде алғыңыз келеді?",
        "language_selected": "👍 Тамаша! Есеп дайындап жатырмын",
        "no_speech": "🤔 Сөйлеуді анықтай алмадым",
        "audio_failed": "❌ Аудио шығара алмадым",
        "download_failed": "❌ Жүктей алмадым",
        "yt_downloading": "📥 YouTube-тен жүктеп жатырмын...",
        "yt_done": "✅ Жүктелді!",
    },
    "es": {
        "file_received": "💪 Tomando el archivo...",
        "extracting": "🎵 Extrayendo audio...",
        "transcribing": "🎧 Escuchando atentamente...",
        "analyzing": "🧠 Qué suerte, soy experto en esto...",
        "analyzing_dynamics": "🔮 Analizando la dinámica de la conversación...",
        "generating": "✨ Organizando mis ideas...",
        "done": "🎁 ¡Voilà! Tu informe está listo",
        "error": "😅 Ups, algo salió mal",
        "language_prompt": "🌍 ¿En qué idioma quieres el resultado?",
        "language_selected": "👍 ¡Genial! Preparando tu informe",
        "no_speech": "🤔 No pude reconocer el habla",
        "audio_failed": "❌ No se pudo extraer el audio",
        "download_failed": "❌ No se pudo descargar",
        "yt_downloading": "📥 Descargando de YouTube...",
        "yt_done": "✅ ¡Descargado!",
    },
}

# Язык → код для Deepgram
LANG_TO_DEEPGRAM = {
    "ru": "ru",
    "en": "en",
    "kk": "kk",
    "es": "es",
    "auto": "ru",  # fallback
}


def get_msg(lang: str, key: str) -> str:
    """Получить сообщение на нужном языке"""
    return BOT_MESSAGES.get(lang, BOT_MESSAGES["ru"]).get(key, BOT_MESSAGES["ru"].get(key, key))


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора языка"""
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        ],
        [
            InlineKeyboardButton("🔄 Язык оригинала", callback_data="lang_auto"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def on_startup(app: Application):
    global pyro_client, openai_client
    if config.API_ID and config.API_HASH:
        pyro_client = PyroClient(
            "bot_downloader",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            no_updates=True,
            in_memory=True,
        )
        await pyro_client.start()
        logger.info("Pyrogram started (large file support)")
    else:
        logger.warning("No API_ID/API_HASH — max 20MB files")
    if config.OPENAI_API_KEY:
        openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("OpenAI client ready")


async def on_shutdown(app: Application):
    global pyro_client
    if pyro_client:
        await pyro_client.stop()


async def download_file(file_id: str, dest: str, update: Update) -> bool:
    try:
        if pyro_client:
            await pyro_client.download_media(file_id, file_name=dest)
        else:
            f = await update.get_bot().get_file(file_id)
            await f.download_to_drive(dest)
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False


def extract_audio(input_path: str):
    output = input_path.rsplit(".", 1)[0] + "_audio.wav"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", output],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0 and os.path.exists(output):
            size_mb = os.path.getsize(output) / (1024 * 1024)
            logger.info(f"Audio extracted: {size_mb:.1f} MB")
            return output
        logger.error(f"ffmpeg error: {result.stderr[:500]}")
        return None
    except Exception as e:
        logger.error(f"ffmpeg failed: {e}")
        return None


async def transcribe_audio(audio_path: str, lang: str = "ru"):
    """Транскрипция с диаризацией (определение спикеров)"""
    if not config.DEEPGRAM_API_KEY:
        logger.error("No DEEPGRAM_API_KEY!")
        return None, None, 1
    url = "https://api.deepgram.com/v1/listen"
    
    deepgram_lang = LANG_TO_DEEPGRAM.get(lang, "ru")
    if lang == "auto":
        deepgram_lang = "ru"
    
    params = {
        "model": "nova-2",
        "language": deepgram_lang,
        "smart_format": "true",
        "punctuate": "true",
        "paragraphs": "true",
        "diarize": "true",  # ← ДИАРИЗАЦИЯ: определение спикеров
        "detect_language": "true" if lang == "auto" else "false",
    }
    try:
        file_size = os.path.getsize(audio_path)
        logger.info(f"Sending {file_size / 1024 / 1024:.1f} MB to Deepgram (with diarization)...")
        async with httpx.AsyncClient(timeout=600.0) as client:
            with open(audio_path, "rb") as f:
                resp = await client.post(
                    url, params=params,
                    headers={
                        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
                        "Content-Type": "audio/wav",
                    },
                    content=f.read(),
                )
        if resp.status_code != 200:
            logger.error(f"Deepgram {resp.status_code}: {resp.text[:300]}")
            return None, None, 1
        data = resp.json()
        
        # Определяем язык
        detected_lang = lang
        if lang == "auto":
            detected = data.get("results", {}).get("channels", [{}])[0].get("detected_language", "ru")
            detected_lang = detected if detected in BOT_MESSAGES else "ru"
        
        channels = data.get("results", {}).get("channels", [])
        if not channels:
            return None, detected_lang, 1
        alternatives = channels[0].get("alternatives", [])
        if not alternatives:
            return None, detected_lang, 1
        
        # Подсчёт спикеров из диаризации
        speakers = set()
        words = alternatives[0].get("words", [])
        for word in words:
            speaker = word.get("speaker")
            if speaker is not None:
                speakers.add(speaker)
        num_speakers = len(speakers) if speakers else 1
        logger.info(f"Detected {num_speakers} speaker(s)")
        
        # Текст с параграфами
        paragraphs = alternatives[0].get("paragraphs", {})
        if paragraphs and paragraphs.get("paragraphs"):
            parts = []
            for p in paragraphs["paragraphs"]:
                speaker = p.get("speaker", 0)
                speaker_label = f"[Спикер {speaker + 1}] " if num_speakers > 1 else ""
                for s in p.get("sentences", []):
                    parts.append(f"{speaker_label}{s.get('text', '')}")
                parts.append("")
            text = "\n".join(parts).strip()
        else:
            text = alternatives[0].get("transcript", "")
        
        logger.info(f"Transcribed: {len(text)} chars, {len(text.split())} words, {num_speakers} speakers")
        return text, detected_lang, num_speakers
    except Exception as e:
        logger.error(f"Deepgram error: {e}")
        return None, None, 1


# ==========================================
# ПРОМПТ С ЖЕЛЕЗНЫМИ ПРАВИЛАМИ
# ==========================================
ANALYSIS_PROMPT_JSON = """Ты — экспертный аналитик. Проанализируй транскрипцию и верни ТОЛЬКО валидный JSON.

Язык ответа: {lang_name}

═══ ЖЕЛЕЗНЫЕ ПРАВИЛА ═══
1. НИЧЕГО НЕ ВЫДУМЫВАЙ. Опирайся ТОЛЬКО на то, что реально сказано в транскрипции.
   Если информации нет — так и напиши. Лучше честный пробел, чем красивая выдумка.
2. Не приписывай участникам слова, мнения или намерения, которых они не выражали.
3. Если участники согласны между собой — отрази это. НЕ создавай видимость конфликта,
   спора или расхождений там, где их нет. Единодушие — это тоже важный результат.
4. Цитируй только реальные высказывания из транскрипции.
5. Если что-то неясно или неоднозначно — укажи это как открытый вопрос, а не додумывай.
6. Пустой массив лучше, чем высосанные из пальца данные.
═══════════════════════

Структура JSON:
{{
  "title": "Краткое название встречи",
  "executive_summary": "2-3 предложения о сути встречи",
  "context": {{
    "industry": "Сфера/индустрия",
    "meeting_type": "Тип встречи",
    "complexity": "Низкий/Средний/Высокий"
  }},
  "goals": {{
    "explicit": ["явная цель 1", "явная цель 2"],
    "hidden": ["скрытая цель 1"]
  }},
  "key_topics": [
    {{"topic": "Тема 1", "details": "Подробности"}},
    {{"topic": "Тема 2", "details": "Подробности"}}
  ],
  "positions": {{
    "side_a": {{"label": "Сторона А", "position": "Позиция", "interests": "Интересы"}},
    "side_b": {{"label": "Сторона Б", "position": "Позиция", "interests": "Интересы"}}
  }},
  "agreement_points": ["точка согласия 1"],
  "disagreement_points": ["точка расхождения 1"],
  "decisions": ["решение 1", "решение 2"],
  "action_items": [
    {{"task": "Задача", "responsible": "Кто", "deadline": "Когда"}}
  ],
  "swot": {{
    "strengths": ["сильная сторона"],
    "weaknesses": ["слабая сторона — ТОЛЬКО если реально есть"],
    "opportunities": ["возможность"],
    "threats": ["угроза — ТОЛЬКО если реально обоснована"]
  }},
  "recommendations": {{
    "substance": ["рекомендация по существу"],
    "methodology": ["методологическая рекомендация"]
  }},
  "risks": [
    {{"risk": "Риск — ТОЛЬКО реальный", "severity": "Высокая/Средняя/Низкая", "mitigation": "Как снизить"}}
  ],
  "open_questions": ["вопрос 1"],
  "action_plan": {{
    "urgent": ["срочно 1-7 дней"],
    "medium": ["среднесрок 1-4 недели"],
    "long_term": ["долгосрок 1-3 месяца"]
  }},
  "kpi": ["KPI 1"],
  "participants_count": 0,
  "conclusion": {{
    "main_insight": "Главный инсайт",
    "key_recommendation": "Ключевая рекомендация",
    "forecast": "Прогноз"
  }}
}}

⚠️ Помни: если встреча прошла конструктивно и без конфликтов — так и напиши.
Не каждая встреча нуждается в списке «что улучшить».

Верни ТОЛЬКО JSON, без markdown, без ```json, без пояснений."""


# ==========================================
# АНАЛИЗ ДИНАМИКИ БЕСЕДЫ
# ==========================================
DYNAMICS_ANALYSIS_PROMPT = """Ты — организационный психолог и эксперт по групповой динамике.

Проанализируй транскрипцию на предмет СКРЫТОЙ ДИНАМИКИ разговора — то, что обычно
остаётся «между строк». Это гипотетический анализ, основанный на речевых паттернах.

Аспекты для анализа:
1. РАСПРЕДЕЛЕНИЕ ВЛИЯНИЯ — кто задаёт направление, кто соглашается, чьё мнение игнорируется
2. ПЕРЕБИВАНИЯ — конструктивные дополнения или попытки доминировать
3. МАРКЕРЫ НАПРЯЖЕНИЯ — хеджирование, пассивная агрессия, уклончивые ответы
4. НЕВЫСКАЗАННОЕ — темы, которые замяли или избегают
5. КОАЛИЦИИ — кто поддерживает чьи идеи
6. ЭМОЦИОНАЛЬНЫЕ СДВИГИ — моменты смены тона
7. СТИЛИ КОММУНИКАЦИИ — факты vs эмоции, «мы»/«я»/«вы»

═══ КРИТИЧЕСКИ ВАЖНО ═══
1. Это ГИПОТЕТИЧЕСКИЙ анализ. Формулируй как «может указывать на...», «возможно...».
2. НИЧЕГО НЕ ВЫДУМЫВАЙ. Каждое наблюдение — с цитатой из транскрипции.
3. Здоровая динамика = тоже результат. Не ищи проблемы где их нет.
4. Анализируй ПАТТЕРНЫ, не людей.
═══════════════════════

Язык: {language}
Участников: {participants}

JSON:
{{
    "overall_atmosphere": {{
        "summary": "Краткое описание атмосферы",
        "tension_level": "low/moderate/elevated/high",
        "collaboration_quality": "high/moderate/low",
        "energy": "energetic/balanced/flat/tense"
    }},
    "power_dynamics": [{{"observation": "", "evidence": "", "confidence": "high/medium/low"}}],
    "tension_markers": [{{"type": "hedging/passive_aggression/evasion", "observation": "", "evidence": "", "confidence": ""}}],
    "healthy_patterns": ["здоровый паттерн 1"],
    "key_observations": ["наблюдение 1 — только high confidence"]
}}

⚠️ Если аспект НЕ обнаружен — пустой массив []. Не заполняй ради заполнения.

Транскрипция:
{text}"""


LANG_NAMES = {
    "ru": "русский",
    "en": "English",
    "kk": "қазақ тілі",
    "es": "español",
}


async def analyze_text_json(text: str, lang: str = "ru") -> dict:
    """Анализ текста с возвратом структурированного JSON"""
    if not openai_client:
        return None
    max_chars = 100_000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...текст обрезан...]"
    
    lang_name = LANG_NAMES.get(lang, "русский")
    prompt = ANALYSIS_PROMPT_JSON.format(lang_name=lang_name)
    
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Транскрипция:\n\n{text}"},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        content = resp.choices[0].message.content
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return None


async def analyze_dynamics(text: str, num_speakers: int, lang: str = "ru") -> dict:
    """Анализ скрытой динамики беседы (только для 2+ участников)"""
    if num_speakers < 2:
        return None
    
    if not openai_client:
        return None
    
    max_chars = 20_000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[...текст обрезан...]"
    
    prompt = DYNAMICS_ANALYSIS_PROMPT.format(
        language=LANG_NAMES.get(lang, "русский"),
        participants=num_speakers,
        text=text
    )
    
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты — организационный психолог. Отвечай ТОЛЬКО валидным JSON. Если динамика здоровая — так и скажи."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error(f"Dynamics analysis error: {e}")
        return None


def format_dynamics_summary(dynamics: dict, lang: str = "ru") -> str:
    """Форматирует краткое summary динамики для чата"""
    if not dynamics:
        return ""
    
    lines = []
    atm = dynamics.get("overall_atmosphere", {})
    
    # Уровень напряжения
    tension_map = {
        "low": "🟢 спокойная",
        "moderate": "🟡 умеренное напряжение", 
        "elevated": "🟠 повышенное напряжение",
        "high": "🔴 высокое напряжение"
    }
    tension = tension_map.get(atm.get("tension_level", ""), "")
    if tension:
        lines.append(f"**Атмосфера:** {tension}")
    
    # Summary
    if atm.get("summary"):
        lines.append(atm["summary"])
    
    # Ключевые наблюдения (только high confidence)
    key_obs = dynamics.get("key_observations", [])
    if key_obs:
        lines.append("\n**Ключевые наблюдения:**")
        for obs in key_obs[:3]:
            lines.append(f"  ⚡ {obs}")
    
    # Здоровые паттерны
    healthy = dynamics.get("healthy_patterns", [])
    if healthy:
        lines.append(f"\n**Здоровые паттерны:** {', '.join(healthy[:3])}")
    
    return "\n".join(lines)


def has_notable_dynamics(dynamics: dict) -> bool:
    """Проверяет есть ли что показывать по динамике"""
    if not dynamics:
        return False
    atm = dynamics.get("overall_atmosphere", {})
    if atm.get("tension_level") in ("n/a", "unknown", None):
        return False
    # Есть что-то интересное?
    return (
        len(dynamics.get("power_dynamics", [])) > 0 or
        len(dynamics.get("tension_markers", [])) > 0 or
        len(dynamics.get("key_observations", [])) > 0 or
        len(dynamics.get("healthy_patterns", [])) > 0
    )


async def process_content(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                          file_path: str):
    """Обработка контента после выбора языка"""
    chat = update.effective_chat
    lang = ctx.user_data.get("output_language", "ru")
    
    msg = await update.message.reply_text(get_msg(lang, "file_received"))
    audio_path = None
    try:
        await msg.edit_text(get_msg(lang, "extracting"))
        await chat.send_action(ChatAction.TYPING)
        audio_path = await asyncio.get_event_loop().run_in_executor(
            None, extract_audio, file_path
        )
        if not audio_path:
            await msg.edit_text(get_msg(lang, "audio_failed"))
            return

        await msg.edit_text(get_msg(lang, "transcribing"))
        await chat.send_action(ChatAction.TYPING)
        
        # Транскрипция с диаризацией
        text, detected_lang, num_speakers = await transcribe_audio(audio_path, lang)
        
        if lang == "auto" and detected_lang:
            lang = detected_lang
            ctx.user_data["output_language"] = lang
        
        if not text or len(text) < 20:
            await msg.edit_text(get_msg(lang, "no_speech"))
            return

        word_count = len(text.split())
        await msg.edit_text(get_msg(lang, "analyzing"))
        await chat.send_action(ChatAction.TYPING)
        
        # Основной анализ
        analysis = await analyze_text_json(text, lang)
        
        # Анализ динамики (только для 2+ участников)
        dynamics = None
        if num_speakers >= 2:
            await msg.edit_text(get_msg(lang, "analyzing_dynamics"))
            dynamics = await analyze_dynamics(text, num_speakers, lang)
        
        if not analysis:
            # Fallback — отправляем просто текст
            await msg.edit_text(f"🧠 Анализ завершён\n📝 Слов: {word_count:,}")
            trans_file = tempfile.mktemp(suffix=".txt")
            with open(trans_file, "w", encoding="utf-8") as f:
                f.write(f"=== Транскрипция ({word_count} слов) ===\n\n{text}")
            with open(trans_file, "rb") as f:
                await update.message.reply_document(
                    InputFile(f, filename="transcript.txt"),
                    caption=f"📄 Транскрипция ({word_count:,} слов)"
                )
            os.unlink(trans_file)
            return

        await msg.edit_text(get_msg(lang, "generating"))
        await chat.send_action(ChatAction.UPLOAD_DOCUMENT)

        # Генерируем название файла
        title = analysis.get("title", "Анализ встречи")
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_filename = f"{safe_filename(title)}_{date_str}"

        # 1. Транскрипт TXT
        trans_file = tempfile.mktemp(suffix=".txt")
        with open(trans_file, "w", encoding="utf-8") as f:
            f.write(f"=== Транскрипция ({word_count} слов, {num_speakers} спикер(ов)) ===\n\n{text}")

        # 2. PDF отчёт
        pdf_path = generate_pdf_report(analysis, lang)

        # 3. HTML артефакт
        html_content = generate_html_report(analysis, lang)
        html_path = tempfile.mktemp(suffix=".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Формируем summary для чата
        summary_lines = [get_msg(lang, "done")]
        summary_lines.append(f"\n📋 **{title}**")
        
        exec_summary = analysis.get("executive_summary", "")
        if exec_summary:
            summary_lines.append(f"\n{exec_summary}")
        
        summary_lines.append(f"\n📊 **Статистика:** {word_count:,} слов, {num_speakers} спикер(ов)")
        
        # Ключевые решения
        decisions = analysis.get("decisions", [])
        if decisions:
            summary_lines.append("\n🎯 **Решения:**")
            for d in decisions[:3]:
                summary_lines.append(f"  ✅ {d}")
        
        # Динамика беседы (если есть)
        if dynamics and has_notable_dynamics(dynamics):
            dyn_summary = format_dynamics_summary(dynamics, lang)
            if dyn_summary:
                summary_lines.append(f"\n🔮 **Динамика беседы:**\n{dyn_summary}")
        
        await msg.edit_text("\n".join(summary_lines), parse_mode=ParseMode.MARKDOWN)

        # Отправляем PDF
        with open(pdf_path, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename=f"{base_filename}.pdf"),
                caption="📊 Экспертный отчёт (PDF)"
            )

        # Отправляем HTML
        with open(html_path, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename=f"{base_filename}.html"),
                caption="🌐 Интерактивный отчёт (HTML)"
            )

        # Отправляем транскрипт
        with open(trans_file, "rb") as f:
            await update.message.reply_document(
                InputFile(f, filename="transcript.txt"),
                caption=f"📝 Транскрипция ({word_count:,} слов)"
            )

        # Cleanup
        for p in [trans_file, pdf_path, html_path]:
            if p and os.path.exists(p):
                os.unlink(p)

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        await msg.edit_text(
            f"{get_msg(lang, 'error')}: <code>{str(e)[:300]}</code>",
            parse_mode=ParseMode.HTML
        )
    finally:
        for p in [file_path, audio_path]:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except Exception:
                    pass


# ==========================================
# ОБРАБОТЧИКИ ФАЙЛОВ — СНАЧАЛА СПРАШИВАЕМ ЯЗЫК
# ==========================================

async def save_file_and_ask_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE, 
                                      file_id: str, file_ext: str):
    """Сохраняем файл и спрашиваем язык"""
    tmp = tempfile.mktemp(suffix=file_ext)
    if not await download_file(file_id, tmp, update):
        await update.message.reply_text("❌ Не удалось скачать файл")
        return
    
    ctx.user_data["pending_file"] = tmp
    
    await update.message.reply_text(
        "🌍 На каком языке хотите получить результат?",
        reply_markup=get_language_keyboard()
    )


async def handle_language_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора языка"""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.replace("lang_", "")
    ctx.user_data["output_language"] = lang
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    file_path = ctx.user_data.get("pending_file")
    if not file_path or not os.path.exists(file_path):
        await query.message.reply_text("❌ Файл не найден, отправьте заново")
        return
    
    original_message = ctx.user_data.get("original_message")
    if original_message:
        update._effective_message = original_message
    
    await process_content(update, ctx, file_path)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 <b>Цифровой Умник</b>\n\n"
        "Отправь мне:\n"
        "🎤 Голосовое сообщение\n"
        "🎵 Аудио файл\n"
        "🎬 Видео файл\n"
        "🔗 Ссылку на YouTube\n\n"
        "Я транскрибирую, проанализирую и создам:\n"
        "📄 PDF-отчёт\n"
        "🌐 Интерактивный HTML\n"
        "📝 Транскрипцию\n"
        "🔮 Анализ динамики (для 2+ участников)\n\n"
        "Файлы до 2 GB.",
        parse_mode=ParseMode.HTML
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Как использовать:</b>\n\n"
        "1. Отправь аудио/видео/голосовое\n"
        "2. Выбери язык результата\n"
        "3. Deepgram транскрибирует (с определением спикеров)\n"
        "4. GPT-4o анализирует (с железными правилами)\n"
        "5. Получаешь PDF + HTML + TXT\n\n"
        "🔮 Для записей с 2+ участниками — анализ динамики беседы\n\n"
        "Файлы до 2 GB через Pyrogram.",
        parse_mode=ParseMode.HTML
    )


async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    if not voice:
        return
    ext = ".ogg" if update.message.voice else ".mp3"
    ctx.user_data["original_message"] = update.message
    await save_file_and_ask_language(update, ctx, voice.file_id, ext)


async def handle_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.video_note
    if not video:
        return
    ctx.user_data["original_message"] = update.message
    await save_file_and_ask_language(update, ctx, video.file_id, ".mp4")


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return
    mime = doc.mime_type or ""
    fname = (doc.file_name or "").lower()
    ok_mime = ("audio", "video", "ogg", "mp4", "mp3", "wav", "m4a",
               "webm", "mpeg", "flac", "aac", "opus")
    ok_ext = (".mp3", ".mp4", ".m4a", ".ogg", ".wav", ".webm", ".flac",
              ".aac", ".mov", ".avi", ".mkv", ".wma", ".opus", ".oga")
    if not (any(t in mime for t in ok_mime) or
            any(fname.endswith(e) for e in ok_ext)):
        await update.message.reply_text("🤔 Отправь аудио или видео файл.")
        return
    size_mb = (doc.file_size or 0) / (1024 * 1024)
    if size_mb > config.MAX_FILE_MB:
        await update.message.reply_text(f"📦 Макс. {config.MAX_FILE_MB} MB.")
        return
    logger.info(f"Downloading: {doc.file_name} ({size_mb:.1f} MB)")
    ext = os.path.splitext(doc.file_name or "file.mp4")[1] or ".mp4"
    ctx.user_data["original_message"] = update.message
    await save_file_and_ask_language(update, ctx, doc.file_id, ext)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    yt = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/\S+)', text)
    if yt:
        url = yt.group(1)
        msg = await update.message.reply_text("📥 Скачиваю с YouTube...")
        try:
            tmp = tempfile.mktemp(suffix=".m4a")
            r = subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "m4a", "-o", tmp, url],
                capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0 and os.path.exists(tmp):
                await msg.edit_text("✅ Скачано!")
                ctx.user_data["pending_file"] = tmp
                ctx.user_data["original_message"] = update.message
                await update.message.reply_text(
                    "🌍 На каком языке хотите получить результат?",
                    reply_markup=get_language_keyboard()
                )
            else:
                await msg.edit_text(f"❌ Ошибка YouTube:\n<code>{r.stderr[:200]}</code>",
                                    parse_mode=ParseMode.HTML)
        except Exception as e:
            await msg.edit_text(f"❌ {str(e)[:200]}")
        return
    await update.message.reply_text(
        "🤔 Отправь аудио, видео, голосовое или ссылку на YouTube."
    )


async def error_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {ctx.error}", exc_info=ctx.error)


def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.post_init = on_startup
    app.post_shutdown = on_shutdown
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CallbackQueryHandler(handle_language_callback, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    logger.info("Bot started!")
    logger.info(f"  Pyrogram: {'yes' if config.API_ID else 'no'}")
    logger.info(f"  Deepgram: {'yes' if config.DEEPGRAM_API_KEY else 'NO!'}")
    logger.info(f"  OpenAI: {'yes' if config.OPENAI_API_KEY else 'NO!'}")
    logger.info("  Features: Iron Rules ✓, Diarization ✓, Dynamics Analysis ✓")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
v4: Iron Rules + Diarization + Dynamics Analysis
