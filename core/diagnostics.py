"""
Diagnostics module - Expert-level analysis
Все выводы на выбранном языке
"""
import logging
from openai import AsyncOpenAI

import config
from core.prompts import DIAGNOSTICS_PROMPT
from core.analysis import detect_expertise
from bot.translations import get_lang_name

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def diagnose_communication(
    transcript: str, 
    language: str = "ru", 
    expertise: dict = None
) -> str:
    """
    Expert-level diagnostics
    Output in target language
    """
    
    lang_name = get_lang_name(language)
    
    # Detect expertise if not provided
    if not expertise:
        expertise = await detect_expertise(transcript, language)
    
    logger.info(f"Diagnosing as: {expertise['expert_role']}")
    
    prompt = DIAGNOSTICS_PROMPT.format(
        transcript=transcript[:50000],
        language=lang_name,
        domain=expertise["domain"],
        domain_localized=expertise["domain_localized"],
        meeting_type=expertise["meeting_type"],
        meeting_type_localized=expertise.get("meeting_type_localized", expertise["meeting_type"]),
        expert_role=expertise["expert_role"]
    )
    
    system_prompt = f"""You are Digital Smarty (Цифровой Умник), acting as {expertise['expert_role']}.

Conduct diagnostics from two angles:
1. EXPERT (content quality from {expertise['domain_localized']} perspective)
2. COMMUNICATION (if relevant for {expertise['meeting_type']})

CRITICAL: ALL your output MUST be in {lang_name}. Every word, every metric, everything.

Be objective. Don't make up problems — note only real ones.
Give professional recommendations as an experienced {expertise['expert_role']}."""

    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content
