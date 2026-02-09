"""Мультиязычность бота."""

TEXTS = {
    "ru": {
        "welcome": (
            "🧠 **Цифровой Умник** — AI-ассистент для анализа аудио и видео\n\n"
            "Отправьте мне:\n"
            "• 🎙 Голосовое сообщение\n"
            "• 🎵 Аудиофайл\n"
            "• 🎬 Видео или видеосообщение\n"
            "• 🔗 Ссылку на YouTube, Google Drive, Dropbox\n\n"
            "Я транскрибирую, разобью по темам, проведу экспертный анализ "
            "и сформирую PDF-отчёт с рекомендациями!"
        ),
        "help": (
            "📖 **Команды:**\n"
            "/start — Приветствие\n"
            "/help — Справка\n"
            "/settings — Настройки\n\n"
            "📎 **Поддерживаемые форматы:**\n"
            "Аудио: MP3, WAV, OGG, M4A, FLAC\n"
            "Видео: MP4, AVI, MKV, MOV, WebM\n"
            "Ссылки: YouTube, Google Drive, Dropbox, Yandex Disk, Vimeo, Loom\n\n"
            "📊 **Типы анализа:**\n"
            "• Брейншторм — идеи, оценка, приоритизация\n"
            "• Встреча — решения, задачи, ответственные\n"
            "• Интервью — профиль, компетенции\n"
            "• Лекция — конспект, тезисы\n"
            "• Консультация — проблема, рекомендации\n"
            "• Переговоры — позиции, договорённости"
        ),
        "choose_type": "📋 Выберите тип контента для более точного анализа:",
        "processing": "⏳ Обрабатываю...",
        "downloading": "⬇️ Скачиваю аудио...",
        "transcribing": "🎙 Транскрибирую...",
        "analyzing_topics": "📑 Извлекаю темы...",
        "expert_analysis": "🧠 Экспертный анализ...",
        "generating_report": "📄 Генерирую отчёт...",
        "done": "✅ Готово!",
        "error": "❌ Ошибка: {error}",
        "too_large": "❌ Файл слишком большой (макс. {max_mb} MB)",
        "unsupported_link": "❌ Ссылка не поддерживается. Поддерживаются: YouTube, Google Drive, Dropbox, Vimeo, Loom.",
        "link_detected": "🔗 Обнаружена ссылка: **{platform}**\n⏳ Скачиваю аудио...",
    },
    "en": {
        "welcome": (
            "🧠 **Digital Smarty** — AI assistant for audio/video analysis\n\n"
            "Send me:\n"
            "• 🎙 Voice message\n"
            "• 🎵 Audio file\n"
            "• 🎬 Video\n"
            "• 🔗 Link to YouTube, Google Drive, Dropbox\n\n"
            "I'll transcribe, extract topics, run expert analysis and generate a PDF report!"
        ),
        "help": "📖 Send /start for info",
        "choose_type": "📋 Choose content type for better analysis:",
        "processing": "⏳ Processing...",
        "downloading": "⬇️ Downloading audio...",
        "transcribing": "🎙 Transcribing...",
        "analyzing_topics": "📑 Extracting topics...",
        "expert_analysis": "🧠 Expert analysis...",
        "generating_report": "📄 Generating report...",
        "done": "✅ Done!",
        "error": "❌ Error: {error}",
        "too_large": "❌ File too large (max {max_mb} MB)",
        "unsupported_link": "❌ Unsupported link.",
        "link_detected": "🔗 Detected link: **{platform}**\n⏳ Downloading...",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text
