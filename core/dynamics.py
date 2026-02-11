"""Анализ скрытой динамики беседы: влияние, напряжение, коалиции, эмоции."""

import json
import logging
from openai import AsyncOpenAI
import config

# ── Анализ динамики беседы (скрытые паттерны) ───────────
DYNAMICS_ANALYSIS_PROMPT = """Ты — организационный психолог и эксперт по групповой динамике с 20-летним опытом
анализа деловых коммуникаций, фасилитации и медиации.

Проанализируй транскрипцию на предмет СКРЫТОЙ ДИНАМИКИ разговора — то, что обычно
остаётся «между строк». Это гипотетический анализ, основанный на речевых паттернах.

Проанализируй следующие аспекты:

1. РАСПРЕДЕЛЕНИЕ ВЛИЯНИЯ
   - Кто задаёт направление дискуссии (инициатор тем)?
   - Кто в основном соглашается / следует за другими?
   - Кто принимает финальные решения?
   - Есть ли участники, чьё мнение игнорируется?

2. ПЕРЕБИВАНИЯ И КОНКУРЕНЦИЯ ЗА СЛОВО
   - Замечены ли перебивания (незаконченные фразы, резкая смена спикера)?
   - Кто перебивает чаще? Кого перебивают чаще?
   - Это конструктивное дополнение или попытка доминировать?

3. МАРКЕРЫ НАПРЯЖЕНИЯ
   - Хеджирование: чрезмерное «ну», «может быть», «наверное», «я не уверен»
   - Пассивная агрессия: ирония, сарказм, обесценивание чужих идей
   - Уклончивые ответы: вопрос задан, но ответ уходит в сторону
   - Защитная реакция: оправдания без запроса, повторяющиеся «но»

4. НЕВЫСКАЗАННОЕ
   - Темы, которые начали и резко свернули
   - Вопросы, оставшиеся без ответа (не технические — а те, что «замяли»)
   - «Слон в комнате» — тема, которую все избегают

5. КОАЛИЦИИ И ГРУППИРОВКИ
   - Кто поддерживает чьи идеи?
   - Есть ли изолированные участники?

6. ЭМОЦИОНАЛЬНЫЕ СДВИГИ
   - Моменты, где тон резко изменился
   - Что вызвало сдвиг? Как группа отреагировала?

7. СТИЛИ КОММУНИКАЦИИ
   - Кто говорит фактами, кто эмоциями?
   - Кто использует «мы» vs «я» vs «вы»?

═══ КРИТИЧЕСКИ ВАЖНО ═══
1. Это ГИПОТЕТИЧЕСКИЙ анализ. Формулируй как «может указывать на...», «возможно...».
2. НИЧЕГО НЕ ВЫДУМЫВАЙ. Каждое наблюдение — с цитатой из транскрипции.
3. Здоровая динамика = тоже результат. Не ищи проблемы где их нет.
4. Анализируй ПАТТЕРНЫ, не людей. confidence: high/medium/low.
═══════════════════════

JSON:
{{
    "overall_atmosphere": {{"summary": "", "tension_level": "low/moderate/elevated/high", "collaboration_quality": "high/moderate/low", "energy": "energetic/balanced/flat/tense"}},
    "power_dynamics": [{{"observation": "", "evidence": "", "confidence": "high/medium/low"}}],
    "interruptions": [{{"observation": "", "evidence": "", "interpretation": "", "confidence": ""}}],
    "tension_markers": [{{"type": "hedging/passive_aggression/evasion/defensiveness", "observation": "", "evidence": "", "possible_meaning": "", "confidence": ""}}],
    "unspoken": [{{"observation": "", "evidence": "", "confidence": ""}}],
    "coalitions": [{{"observation": "", "members": [], "evidence": "", "confidence": ""}}],
    "emotional_shifts": [{{"moment": "", "shift": "", "trigger": "", "group_reaction": "", "confidence": ""}}],
    "communication_styles": [{{"speaker": "", "style": "", "notable_patterns": ""}}],
    "healthy_patterns": [],
    "recommendations": []
}}

⚠️ Если аспект НЕ обнаружен — пустой массив []. Не заполняй ради заполнения.

Язык: {language}
Участников: {participants}

Транскрипция:
{text}"""

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def analyze_dynamics(text: str, participants: int = 2, language: str = "ru") -> dict:
    """Гипотетический анализ скрытой динамики беседы."""
    if participants < 2:
        return _solo_result()
    prompt = DYNAMICS_ANALYSIS_PROMPT.format(language=language, participants=participants, text=text[:20000])
    try:
        resp = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Ты — организационный психолог. Отвечай ТОЛЬКО валидным JSON. Если динамика здоровая — так и скажи."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4, max_tokens=5000,
            response_format={"type": "json_object"},
        )
        return _normalize(json.loads(resp.choices[0].message.content))
    except Exception as e:
        logger.error(f"Ошибка анализа динамики: {e}")
        return _empty()


def _normalize(data: dict) -> dict:
    atm = data.setdefault("overall_atmosphere", {})
    atm.setdefault("summary", "")
    atm.setdefault("tension_level", "low")
    atm.setdefault("collaboration_quality", "high")
    atm.setdefault("energy", "balanced")
    for key in ("power_dynamics", "interruptions", "tension_markers", "unspoken", "coalitions", "emotional_shifts", "communication_styles", "healthy_patterns", "recommendations"):
        data.setdefault(key, [])
    if atm["tension_level"] == "low":
        data["tension_markers"] = [m for m in data["tension_markers"] if m.get("confidence") != "low"]
    return data


def _empty() -> dict:
    return {"overall_atmosphere": {"summary": "Не удалось проанализировать", "tension_level": "unknown", "collaboration_quality": "unknown", "energy": "unknown"}, "power_dynamics": [], "interruptions": [], "tension_markers": [], "unspoken": [], "coalitions": [], "emotional_shifts": [], "communication_styles": [], "healthy_patterns": [], "recommendations": []}


def _solo_result() -> dict:
    return {"overall_atmosphere": {"summary": "Монолог — анализ групповой динамики неприменим", "tension_level": "n/a", "collaboration_quality": "n/a", "energy": "n/a"}, "power_dynamics": [], "interruptions": [], "tension_markers": [], "unspoken": [], "coalitions": [], "emotional_shifts": [], "communication_styles": [], "healthy_patterns": [], "recommendations": []}


def has_notable_dynamics(dynamics: dict) -> bool:
    if not dynamics:
        return False
    atm = dynamics.get("overall_atmosphere", {})
    if atm.get("tension_level") in ("n/a", "unknown"):
        return False
    return sum(len(dynamics.get(k, [])) for k in ("power_dynamics", "interruptions", "tension_markers", "unspoken", "coalitions", "emotional_shifts")) > 0


def format_dynamics_summary(dynamics: dict, lang: str = "ru") -> str:
    if not has_notable_dynamics(dynamics):
        return ""
    lines = []
    atm = dynamics.get("overall_atmosphere", {})
    tension_map = {"low": "🟢 спокойная", "moderate": "🟡 умеренное напряжение", "elevated": "🟠 повышенное напряжение", "high": "🔴 высокое напряжение"}
    tension = tension_map.get(atm.get("tension_level", ""), "")
    if tension:
        lines.append(f"**Атмосфера:** {tension}")
    if atm.get("summary"):
        lines.append(atm["summary"])
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
