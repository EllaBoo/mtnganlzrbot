"""Цифровой Умник — точка входа бота."""

import logging
import sys
from pyrogram import Client

import config
from bot.handlers.commands import register_commands
from bot.handlers.audio import register_audio_handlers
from bot.handlers.video import register_video_handlers
from bot.handlers.links import register_link_handlers

# ── Logging ────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("digital_smarty")


def create_app() -> Client:
    """Создаёт и настраивает Pyrogram-клиент."""
    app = Client(
        name="digital_smarty",
        api_id=config.TELEGRAM_API_ID,
        api_hash=config.TELEGRAM_API_HASH,
        bot_token=config.TELEGRAM_BOT_TOKEN,
        workdir=str(config.SESSIONS_DIR),
    )

    # Регистрируем все обработчики
    register_commands(app)
    register_audio_handlers(app)
    register_video_handlers(app)
    register_link_handlers(app)

    return app


def main():
    logger.info("🧠 Цифровой Умник запускается...")

    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        sys.exit(1)
    if not config.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY не установлен!")
        sys.exit(1)
    if not config.DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY не установлен!")
        sys.exit(1)

    app = create_app()

    logger.info("✅ Бот запущен и ожидает сообщений")
    app.run()


if __name__ == "__main__":
    main()
