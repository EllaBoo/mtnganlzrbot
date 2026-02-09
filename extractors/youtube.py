"""Скачивание аудио с YouTube через yt-dlp."""

import logging
import asyncio
from pathlib import Path
import config

logger = logging.getLogger(__name__)


async def extract_audio_from_youtube(url: str, output_dir: Path = None) -> dict:
    """
    Скачивает аудио с YouTube.
    Returns: {"audio_path": Path, "title": str, "duration": int, "channel": str}
    """
    if output_dir is None:
        output_dir = config.TEMP_DIR

    output_template = str(output_dir / "%(id)s.%(ext)s")

    # Сначала получаем инфо
    info = await _get_info(url)
    duration = info.get("duration", 0)

    if duration > config.MAX_DURATION_SECONDS:
        raise ValueError(
            f"Видео слишком длинное: {duration // 3600}ч {(duration % 3600) // 60}мин "
            f"(макс. {config.MAX_DURATION_SECONDS // 3600}ч)"
        )

    logger.info(f"YouTube: {info.get('title', '?')} ({duration // 60}мин)")

    # Скачиваем аудио
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-x",  # extract audio
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", output_template,
        "--no-warnings",
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error = stderr.decode()[:500]
        logger.error(f"yt-dlp error: {error}")
        raise Exception(f"Не удалось скачать видео: {error}")

    # Ищем скачанный файл
    video_id = info.get("id", "")
    audio_path = None
    for ext in ("mp3", "m4a", "opus", "webm", "ogg"):
        candidate = output_dir / f"{video_id}.{ext}"
        if candidate.exists():
            audio_path = candidate
            break

    if not audio_path:
        # fallback — ищем последний файл
        files = sorted(output_dir.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            audio_path = files[0]
        else:
            raise Exception("Файл не найден после скачивания")

    return {
        "audio_path": audio_path,
        "title": info.get("title", ""),
        "duration": duration,
        "channel": info.get("channel", info.get("uploader", "")),
    }


async def _get_info(url: str) -> dict:
    """Получает метаданные видео."""
    import json

    cmd = ["yt-dlp", "--no-playlist", "-j", "--no-warnings", url]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise Exception(f"Не удалось получить информацию о видео: {stderr.decode()[:300]}")

    return json.loads(stdout.decode())
