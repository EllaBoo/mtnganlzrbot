"""
Topic extraction utilities
"""
import re
import logging
from openai import AsyncOpenAI

import config
from core.prompts import TOPIC_EXTRACTION_PROMPT
from bot.translations import get_lang_name

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def extract_main_topic(analysis: str, language: str = "ru") -> str:
    """Extract main topic from analysis for filename"""
    
    lang_name = get_lang_name(language)
    
    prompt = TOPIC_EXTRACTION_PROMPT.format(
        analysis=analysis[:5000],
        language=lang_name
    )
    
    try:
        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50
        )
        
        topic = response.choices[0].message.content.strip()
        
        # Clean up
        topic = re.sub(r'[^\w\s-]', '', topic)
        topic = topic.replace(' ', '_')[:30]
        
        return topic or "analysis"
        
    except Exception as e:
        logger.error(f"Topic extraction error: {e}")
        return "analysis"
