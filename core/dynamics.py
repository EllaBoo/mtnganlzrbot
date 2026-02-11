"""Анализ скрытой динамики беседы: влияние, напряжение, коалиции, эмоции."""

import json
import logging
from openai import AsyncOpenAI
import config
from core.prompts import DYNAMICS_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def analyze_dynamics(
    text: str,
    participants: int = 2,
    language: str = "ru",
) -> dict:
    """
    Гипотетический анализ скрытой динамики беседы.
    Возвращает структуру с наблюдениями по 7+ категориям.
    """
    if participants < 2:
        return _solo_result()

    prompt = DYNAMICS_ANALYSIS_PROMPT.format(
        language=language,
        participants=participants,
        text=text[:20000],
    )

    try:
        resp = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — организационный психолог. Анализируешь динамику группового общения. "
                        "Отвечай ТОЛЬКО валидным JSON. Будь честен: если динамика здоровая — так и скажи."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=5000,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        return _normalize(result)
    except Exception as e:
        logger.error(f"Ошибка анализа динамики: {e}")
        return _empty()


def _normalize(data: dict) -> dict:
    """Нормализует структуру, гарантируя наличие всех ключей."""
    atm = data.setdefault("overall_atmosphere", {})
    atm.setdefault("summary", "")
    atm.setdefault("tension_level", "low")
    atm.setdefault("collaboration_quality", "high")
    atm.setdefault("energy", "balanced")

    for key in (
        "power_dynamics", "interruptions", "tension_markers",
        "unspoken", "coalitions", "emotional_shifts",
        "communication_styles", "healthy_patterns", "recommendations",
    ):
        data.setdefault(key, [])

    if atm["tension_level"] == "low":
        data["tension_markers"] = [
            m for m in data["tension_markers"]
            if m.get("confidence") != "low"
        ]

    return data


def _empty() -> dict:
    return {
        "overall_atmosphere": {
            "summary": "Не удалось проанализировать динамику",
            "tension_level": "unknown",
            "collaboration_quality": "unknown",
            "energy": "unknown",
        },
        "power_dynamics": [],
        "interruptions": [],
        "tension_markers": [],
        "unspoken": [],
        "coalitions": [],
        "emotional_shifts": [],
        "communication_styles": [],
        "healthy_patterns": [],
        "recommendations": [],
    }


def _solo_result() -> dict:
    return {
        "overall_atmosphere": {
            "summary": "Монолог — анализ групповой динамики неприменим",
            "tension_level": "n/a",
            "collaboration_quality": "n/a",
            "energy": "n/a",
        },
        "power_dynamics": [],
        "interruptions": [],
        "tension_markers": [],
        "unspoken": [],
        "coalitions": [],
        "emotional_shifts": [],
        "communication_styles": [],
        "healthy_patterns": [],
        "recommendations": [],
    }


def has_notable_dynamics(dynamics: dict) -> bool:
    """Проверяет, есть ли что-то интересное для отображения."""
    if not dynamics:
        return False
    atm = dynamics.get("overall_atmosphere", {})
    if atm.get("tension_level") in ("n/a", "unknown"):
        return False
    count = sum(
        len(dynamics.get(k, []))
        for k in ("power_dynamics", "interruptions", "tension_markers",
                   "unspoken", "coalitions", "emotional_shifts")
    )
    return count > 0


def format_dynamics_summary(dynamics: dict, lang: str = "ru") -> str:
    """Форматирует краткое summary динамики для чата."""
    if not has_notable_dynamics(dynamics):
        return ""

    lines = []
    atm = dynamics.get("overall_atmosphere", {})

    tension_map = {
        "low": "🟢 спокойная",
        "moderate": "🟡 умеренное напряжение",
        "elevated": "🟠 повышенное напряжение",
        "high": "🔴 высокое напряжение",
    }
    tension = tension_map.get(atm.get("tension_level", ""), "")
    if tension:
        lines.append(f"**Атмосфера:** {tension}")

    summary = atm.get("summary", "")
    if summary:
        lines.append(summary)

    high_conf = []
    for key in ("power_dynamics", "interruptions", "tension_markers", "unspoken"):
        for item in dynamics.get(key, []):
            if item.get("confidence") == "high":
                high_conf.append(item.get("observation", ""))
    if high_conf:
        lines.append("\n**Ключевые наблюдения:**")
        for obs in high_conf[:3]:
            lines.append(f"  ⚡ {obs}")

    healthy = dynamics.get("healthy_patterns", [])
    if healthy:
        lines.append(f"\n**Здоровые паттерны:** {', '.join(healthy[:3])}")

    return "\n".join(lines)
