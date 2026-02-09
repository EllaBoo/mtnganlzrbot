"""Обработка видеофайлов и видеосообщений."""

import logging
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.translations import t
from bot.keyboards import context_type_keyboard
from bot.handlers.commands import get_user_context_type, set_pending_audio
from bot.handlers.audio import _run_pipeline
from extractors.video import extract_audio_from_video
import config

logger = logging.getLogger(__name__)


def register_video_handlers(app: Client):

    @app.on_message(filters.video | filters.video_note)
    async def handle_video(client: Client, message: Message):
        lang = "en" if (message.from_user and message.from_user.language_code and
                        message.from_user.language_code.startswith("en")) else "ru"

        file_size = 0
        if message.video:
            file_size = message.video.file_size or 0
        elif message.video_note:
            file_size = message.video_note.file_size or 0

        if file_size > config.MAX_FILE_SIZE_BYTES:
            await message.reply(t("too_large", lang, max_mb=config.MAX_FILE_SIZE_BYTES // (1024*1024)))
            return

        status = await message.reply(t("processing", lang))

        try:
            video_path = await message.download(
                file_name=str(config.TEMP_DIR / f"video_{message.id}")
            )
            video_path = Path(video_path)
            logger.info(f"Video downloaded: {video_path}")

            await status.edit_text("🎬 Извлекаю аудио из видео...")
            audio_path = await extract_audio_from_video(video_path)

            # Удаляем видео — он больше не нужен
            video_path.unlink(missing_ok=True)

            ctx_type = get_user_context_type(message.from_user.id)
            if ctx_type == "meeting":
                set_pending_audio(message.from_user.id, audio_path, lang)
                await status.edit_text(t("choose_type", lang), reply_markup=context_type_keyboard(lang))
                return

            await _run_pipeline(client, status, audio_path, ctx_type, lang)

        except Exception as e:
            logger.exception("Video processing error")
            await status.edit_text(t("error", lang, error=str(e)[:200]))
