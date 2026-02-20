import json
from openai import AsyncOpenAI
from config import Config

class Analyzer:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
    
    async def analyze(self, transcript_data: dict, output_language: str = "ru") -> dict:
        """Analyzes transcript and returns structured summary"""
        
        language_names = {
            "ru": "Russian",
            "en": "English",
            "kk": "Kazakh",
            "es": "Spanish",
            "auto": "same as input"
        }
        
        output_lang = language_names.get(output_language, "Russian")
        
        speakers_text = "\n".join([
            f"[Speaker {s['speaker']+1}]: {s['text']}" 
            for s in transcript_data.get("speakers", [])
        ])
        
        if not speakers_text:
            speakers_text = transcript_data.get("transcript", "")
        
        system_prompt = f"""You are Digital Smarty - an expert meeting analyst with a slightly sarcastic but friendly tone.

Your task: Analyze the meeting transcript and create a comprehensive summary.

CRITICAL RULES:
1. ONLY use information from the transcript. NO hallucinations, NO assumptions.
2. If something is unclear, say "unclear from recording" rather than guessing.
3. Be precise with speaker attributions.
4. Output in {output_lang} language.

Return a JSON object with this EXACT structure:
{{
    "title": "Meeting title based on main topic",
    "date_mentioned": "date if mentioned, otherwise null",
    "duration_minutes": {int(transcript_data.get('duration', 0) / 60)},
    "participants_count": {transcript_data.get('speakers_count', 1)},
    "detected_language": "{transcript_data.get('detected_language', 'unknown')}",
    
    "key_topics": [
        {{"topic": "Topic name", "summary": "Brief description", "importance": "high/medium/low"}}
    ],
    
    "speaker_positions": [
        {{"speaker": "Speaker 1", "main_points": ["point1", "point2"], "stance": "brief stance description"}}
    ],
    
    "decisions": [
        {{"decision": "What was decided", "context": "Why/how"}}
    ],
    
    "action_items": [
        {{"task": "Task description", "responsible": "Speaker X or unassigned", "deadline": "if mentioned"}}
    ],
    
    "open_questions": [
        {{"question": "Unresolved question", "context": "Why it matters"}}
    ],
    
    "risks": [
        {{"risk": "Risk description", "severity": "high/medium/low"}}
    ],
    
    "reality_check": {{
        "feasibility": "Assessment of how realistic the agreements are",
        "concerns": ["List of potential issues"],
        "recommendations": ["Suggestions for improvement"]
    }},
    
    "key_insights": [
        "Insight 1",
        "Insight 2"
    ],
    
    "meeting_mood": "Overall emotional tone of the meeting",
    "smarty_comment": "A witty, slightly sarcastic one-liner about the meeting"
}}"""

        user_prompt = f"""Analyze this meeting transcript:

{speakers_text}

Remember: Only facts from the transcript. Be precise and structured."""

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
