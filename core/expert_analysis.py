"""Экспертный анализ: AI принимает роль эксперта в предметной области."""

import json, logging
from openai import AsyncOpenAI
import config
from core.prompts import EXPERT_ANALYSIS_PROMPT, DOMAIN_DETECTION_PROMPT, DOMAIN_EXPERT_ROLES

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

DOMAIN_TRIGGERS = {
    "business_strategy": ["стратегия", "рынок", "конкурент", "выручка", "бизнес-модель", "strategy"],
    "product_management": ["продукт", "фич", "roadmap", "mvp", "user story", "бэклог", "спринт"],
    "marketing": ["маркетинг", "воронка", "лид", "конверсия", "бренд", "контент", "seo", "таргет"],
    "sales": ["продаж", "сделк", "crm", "pipeline", "холодн", "оффер"],
    "tech_architecture": ["архитектур", "api", "база данных", "микросервис", "docker", "backend"],
    "hr_management": ["команд", "найм", "культур", "мотивац", "онбординг", "hr"],
    "finance": ["бюджет", "инвестиц", "unit-экономик", "cashflow", "финанс", "roi"],
    "legal": ["договор", "юридическ", "compliance", "патент", "лицензи"],
    "medical": ["здоровь", "симптом", "лечени", "диагноз", "терапия", "медицин"],
    "education": ["обучени", "курс", "методик", "студент", "преподава", "образован"],
}


async def expert_analysis(
    text: str, topics: dict, domain: str = "auto",
    expertise_level: str = "professional", language: str = "ru",
) -> dict:
    if domain == "auto":
        domain = await _detect_domain(text)
    role = DOMAIN_EXPERT_ROLES.get(domain, DOMAIN_EXPERT_ROLES["general"])
    topics_text = _format_topics(topics)

    prompt = EXPERT_ANALYSIS_PROMPT.format(
        expertise_role=role, domain=domain, expertise_level=expertise_level,
        language=language, topics=topics_text, text=text[:15000],
    )
    try:
        resp = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": f"Ты — {role}. Отвечай ТОЛЬКО валидным JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3, max_tokens=6000,
            response_format={"type": "json_object"},
        )
        result = json.loads(resp.choices[0].message.content)
        return _normalize(result, domain, role)
    except Exception as e:
        logger.error(f"Ошибка экспертного анализа: {e}")
        return _empty(domain, role)


async def _detect_domain(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for dom, triggers in DOMAIN_TRIGGERS.items():
        score = sum(1 for t in triggers if t in text_lower)
        if score > 0:
            scores[dom] = score
    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 2:
            return best
    try:
        resp = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": DOMAIN_DETECTION_PROMPT.format(text=text[:5000])}],
            temperature=0, max_tokens=50,
        )
        d = resp.choices[0].message.content.strip().lower()
        if d in DOMAIN_EXPERT_ROLES:
            return d
    except Exception:
        pass
    return "general"


def _format_topics(topics: dict) -> str:
    lines = []
    for t in topics.get("topics", []):
        lines.append(f"\n## Тема {t['id']}: {t['title']}")
        lines.append(t.get("summary", ""))
        for p in t.get("key_points", []):
            lines.append(f"  - {p}")
        for d in t.get("decisions", []):
            lines.append(f"  Решение: {d}")
    return "\n".join(lines)


def _normalize(data: dict, domain: str, role: str) -> dict:
    data.setdefault("domain_detected", domain)
    data.setdefault("expertise_role", role)
    data.setdefault("executive_summary", "")
    a = data.setdefault("expert_assessment", {})
    for k in ("strengths", "weaknesses", "opportunities", "threats"):
        a.setdefault(k, [])
    recs = data.setdefault("recommendations", [])
    for r in recs:
        for k in ("priority", "area", "recommendation", "rationale", "action", "expected_impact"):
            r.setdefault(k, "")
    data["recommendations"] = recs[:config.MAX_RECOMMENDATIONS]
    data.setdefault("industry_benchmarks", {})
    data.setdefault("suggested_next_steps", [])
    data.setdefault("questions_to_consider", [])
    data.setdefault("resources", [])
    return data


def _empty(domain: str, role: str) -> dict:
    return {
        "domain_detected": domain, "expertise_role": role,
        "executive_summary": "Не удалось выполнить экспертный анализ",
        "expert_assessment": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
        "recommendations": [], "industry_benchmarks": {},
        "suggested_next_steps": [], "questions_to_consider": [], "resources": [],
    }
