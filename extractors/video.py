"""Извлечение аудио из видео через FFmpeg."""

import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


async def extract_audio_from_video(video_path: Path, output_format: str = "mp3") -> Path:
    """Извлекает аудиодорожку из видеофайла."""
    output_path = video_path.with_suffix(f".{output_format}")

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vn",               # no video
        "-acodec", "libmp3lame" if output_format == "mp3" else "copy",
        "-ar", "16000",      # 16kHz for transcription
        "-ac", "1",          # mono
        "-y",                # overwrite
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"FFmpeg error: {stderr.decode()[:300]}")
        raise Exception("Не удалось извлечь аудио из видео")

    logger.info(f"Audio extracted: {output_path.name} ({output_path.stat().st_size / 1024:.0f} KB)")
    return output_path
