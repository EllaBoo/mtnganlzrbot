# 🧠 Digital Smarty v5.0 — Цифровой Умник

**AI-эксперт в любой области** — Telegram Bot + Mini App Hybrid

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│                  TELEGRAM                             │
│  ┌──────────┐    ┌──────────┐                        │
│  │   Bot    │    │ Mini App │                        │
│  │ bot.py   │    │ webapp/  │                        │
│  └────┬─────┘    └────┬─────┘                        │
│       │               │                              │
│       └───────┬───────┘                              │
│               ▼                                      │
│      ┌─────────────────┐                             │
│      │  dronor_client   │  ← HTTP POST              │
│      │  .py             │                            │
│      └────────┬────────┘                             │
└───────────────┼──────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│              DRONOR EXPERTS                          │
│                                                      │
│  1. ds_url_resolver      → определяет источник       │
│  2. ds_audio_extractor   → извлекает аудио           │
│  3. ds_transcriber       → Deepgram Nova-2           │
│  4. ds_topic_extractor   → темы, решения (GPT-4o)   │
│  5. ds_expert_analyzer   → SWOT, рекомендации        │
│  6. ds_report_generator  → PDF/HTML/TXT/JSON         │
│  7. ds_context_manager   → сохранение контекста      │
│  8. ds_session_memory    → загрузка истории           │
│                                                      │
│  Pipeline: pipeline_27 (Digital Smarty v4.1)         │
└─────────────────────────────────────────────────────┘
```

## Файлы проекта

```
digital_smarty/
├── bot.py              # Telegram bot — handlers, keyboards, processing
├── dronor_client.py    # Dronor Expert Client — вызовы экспертов
├── config.py           # Конфигурация из ENV
├── webapp/
│   └── index.html      # Telegram Mini App — UI
├── .env.example        # Шаблон переменных
├── Dockerfile          # Docker image
├── requirements.txt    # Python зависимости
├── railway.toml        # Railway deploy config
└── README.md           # Этот файл
```

## Быстрый старт

```bash
# 1. Клонировать
git clone <repo> && cd digital_smarty

# 2. Настроить
cp .env.example .env
# Заполнить TELEGRAM_BOT_TOKEN и DRONOR_API_URL

# 3. Запустить
pip install -r requirements.txt
python bot.py
```

## Railway Deploy

```bash
# В Railway добавить env vars:
# TELEGRAM_BOT_TOKEN=...
# DRONOR_API_URL=https://your-dronor.com
railway up
```

## Поддерживаемые источники

| Источник | Примеры |
|----------|---------|
| Telegram | Голосовые, аудио, видео, видеосообщения |
| YouTube | youtube.com/watch, youtu.be/, shorts |
| Облачные диски | Google Drive, Dropbox, Yandex Disk |
| Видеоплатформы | Vimeo, Loom |
| Прямые ссылки | .mp3, .mp4, .wav, .m4a |

## Универсальный эксперт

Умник **сам определяет** область и становится экспертом:

- 🏢 Бизнес, стратегия, продукт
- 📈 Маркетинг, продажи
- ⚖️ Юриспруденция
- 🏥 Медицина
- 🧠 Психология
- 🎓 Образование
- 🎨 Дизайн
- 📦 Логистика
- 💰 Финансы
- 👥 HR
- ... и любая другая область

## Принцип честности

- 📌 **Факт** — только то, что реально сказано в аудио
- 💡 **Рекомендация** — помечена как мнение эксперта
- ❓ **Не обсуждалось** — явно указано
- ⚠️ **Риск** — выявлен экспертом, помечен
