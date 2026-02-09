"""Определение типа ссылки и маршрутизация к экстрактору."""

import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PATTERNS = [
    ("youtube", [
        r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/shorts/|youtube\.com/embed/)[\w-]+",
    ]),
    ("gdrive", [
        r"drive\.google\.com/file/d/[\w-]+",
        r"docs\.google\.com/.+/d/[\w-]+",
    ]),
    ("dropbox", [
        r"dropbox\.com/s(?:cl)?/[\w-]+",
        r"dl\.dropboxusercontent\.com",
    ]),
    ("yandex", [
        r"disk\.yandex\.ru/d/[\w-]+",
        r"yadi\.sk/d/[\w-]+",
    ]),
    ("vimeo", [r"vimeo\.com/\d+"]),
    ("loom", [r"loom\.com/share/[\w-]+"]),
]

DIRECT_EXTS = {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg", ".flac", ".avi", ".mkv", ".mov"}


def resolve_url(url: str) -> dict:
    """
    Определяет тип ссылки.
    Returns: {"type": str, "url": str, "platform": str}
    """
    url = url.strip()

    for platform, regexes in PATTERNS:
        for regex in regexes:
            if re.search(regex, url):
                logger.info(f"URL resolved: {platform} — {url[:60]}")
                return {"type": platform, "url": url, "platform": platform}

    # Direct file link
    parsed = urlparse(url)
    ext = "." + parsed.path.rsplit(".", 1)[-1].lower() if "." in parsed.path else ""
    if ext in DIRECT_EXTS:
        return {"type": "direct", "url": url, "platform": "direct"}

    return {"type": "unknown", "url": url, "platform": "unknown"}


def extract_url_from_text(text: str) -> str | None:
    """Извлекает первую URL из текста."""
    match = re.search(r"https?://[^\s<>\"']+", text)
    return match.group(0) if match else None
