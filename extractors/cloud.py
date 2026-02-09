"""Скачивание файлов из облачных хранилищ."""

import re
import logging
from pathlib import Path
import httpx
import config

logger = logging.getLogger(__name__)


async def extract_from_cloud(url: str, service: str, output_dir: Path = None) -> dict:
    """Скачивает аудио/видео из облака. Returns: {"audio_path": Path, "title": str}"""
    if output_dir is None:
        output_dir = config.TEMP_DIR

    download_url = _get_direct_url(url, service)
    logger.info(f"Cloud download ({service}): {url[:60]}...")

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        resp = await client.get(download_url)
        resp.raise_for_status()

        # Determine filename
        cd = resp.headers.get("content-disposition", "")
        if "filename=" in cd:
            fname = cd.split("filename=")[-1].strip('"').strip("'")
        else:
            fname = f"cloud_{service}_{hash(url) % 10000}.mp3"

        path = output_dir / fname
        path.write_bytes(resp.content)

        if path.stat().st_size > config.MAX_FILE_SIZE_BYTES:
            path.unlink()
            raise ValueError(f"Файл слишком большой: {path.stat().st_size / 1024 / 1024:.0f} MB")

    return {"audio_path": path, "title": fname}


async def download_direct_url(url: str, output_dir: Path = None) -> dict:
    """Скачивает файл по прямой ссылке."""
    if output_dir is None:
        output_dir = config.TEMP_DIR

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

        fname = url.rsplit("/", 1)[-1].split("?")[0] or "download.mp3"
        path = output_dir / fname
        path.write_bytes(resp.content)

    return {"audio_path": path, "title": fname}


def _get_direct_url(url: str, service: str) -> str:
    if service == "gdrive":
        file_id = _extract_gdrive_id(url)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    elif service == "dropbox":
        return url.replace("www.dropbox.com", "dl.dropboxusercontent.com").split("?")[0]
    elif service == "yandex":
        return f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={url}"
    return url


def _extract_gdrive_id(url: str) -> str:
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"id=([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else ""
