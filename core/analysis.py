"""
Analysis module - Adaptive Expert System
Цифровой Умник становится экспертом в области обсуждения
Все выводы на выбранном языке
"""
import json
import logging
from openai import AsyncOpenAI

import config
from core.prompts import (
    EXPERTISE_DETECTION_PROMPT,
    ANALYSIS_PROMPT,
    QUESTION_PROMPT,
    DOMAIN_TO_EXPERT,
    DOMAIN_KEYWORDS
)
from bot.translations import get_lang_name

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


def detect_domain_by_keywords(transcript: str) -> str:
    """Quick domain detection by keywords"""
    transcript_lower = transcript.lower()
    
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in transcript_lower)
        if score > 0:
            domain_scores[domain] = score
    
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return "general"


async def detect_expertise(transcript: str, language: str = "ru") -> dict:
    """
    Detect expertise domain and meeting type
    Returns expert role in target language
    """
    
    lang_name = get_lang_name(language)
    
    # Quick fallback by keywords
    keyword_domain = detect_domain_by_keywords(transcript)
    
    prompt = EXPERTISE_DETECTION_PROMPT.format(
        transcript_preview=transcript[:3000],
        language=lang_name
    )
    
    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": f"You determine recording topic and context. Respond ONLY with valid JSON. All localized fields must be in {lang_name}."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0]
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0]
        
        result = json.loads(result_text)
        
        # Get expert role (should already be in target language from GPT)
        domain = result.get("domain", keyword_domain).lower()
        expert_role = result.get("expert_role")
        
        # Fallback if expert_role not provided
        if not expert_role:
            expert_role = DOMAIN_TO_EXPERT.get(domain, DOMAIN_TO_EXPERT["general"])
        
        return {
            "domain": domain,
            "domain_localized": result.get("domain_localized", domain),
            "meeting_type": result.get("meeting_type", "meeting"),
            "meeting_type_localized": result.get("meeting_type_localized", result.get("meeting_type", "meeting")),
            "participants_level": result.get("participants_level", ""),
            "context": result.get("context", ""),
            "expert_role": expert_role
        }
        
    except Exception as e:
        logger.error(f"Expertise detection error: {e}")
        expert_role = DOMAIN_TO_EXPERT.get(keyword_domain, DOMAIN_TO_EXPERT["general"])
        return {
            "domain": keyword_domain,
            "domain_localized": keyword_domain,
            "meeting_type": "meeting",
            "meeting_type_localized": "meeting",
            "participants_level": "",
            "context": "",
            "expert_role": expert_role
        }


async def analyze_transcript(transcript: str, language: str = "ru", expertise: dict = None) -> str:
    """
    Analyze transcript as domain expert
    Output in target language
    """
    
    lang_name = get_lang_name(language)
    
    # Detect expertise if not provided
    if not expertise:
        expertise = await detect_expertise(transcript, language)
    
    logger.info(f"Analyzing as: {expertise['expert_role']} in {expertise['domain']}")
    
    prompt = ANALYSIS_PROMPT.format(
        transcript=transcript[:50000],
        language=lang_name,
        domain=expertise["domain"],
        domain_localized=expertise["domain_localized"],
        meeting_type=expertise["meeting_type"],
        meeting_type_localized=expertise.get("meeting_type_localized", expertise["meeting_type"]),
        expert_role=expertise["expert_role"]
    )
    
    system_prompt = f"""You are Digital Smarty (Цифровой Умник), an AI that becomes an expert in any field.

Now you are: {expertise['expert_role']}.
Domain: {expertise['domain_localized']}
Recording type: {expertise['meeting_type']}

CRITICAL: ALL your output MUST be in {lang_name}. Every word, every section header, everything.

Analyze as a real professional with years of experience in this field.
Give expert insights that only an experienced specialist can provide."""

    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=5000
    )
    
    return response.choices[0].message.content


async def answer_question(
    question: str,
    transcript: str,
    analysis: str,
    language: str = "ru",
    expertise: dict = None
) -> str:
    """
    Answer user's question as domain expert
    Output in target language
    """
    
    lang_name = get_lang_name(language)
    
    # Detect expertise if not provided
    if not expertise:
        expertise = await detect_expertise(transcript, language)
    
    prompt = QUESTION_PROMPT.format(
        transcript=transcript[:30000],
        analysis=analysis[:10000],
        question=question,
        language=lang_name,
        domain=expertise["domain"],
        expert_role=expertise["expert_role"]
    )
    
    system_prompt = f"""You are Digital Smarty (Цифровой Умник), acting as {expertise['expert_role']}.
Answer questions as a professional with deep expertise in {expertise['domain_localized']}.

CRITICAL: ALL your output MUST be in {lang_name}. 
Keep the Digital Smarty tone — friendly, helpful, but professionally expert."""

    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1500
    )
    
    return response.choices[0].message.content
