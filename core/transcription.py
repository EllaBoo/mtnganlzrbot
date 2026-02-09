"""Транскрипция аудио через Deepgram API."""

import logging
import httpx
from pathlib import Path
import config

logger = logging.getLogger(__name__)

MIME_MAP = {
    ".mp3": "audio/mp3", ".wav": "audio/wav", ".ogg": "audio/ogg",
    ".oga": "audio/ogg", ".m4a": "audio/mp4", ".mp4": "audio/mp4",
    ".webm": "audio/webm", ".flac": "audio/flac",
}


async def transcribe_audio(
    audio_path: Path, language: str = "ru", diarize: bool = True,
) -> dict:
    """
    Транскрибирует аудио через Deepgram.
    Returns: {"text", "segments", "speakers", "duration", "confidence"}
    """
    if not config.DEEPGRAM_API_KEY:
        raise ValueError("DEEPGRAM_API_KEY не установлен")

    params = {
        "model": "nova-2", "language": language,
        "punctuate": "true", "diarize": str(diarize).lower(),
        "paragraphs": "true", "utterances": "true", "smart_format": "true",
    }
    headers = {
        "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
        "Content-Type": MIME_MAP.get(audio_path.suffix.lower(), "audio/wav"),
    }

    size_mb = audio_path.stat().st_size / 1024 / 1024
    logger.info(f"Транскрипция: {audio_path.name} ({size_mb:.1f} MB)")

    async with httpx.AsyncClient(timeout=600) as client:
        with open(audio_path, "rb") as f:
            resp = await client.post(
                "https://api.deepgram.com/v1/listen",
                params=params, headers=headers, content=f.read(),
            )

    if resp.status_code != 200:
        logger.error(f"Deepgram: {resp.status_code} — {resp.text[:200]}")
        raise Exception(f"Ошибка транскрипции: {resp.status_code}")

    return _parse_response(resp.json())


def _parse_response(data: dict) -> dict:
    channels = data.get("results", {}).get("channels", [{}])
    alt = channels[0].get("alternatives", [{}])[0] if channels else {}
    full_text = alt.get("transcript", "")
    words = alt.get("words", [])

    segments, current = [], {"speaker": None, "start": 0, "end": 0, "text": ""}
    for w in words:
        spk = w.get("speaker", 0)
        if spk != current["speaker"] and current["text"]:
            segments.append(_flush_segment(current))
            current = {"speaker": spk, "start": w.get("start", 0), "end": 0, "text": ""}
        current["speaker"] = spk
        current["end"] = w.get("end", 0)
        current["text"] += w.get("punctuated_word", w.get("word", "")) + " "
    if current["text"]:
        segments.append(_flush_segment(current))

    speakers = {w.get("speaker") for w in words if "speaker" in w}
    duration = data.get("results", {}).get("metadata", {}).get("duration", 0)
    if not duration and words:
        duration = words[-1].get("end", 0)
    confs = [w["confidence"] for w in words if "confidence" in w]

    return {
        "text": full_text,
        "segments": segments,
        "speakers": len(speakers) or 1,
        "duration": duration,
        "confidence": round(sum(confs) / len(confs), 3) if confs else 0,
    }


def _flush_segment(seg: dict) -> dict:
    spk_num = (seg["speaker"] + 1) if seg["speaker"] is not None else 1
    return {
        "speaker": f"Спикер {spk_num}",
        "start": seg["start"], "end": seg["end"],
        "text": seg["text"].strip(),
        "timestamp": _fmt_ts(seg["start"]),
    }


def _fmt_ts(sec: float) -> str:
    t = int(sec)
    h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def format_transcript_with_speakers(segments: list) -> str:
    return "\n\n".join(f"[{s['timestamp']}] {s['speaker']}: {s['text']}" for s in segments)
