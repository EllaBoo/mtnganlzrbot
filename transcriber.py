import aiohttp
import json
from config import Config

class Transcriber:
    def __init__(self):
        self.api_key = Config.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1/listen"
    
    async def transcribe(self, audio_path: str, language: str = "auto") -> dict:
        """Transcribes audio via Deepgram Nova-2"""
        
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "diarize": "true",
            "punctuate": "true",
            "utterances": "true"
        }
        
        if language != "auto":
            params["language"] = language
        else:
            params["detect_language"] = "true"
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/mpeg"
        }
        
        async with aiohttp.ClientSession() as session:
            with open(audio_path, "rb") as audio_file:
                async with session.post(
                    self.base_url,
                    params=params,
                    headers=headers,
                    data=audio_file
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_result(result)
                    else:
                        error = await response.text()
                        raise Exception(f"Deepgram error: {error}")
    
    def _parse_result(self, result: dict) -> dict:
        """Parses Deepgram result into convenient format"""
        
        channels = result.get("results", {}).get("channels", [])
        if not channels:
            return {"transcript": "", "speakers": [], "duration": 0}
        
        alternatives = channels[0].get("alternatives", [])
        if not alternatives:
            return {"transcript": "", "speakers": [], "duration": 0}
        
        alt = alternatives[0]
        utterances = result.get("results", {}).get("utterances", [])
        
        speakers_text = []
        current_speaker = None
        current_text = []
        
        for utt in utterances:
            speaker = utt.get("speaker", 0)
            text = utt.get("transcript", "")
            
            if speaker != current_speaker:
                if current_text:
                    speakers_text.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_text)
                    })
                current_speaker = speaker
                current_text = [text]
            else:
                current_text.append(text)
        
        if current_text:
            speakers_text.append({
                "speaker": current_speaker,
                "text": " ".join(current_text)
            })
        
        detected_lang = result.get("results", {}).get("channels", [{}])[0].get("detected_language", "unknown")
        duration = result.get("metadata", {}).get("duration", 0)
        
        return {
            "transcript": alt.get("transcript", ""),
            "speakers": speakers_text,
            "speakers_count": len(set(s["speaker"] for s in speakers_text)) if speakers_text else 1,
            "duration": duration,
            "detected_language": detected_lang,
            "words": alt.get("words", [])
        }
