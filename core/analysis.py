"""Базовый AI-анализ транскрипции."""

import json, logging
from openai import AsyncOpenAI
import config
from core.prompts import BASIC_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def analyze_text(text: str, language: str = "ru") -> dict:
    """Базовый анализ: резюме, темы, выводы, тон."""
    prompt = BASIC_ANALYSIS_PROMPT.format(language=language, text=text[:15000])
    try:
        resp = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Отвечай ТОЛЬКО валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3, max_tokens=3000,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        return {
            "summary": result.get("summary", ""),
            "main_topics": result.get("main_topics", []),
            "key_conclusions": result.get("key_conclusions", []),
            "tone": result.get("tone", "нейтральный"),
            "participants": result.get("participants", 1),
        }
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        return {"summary": "Ошибка анализа", "main_topics": [], "key_conclusions": [], "tone": "", "participants": 1}
