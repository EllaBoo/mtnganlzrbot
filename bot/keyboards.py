"""
Keyboards for Digital Smarty bot
"""
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.translations import t


def language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Auto-detect", callback_data="lang_auto")],
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ],
        [
            InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        ],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")],
    ])


def main_keyboard(user_id: int, expert_role: str = "") -> InlineKeyboardMarkup:
    """Main keyboard after analysis"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "ask_question"), callback_data="ask")],
        [InlineKeyboardButton(t(user_id, "get_transcript"), callback_data="transcript")],
        [InlineKeyboardButton(t(user_id, "new_analysis"), callback_data="new")],
    ])


def back_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Back button keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "back"), callback_data="back")]
    ])


def question_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard during question mode"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "back"), callback_data="back")]
    ])
