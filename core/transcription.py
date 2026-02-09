"""
Transcription module using Deepgram Nova-2
"""
import httpx
import logging
from typing import Dict, Any

import config

logger = logging.getLogger(__name__)


async def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """
    Transcribe audio file using Deepgram Nova-2
    
    Returns:
        dict with keys: text, speakers, duration, speakers_count
    """
    
    # Read audio file
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    url = "https://api.deepgram.com/v1/listen"
    
    params = {
        "model": "nova-2",
        "smart_format": "true",
        "diarize": "true",
        "punctuate": "true",
        "detect_language": "true",
        "paragraphs": "true",
    }
    
    headers = {
        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/mp3",
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            url, 
            params=params, 
            headers=headers, 
            content=audio_data
        )
        response.raise_for_status()
        result = response.json()
    
    # Parse response
    channels = result.get("results", {}).get("channels", [])
    
    if not channels:
        return {"text": "", "speakers": [], "duration": 0, "speakers_count": 0}
    
    alternatives = channels[0].get("alternatives", [])
    
    if not alternatives:
        return {"text": "", "speakers": [], "duration": 0, "speakers_count": 0}
    
    transcript_data = alternatives[0]
    text = transcript_data.get("transcript", "")
    
    # Extract speaker information
    words = transcript_data.get("words", [])
    speakers = set()
    speaker_segments = []
    
    current_speaker = None
    current_text = []
    
    for word in words:
        speaker = word.get("speaker", 0)
        speakers.add(speaker)
        
        if speaker != current_speaker:
            if current_text:
                speaker_segments.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text)
                })
            current_speaker = speaker
            current_text = [word.get("word", "")]
        else:
            current_text.append(word.get("word", ""))
    
    # Don't forget last segment
    if current_text:
        speaker_segments.append({
            "speaker": current_speaker,
            "text": " ".join(current_text)
        })
    
    # Get duration
    duration = result.get("metadata", {}).get("duration", 0)
    
    # Format transcript with speakers
    formatted_text = ""
    for segment in speaker_segments:
        speaker_num = segment['speaker'] if segment['speaker'] is not None else 0
        formatted_text += f"\n[Speaker {speaker_num}]: {segment['text']}\n"
    
    if not formatted_text.strip():
        formatted_text = text
    
    return {
        "text": formatted_text.strip() or text,
        "speakers": list(speakers),
        "duration": duration,
        "speakers_count": len(speakers) if speakers else 1
    }
