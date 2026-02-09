"""Обработка ссылок: YouTube, Cloud, Direct."""

import logging
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.translations import t
from bot.keyboards import context_type_keyboard
from bot.handlers.commands import get_user_context_type, set_pending_audio
from bot.handlers.audio import _run_pipeline
from extractors.url_resolver import resolve_url, extract_url_from_text
from extractors.youtube import extract_audio_from_youtube
from extractors.cloud import extract_from_cloud, download_direct_url
from extractors.video import extract_audio_from_video
import config

logger = logging.getLogger(__name__)

PLATFORM_NAMES = {
    "youtube": "YouTube", "gdrive": "Google Drive", "dropbox": "Dropbox",
    "yandex": "Яндекс Диск", "vimeo": "Vimeo", "loom": "Loom", "direct": "Прямая ссылка",
}


def register_link_handlers(app: Client):

    @app.on_message(filters.text & ~filters.command(["start", "help", "settings"]))
    async def handle_text(client: Client, message: Message):
        url = extract_url_from_text(message.text)
        if not url:
            return  # Не ссылка — игнорируем

        lang = "en" if (message.from_user and message.from_user.language_code and
                        message.from_user.language_code.startswith("en")) else "ru"

        resolved = resolve_url(url)
        platform = resolved["type"]

        if platform == "unknown":
            await message.reply(t("unsupported_link", lang))
            return

        platform_name = PLATFORM_NAMES.get(platform, platform)
        status = await message.reply(t("link_detected", lang, platform=platform_name))

        try:
            audio_path = await _download_audio(url, platform, status, lang)

            ctx_type = get_user_context_type(message.from_user.id)
            if ctx_type == "meeting":
                set_pending_audio(message.from_user.id, audio_path, lang)
                await status.edit_text(t("choose_type", lang), reply_markup=context_type_keyboard(lang))
                return

            await _run_pipeline(client, status, audio_path, ctx_type, lang)

        except Exception as e:
            logger.exception(f"Link processing error ({platform})")
            await status.edit_text(t("error", lang, error=str(e)[:200]))


async def _download_audio(url: str, platform: str, status_msg: Message, lang: str) -> Path:
    """Скачивает аудио в зависимости от платформы."""

    if platform == "youtube":
        await status_msg.edit_text(t("downloading", lang) + "\n🎬 YouTube...")
        result = await extract_audio_from_youtube(url)
        return result["audio_path"]

    elif platform in ("gdrive", "dropbox", "yandex"):
        await status_msg.edit_text(t("downloading", lang) + f"\n☁️ {platform}...")
        result = await extract_from_cloud(url, platform)
        audio_path = result["audio_path"]
        # Если это видео — извлекаем аудио
        if audio_path.suffix.lower() in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
            audio_path = await extract_audio_from_video(audio_path)
        return audio_path

    elif platform == "direct":
        await status_msg.edit_text(t("downloading", lang))
        result = await download_direct_url(url)
        audio_path = result["audio_path"]
        if audio_path.suffix.lower() in (".mp4", ".mkv", ".avi", ".mov", ".webm"):
            audio_path = await extract_audio_from_video(audio_path)
        return audio_path

    elif platform in ("vimeo", "loom"):
        # yt-dlp поддерживает и Vimeo, и Loom
        await status_msg.edit_text(t("downloading", lang) + f"\n🎬 {platform}...")
        result = await extract_audio_from_youtube(url)  # yt-dlp handles these
        return result["audio_path"]

    raise ValueError(f"Неподдерживаемая платформа: {platform}")
