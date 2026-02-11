"""Обработка аудиофайлов и голосовых сообщений — основной pipeline."""

import logging
import os
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

from bot.translations import t
from bot.keyboards import context_type_keyboard
from bot.handlers.commands import get_user_context_type, set_pending_audio
from core.transcription import transcribe_audio, format_transcript_with_speakers
from core.analysis import analyze_text
from core.topic_extractor import extract_topics
from core.expert_analysis import expert_analysis
from core.diagnostics import analyze_speech
from core.dynamics import analyze_dynamics, has_notable_dynamics, format_dynamics_summary
from core.pdf_generator import generate_pdf_report, generate_html_report
import config

logger = logging.getLogger(__name__)


def register_audio_handlers(app: Client):
    """Регистрирует обработчики аудио."""

    @app.on_message(filters.voice | filters.audio)
    async def handle_audio(client: Client, message: Message):
        lang = "en" if (message.from_user and message.from_user.language_code and
                        message.from_user.language_code.startswith("en")) else "ru"

        file_size = message.voice.file_size if message.voice else (message.audio.file_size if message.audio else 0)
        if file_size and file_size > config.MAX_FILE_SIZE_BYTES:
            await message.reply(t("too_large", lang, max_mb=config.MAX_FILE_SIZE_BYTES // (1024*1024)))
            return

        status = await message.reply(t("processing", lang))

        try:
            audio_path = await message.download(file_name=str(config.TEMP_DIR / f"audio_{message.id}"))
            audio_path = Path(audio_path)
            logger.info(f"Audio downloaded: {audio_path} ({audio_path.stat().st_size / 1024:.0f} KB)")

            ctx_type = get_user_context_type(message.from_user.id)
            if ctx_type == "meeting":
                set_pending_audio(message.from_user.id, audio_path, lang)
                await status.edit_text(t("choose_type", lang), reply_markup=context_type_keyboard(lang))
                return

            await _run_pipeline(client, status, audio_path, ctx_type, lang)

        except Exception as e:
            logger.exception("Audio processing error")
            await status.edit_text(t("error", lang, error=str(e)[:200]))


async def _run_pipeline(
    client: Client, status_msg: Message, audio_path: Path,
    context_type: str, lang: str,
):
    """Основной pipeline обработки аудио."""
    pdf_path = None
    html_path = None
    try:
        # 1. Транскрипция
        await status_msg.edit_text(t("transcribing", lang))
        transcription = await transcribe_audio(audio_path, language=lang)
        text = transcription["text"]

        if not text or len(text.strip()) < 20:
            await status_msg.edit_text("⚠️ Не удалось распознать речь. Попробуйте другой файл.")
            return

        # 2. Извлечение тем
        await status_msg.edit_text(t("analyzing_topics", lang))
        if context_type == "auto":
            context_type = "meeting"
        topics = await extract_topics(text, context_type=context_type, language=lang)

        # 3. Базовый анализ
        analysis = await analyze_text(text, language=lang)

        # 4. Экспертный анализ
        await status_msg.edit_text(t("expert_analysis", lang))
        expert_data = await expert_analysis(text, topics, language=lang)

        # 5. Диагностика речи
        diag = analyze_speech(
            text, transcription["duration"],
            transcription.get("segments", []), lang,
        )

        # 6. Анализ динамики беседы
        participants = analysis.get("participants", transcription.get("speakers", 1))
        if participants >= 2:
            await status_msg.edit_text(
                "🔍 Анализ динамики беседы..." if lang == "ru"
                else "🔍 Analyzing conversation dynamics..."
            )
            dynamics = await analyze_dynamics(
                text, participants=participants, language=lang,
            )
        else:
            dynamics = None

        # 7. Генерация отчётов
        await status_msg.edit_text(t("generating_report", lang))

        pdf_path = generate_pdf_report(
            text=text, analysis=analysis, topics=topics,
            expert_data=expert_data, language=lang,
            report_type=context_type, diagnostics=diag,
        )

        html_path = generate_html_report(
            text=text, analysis=analysis, topics=topics,
            expert_data=expert_data, language=lang,
            report_type=context_type, diagnostics=diag,
        )

        # 8. Краткое резюме для чата
        summary_text = _format_chat_summary(expert_data, topics, diag, dynamics, lang)

        # 9. Отправка
        await status_msg.edit_text(f"✅ Анализ завершён!\n\n{summary_text}", parse_mode="markdown")

        await status_msg.reply_document(
            document=str(pdf_path),
            caption="📄 PDF-отчёт — Цифровой Умник",
        )

        await status_msg.reply_document(
            document=str(html_path),
            caption="🌐 HTML-отчёт (интерактивный, с раскрываемыми разделами)",
        )

    except Exception as e:
        logger.exception("Pipeline error")
        await status_msg.edit_text(t("error", lang, error=str(e)[:200]))

    finally:
        for p in [audio_path, pdf_path, html_path]:
            if p and Path(p).exists():
                try:
                    os.unlink(p)
                except Exception:
                    pass


def _format_chat_summary(
    expert_data: dict, topics: dict, diag: dict,
    dynamics: dict | None, lang: str,
) -> str:
    """Форматирует краткое summary для чата."""
    lines = []

    summary = expert_data.get("executive_summary", "")
    if summary:
        lines.append(f"📋 **Резюме:**\n{summary}\n")

    topic_list = topics.get("topics", [])
    if topic_list:
        lines.append(f"📑 **Темы ({len(topic_list)}):**")
        for t_item in topic_list[:5]:
            lines.append(f"  • {t_item['title']}")
        if len(topic_list) > 5:
            lines.append(f"  _...и ещё {len(topic_list) - 5}_")
        lines.append("")

    all_decisions = [d for t_item in topic_list for d in t_item.get("decisions", [])]
    if all_decisions:
        lines.append("🎯 **Решения:**")
        for d in all_decisions[:3]:
            lines.append(f"  ✅ {d}")
        lines.append("")

    lines.append(
        f"📊 **Статистика:** {diag.get('words_total', 0)} слов, "
        f"{diag.get('words_per_minute', 0)} сл/мин"
    )

    role = expert_data.get("expertise_role", "")
    if role:
        lines.append(f"🧠 **Эксперт:** {role}")

    if dynamics and has_notable_dynamics(dynamics):
        dyn_summary = format_dynamics_summary(dynamics, lang)
        if dyn_summary:
            lines.append(f"\n🔮 **Динамика беседы:**\n{dyn_summary}")

    return "\n".join(lines)
