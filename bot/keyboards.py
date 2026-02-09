"""Инлайн-клавиатуры бота."""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def context_type_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора типа контента."""
    labels = {
        "ru": [
            ("💡 Брейншторм", "ctx:brainstorm"),
            ("📋 Встреча", "ctx:meeting"),
            ("🤝 Переговоры", "ctx:negotiation"),
            ("🎓 Интервью", "ctx:interview"),
            ("📚 Лекция", "ctx:lecture"),
            ("💼 Консультация", "ctx:consultation"),
            ("🔄 Авто", "ctx:auto"),
        ],
        "en": [
            ("💡 Brainstorm", "ctx:brainstorm"),
            ("📋 Meeting", "ctx:meeting"),
            ("🤝 Negotiation", "ctx:negotiation"),
            ("🎓 Interview", "ctx:interview"),
            ("📚 Lecture", "ctx:lecture"),
            ("💼 Consultation", "ctx:consultation"),
            ("🔄 Auto", "ctx:auto"),
        ],
    }
    btns = labels.get(lang, labels["ru"])
    rows = [[InlineKeyboardButton(t, callback_data=d)] for t, d in btns[:3]]
    rows.append([InlineKeyboardButton(btns[3][0], callback_data=btns[3][1]),
                 InlineKeyboardButton(btns[4][0], callback_data=btns[4][1])])
    rows.append([InlineKeyboardButton(btns[5][0], callback_data=btns[5][1]),
                 InlineKeyboardButton(btns[6][0], callback_data=btns[6][1])])
    return InlineKeyboardMarkup(rows)


def report_options_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура опций отчёта."""
    if lang == "en":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 PDF Report", callback_data="report:pdf"),
             InlineKeyboardButton("🌐 HTML Report", callback_data="report:html")],
            [InlineKeyboardButton("📄 Both", callback_data="report:both")],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 PDF отчёт", callback_data="report:pdf"),
         InlineKeyboardButton("🌐 HTML отчёт", callback_data="report:html")],
        [InlineKeyboardButton("📄 Оба формата", callback_data="report:both")],
    ])
