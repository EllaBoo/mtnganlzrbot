"""Обработчики команд бота."""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from bot.translations import t
from bot.keyboards import context_type_keyboard

logger = logging.getLogger(__name__)

# Хранилище состояний пользователей
user_states: dict[int, dict] = {}


def register_commands(app: Client):
    """Регистрирует обработчики команд."""

    @app.on_message(filters.command("start"))
    async def cmd_start(client: Client, message: Message):
        lang = _get_lang(message)
        await message.reply(t("welcome", lang), parse_mode="markdown")

    @app.on_message(filters.command("help"))
    async def cmd_help(client: Client, message: Message):
        lang = _get_lang(message)
        await message.reply(t("help", lang), parse_mode="markdown")

    @app.on_message(filters.command("settings"))
    async def cmd_settings(client: Client, message: Message):
        await message.reply(
            "⚙️ **Настройки**\n\n"
            "Язык анализа: 🇷🇺 Русский\n"
            "Формат отчёта: PDF + HTML\n"
            "Транскрипция: включена\n\n"
            "Настройки будут доступны в следующих версиях.",
            parse_mode="markdown",
        )

    @app.on_callback_query(filters.regex(r"^ctx:"))
    async def on_context_type(client: Client, callback: CallbackQuery):
        uid = callback.from_user.id
        ctx_type = callback.data.split(":")[1]

        state = user_states.get(uid, {})
        state["context_type"] = ctx_type
        user_states[uid] = state

        labels = {
            "brainstorm": "💡 Брейншторм",
            "meeting": "📋 Встреча",
            "negotiation": "🤝 Переговоры",
            "interview": "🎓 Интервью",
            "lecture": "📚 Лекция",
            "consultation": "💼 Консультация",
            "auto": "🔄 Авто",
        }

        await callback.answer(f"Выбрано: {labels.get(ctx_type, ctx_type)}")
        await callback.message.edit_text(
            f"Тип анализа: **{labels.get(ctx_type, ctx_type)}**\n\n"
            f"⏳ Начинаю обработку...",
            parse_mode="markdown",
        )

        # Запускаем обработку если есть pending audio
        if "pending_audio" in state:
            from bot.handlers.audio import _run_pipeline
            await _run_pipeline(
                client, callback.message, state["pending_audio"],
                ctx_type, state.get("lang", "ru"),
            )
            state.pop("pending_audio", None)

    @app.on_callback_query(filters.regex(r"^report:"))
    async def on_report_type(client: Client, callback: CallbackQuery):
        report_type = callback.data.split(":")[1]
        await callback.answer(f"Формат: {report_type.upper()}")


def get_user_context_type(uid: int) -> str:
    return user_states.get(uid, {}).get("context_type", "meeting")


def set_pending_audio(uid: int, audio_path, lang: str = "ru"):
    state = user_states.setdefault(uid, {})
    state["pending_audio"] = audio_path
    state["lang"] = lang


def _get_lang(message: Message) -> str:
    code = message.from_user.language_code if message.from_user else "ru"
    return "en" if code and code.startswith("en") else "ru"
