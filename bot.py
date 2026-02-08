import os
import uuid
import tempfile
import re
import requests as http_requests
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import OpenAI

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

API_ID = os.environ.get('TELEGRAM_API_ID')
API_HASH = os.environ.get('TELEGRAM_API_HASH')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DEEPGRAM_KEY = os.environ.get('DEEPGRAM_API_KEY')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY')

LANGUAGES = {
    'ru': {'name': '🇷🇺 Русский', 'deepgram': 'ru'},
    'en': {'name': '🇬🇧 English', 'deepgram': 'en'},
    'kk': {'name': '🇰🇿 Қазақша', 'deepgram': 'kk'},
    'es': {'name': '🇪🇸 Español', 'deepgram': 'es'},
    'zh': {'name': '🇨🇳 中文', 'deepgram': 'zh'},
}

# ═══════════════════════════════════════════════════════════════
# ЦИФРОВОЙ УМНИК - ПЕРЕВОДЫ И ФРАЗЫ
# ═══════════════════════════════════════════════════════════════

TRANSLATIONS = {
    'ru': {
        'welcome': '''🤖 **Йо! Я Цифровой Умник!**

Кидай сюда запись встречи — аудио или видео — и я разложу всё по полочкам:

📝 Что обсуждали (без воды)
👥 Кто что говорил
✅ Решения и задачи
💡 Мои рекомендации (бесплатно, но бесценно)

🎤 **Жду файл!**''',
        'choose_lang': '🌍 **На каком языке сделать анализ?**\n\n_(язык аудио определю сам)_',
        'downloading': '⏳ Секунду, тащу файл...',
        'transcribing': '🎤 Слушаю внимательно... (транскрибирую)',
        'analyzing': '🧠 Врубаюсь в контекст...',
        'done': '✅ Готово!',
        'error': '😬 Упс, что-то пошло не так',
        'choose_action': '✨ **Что дальше?**',
        'html_light': '🌐 HTML светлая',
        'html_dark': '🌑 HTML тёмная',
        'txt': '📄 TXT файл',
        'deep_dive': '🔍 Копнуть глубже',
        'custom_q': '✏️ Свой вопрос',
        'transcript': '📜 Весь текст',
        'regenerate': '🔄 Ещё раз',
        'back': '⬅️ Назад',
        'all_decisions': '📋 Все решения',
        'all_tasks': '📌 Все задачи',
        'speakers': '👥 Кто что говорил',
        'quotes': '💬 Цитаты огонь',
        'open_q': '❓ Что не решили',
        'recommendations': '💡 Мои советы',
        'enter_question': '✏️ **Спрашивай что хочешь!**\n\nНапример:\n• Какие бюджеты называли?\n• Кто был против?\n• Что решили по срокам?',
        'transcribed': '✅ Расслышал всё!\n👥 Спикеров: {speakers}\n🕐 Длительность: {mins} мин',
        'analysis_ready': '📋 **Разбор полётов:**',
        'file_ready': '📄 Держи файл! 💡 Секции раскрываются по клику',
        'no_data': '🤔 А данных-то нет! Сначала кинь файл.',
        'deep_dive_menu': '🔍 **Что разобрать подробнее?**',
        'analyzing_topic': '🧠 Копаю глубже...',
        'result': '📋 **Вот что накопал:**',
        'send_file_first': '🎤 Кинь аудио или видео — и погнали!',
        'lang_auto': '🔄 На языке аудио',
    },
    'en': {
        'welcome': '''🤖 **Hey! I'm Digital Smarty!**

Drop your meeting recording here — audio or video — and I'll break it all down:

📝 What was discussed (no fluff)
👥 Who said what
✅ Decisions and tasks
💡 My recommendations (free but priceless)

🎤 **Waiting for your file!**''',
        'choose_lang': '🌍 **What language for the analysis?**\n\n_(I\'ll detect audio language automatically)_',
        'downloading': '⏳ Hang on, grabbing the file...',
        'transcribing': '🎤 Listening carefully... (transcribing)',
        'analyzing': '🧠 Getting into the context...',
        'done': '✅ Done!',
        'error': '😬 Oops, something went wrong',
        'choose_action': '✨ **What next?**',
        'html_light': '🌐 HTML light',
        'html_dark': '🌑 HTML dark',
        'txt': '📄 TXT file',
        'deep_dive': '🔍 Dig deeper',
        'custom_q': '✏️ Ask anything',
        'transcript': '📜 Full text',
        'regenerate': '🔄 Try again',
        'back': '⬅️ Back',
        'all_decisions': '📋 All decisions',
        'all_tasks': '📌 All tasks',
        'speakers': '👥 Who said what',
        'quotes': '💬 Best quotes',
        'open_q': '❓ Unresolved',
        'recommendations': '💡 My advice',
        'enter_question': '✏️ **Ask me anything!**\n\nFor example:\n• What budgets were mentioned?\n• Who disagreed?\n• What about deadlines?',
        'transcribed': '✅ Got it all!\n👥 Speakers: {speakers}\n🕐 Duration: {mins} min',
        'analysis_ready': '📋 **Here\'s the breakdown:**',
        'file_ready': '📄 Here you go! 💡 Click sections to expand',
        'no_data': '🤔 No data yet! Send a file first.',
        'deep_dive_menu': '🔍 **What to explore?**',
        'analyzing_topic': '🧠 Digging deeper...',
        'result': '📋 **Here\'s what I found:**',
        'send_file_first': '🎤 Send audio or video — let\'s go!',
        'lang_auto': '🔄 Same as audio',
    },
    'kk': {
        'welcome': '🤖 **Сәлем! Мен Цифрлық Данышпанмын!**\n\nКездесу жазбасын жібер — талдап берем!\n\n🎤 **Файлды күтемін!**',
        'choose_lang': '🌍 **Талдау қай тілде болсын?**\n\n_(аудио тілін өзім анықтаймын)_',
        'downloading': '⏳ Файлды жүктеп жатырмын...',
        'transcribing': '🎤 Тыңдап жатырмын...',
        'analyzing': '🧠 Талдап жатырмын...',
        'done': '✅ Дайын!',
        'error': '😬 Қате болды',
        'choose_action': '✨ **Не істейміз?**',
        'html_light': '🌐 HTML ашық',
        'html_dark': '🌑 HTML қараңғы',
        'txt': '📄 TXT файл',
        'deep_dive': '🔍 Толығырақ',
        'custom_q': '✏️ Сұрақ қою',
        'transcript': '📜 Толық мәтін',
        'regenerate': '🔄 Қайта',
        'back': '⬅️ Артқа',
        'all_decisions': '📋 Барлық шешімдер',
        'all_tasks': '📌 Барлық тапсырмалар',
        'speakers': '👥 Кім не айтты',
        'quotes': '💬 Дәйексөздер',
        'open_q': '❓ Шешілмегендер',
        'recommendations': '💡 Ұсыныстар',
        'enter_question': '✏️ **Сұрағыңызды жазыңыз:**',
        'transcribed': '✅ Естідім!\n👥 Спикерлер: {speakers}\n🕐 Ұзақтығы: {mins} мин',
        'analysis_ready': '📋 **Талдау:**',
        'file_ready': '📄 Файл дайын!',
        'no_data': '🤔 Деректер жоқ!',
        'deep_dive_menu': '🔍 **Нені қарастырамыз?**',
        'analyzing_topic': '🧠 Талдаймын...',
        'result': '📋 **Нәтиже:**',
        'send_file_first': '🎤 Аудио немесе видео жіберіңіз!',
        'lang_auto': '🔄 Аудио тілінде',
    },
    'es': {
        'welcome': '🤖 **¡Hola! Soy Digital Smarty!**\n\nEnvía la grabación de tu reunión — ¡y la analizaré!\n\n🎤 **¡Esperando archivo!**',
        'choose_lang': '🌍 **¿En qué idioma el análisis?**\n\n_(detectaré el idioma del audio)_',
        'downloading': '⏳ Descargando archivo...',
        'transcribing': '🎤 Escuchando...',
        'analyzing': '🧠 Analizando...',
        'done': '✅ ¡Listo!',
        'error': '😬 Algo salió mal',
        'choose_action': '✨ **¿Qué sigue?**',
        'html_light': '🌐 HTML claro',
        'html_dark': '🌑 HTML oscuro',
        'txt': '📄 Archivo TXT',
        'deep_dive': '🔍 Más detalles',
        'custom_q': '✏️ Tu pregunta',
        'transcript': '📜 Texto completo',
        'regenerate': '🔄 Otra vez',
        'back': '⬅️ Atrás',
        'all_decisions': '📋 Todas las decisiones',
        'all_tasks': '📌 Todas las tareas',
        'speakers': '👥 Quién dijo qué',
        'quotes': '💬 Citas clave',
        'open_q': '❓ Sin resolver',
        'recommendations': '💡 Mis consejos',
        'enter_question': '✏️ **¡Pregunta lo que quieras!**',
        'transcribed': '✅ ¡Escuché todo!\n👥 Oradores: {speakers}\n🕐 Duración: {mins} min',
        'analysis_ready': '📋 **Análisis:**',
        'file_ready': '📄 ¡Aquí tienes!',
        'no_data': '🤔 ¡No hay datos!',
        'deep_dive_menu': '🔍 **¿Qué explorar?**',
        'analyzing_topic': '🧠 Analizando...',
        'result': '📋 **Resultado:**',
        'send_file_first': '🎤 ¡Envía audio o video!',
        'lang_auto': '🔄 Igual que audio',
    },
    'zh': {
        'welcome': '🤖 **你好！我是数字智者！**\n\n发送会议录音——我来分析！\n\n🎤 **等待文件！**',
        'choose_lang': '🌍 **分析用什么语言？**\n\n_(我会自动检测音频语言)_',
        'downloading': '⏳ 下载中...',
        'transcribing': '🎤 聆听中...',
        'analyzing': '🧠 分析中...',
        'done': '✅ 完成！',
        'error': '😬 出错了',
        'choose_action': '✨ **下一步？**',
        'html_light': '🌐 HTML 浅色',
        'html_dark': '🌑 HTML 深色',
        'txt': '📄 TXT 文件',
        'deep_dive': '🔍 深入分析',
        'custom_q': '✏️ 提问',
        'transcript': '📜 完整文本',
        'regenerate': '🔄 重新生成',
        'back': '⬅️ 返回',
        'all_decisions': '📋 所有决定',
        'all_tasks': '📌 所有任务',
        'speakers': '👥 发言人',
        'quotes': '💬 关键引用',
        'open_q': '❓ 未决问题',
        'recommendations': '💡 建议',
        'enter_question': '✏️ **请输入问题：**',
        'transcribed': '✅ 听到了！\n👥 发言人：{speakers}\n🕐 时长：{mins} 分钟',
        'analysis_ready': '📋 **分析：**',
        'file_ready': '📄 给你！',
        'no_data': '🤔 没有数据！',
        'deep_dive_menu': '🔍 **探索什么？**',
        'analyzing_topic': '🧠 分析中...',
        'result': '📋 **结果：**',
        'send_file_first': '🎤 发送音频或视频！',
        'lang_auto': '🔄 与音频相同',
    }
}

# ═══════════════════════════════════════════════════════════════
# USER CACHE
# ═══════════════════════════════════════════════════════════════

user_cache = {}


def get_cache(uid):
    if uid not in user_cache:
        user_cache[uid] = {'lang': 'ru'}
    return user_cache[uid]


def t(uid, key, **kwargs):
    cache = get_cache(uid)
    lang = cache.get('output_lang', 'ru')
    text = TRANSLATIONS.get(lang, TRANSLATIONS['ru']).get(key, TRANSLATIONS['ru'].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text


# ═══════════════════════════════════════════════════════════════
# HTML GENERATOR - С НАЗВАНИЕМ ФАЙЛА ПО ТЕМЕ И ДАТЕ
# ═══════════════════════════════════════════════════════════════

def generate_html(content, theme="light", lang="ru", meeting_title=None):
    """Генерирует HTML с раскрывающимися секциями"""
    
    dark_css = """:root{--bg:#0f0f0f;--card:#1a1a2e;--card2:#16213e;--text:#e4e4e7;--text2:#a1a1aa;--accent:#3b82f6;--accent2:#8b5cf6;--success:#10b981;--border:#2d2d44}
body{font-family:'Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.8;color:var(--text);background:var(--bg);padding:40px 20px;max-width:900px;margin:0 auto}
h1{font-size:28px;color:#fff;border-bottom:3px solid var(--accent);padding-bottom:15px;margin-bottom:10px}
.meta{color:var(--text2);font-size:13px;margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid var(--border)}
details{background:var(--card);border:1px solid var(--border);border-radius:12px;margin:15px 0;overflow:hidden;transition:all 0.3s}
details[open]{box-shadow:0 4px 20px rgba(59,130,246,0.15)}
summary{cursor:pointer;padding:18px 20px;font-weight:600;font-size:16px;color:#fff;list-style:none;display:flex;align-items:center;gap:10px;background:linear-gradient(135deg,var(--card),var(--card2))}
summary::-webkit-details-marker{display:none}
summary::before{content:'▶';color:var(--accent);font-size:12px;transition:transform 0.3s}
details[open] summary::before{transform:rotate(90deg)}
summary .icon{font-size:20px}
details>div{padding:20px;background:var(--card2);border-top:1px solid var(--border)}
h3{font-size:15px;color:var(--accent);margin:20px 0 10px;padding-left:12px;border-left:3px solid var(--accent)}
strong{color:#fff}
ul,ol{padding-left:24px;margin:10px 0}
li{margin-bottom:10px;color:var(--text)}
blockquote{background:rgba(139,92,246,0.1);border-left:4px solid var(--accent2);padding:15px 20px;margin:15px 0;border-radius:0 8px 8px 0;font-style:italic;color:#c4b5fd}
.topic-detail{background:rgba(59,130,246,0.05);border-radius:8px;padding:15px;margin:10px 0}
.recommendation{background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(59,130,246,0.1));border:1px solid var(--success);border-radius:12px;padding:20px;margin:20px 0}
.recommendation h3{color:var(--success);border-color:var(--success)}
table{width:100%;border-collapse:collapse;margin:15px 0}
th,td{border:1px solid var(--border);padding:10px;text-align:left}
th{background:var(--card)}"""

    light_css = """:root{--bg:#f8fafc;--card:#fff;--card2:#f1f5f9;--text:#1e293b;--text2:#64748b;--accent:#3b82f6;--accent2:#8b5cf6;--success:#10b981;--border:#e2e8f0}
body{font-family:'Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.8;color:var(--text);background:var(--bg);padding:40px 20px;max-width:900px;margin:0 auto}
h1{font-size:28px;color:#0f172a;border-bottom:3px solid var(--accent);padding-bottom:15px;margin-bottom:10px}
.meta{color:var(--text2);font-size:13px;margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid var(--border)}
details{background:var(--card);border:1px solid var(--border);border-radius:12px;margin:15px 0;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.05);transition:all 0.3s}
details[open]{box-shadow:0 4px 20px rgba(59,130,246,0.12)}
summary{cursor:pointer;padding:18px 20px;font-weight:600;font-size:16px;color:#0f172a;list-style:none;display:flex;align-items:center;gap:10px;background:linear-gradient(135deg,#fff,var(--card2))}
summary::-webkit-details-marker{display:none}
summary::before{content:'▶';color:var(--accent);font-size:12px;transition:transform 0.3s}
details[open] summary::before{transform:rotate(90deg)}
summary .icon{font-size:20px}
details>div{padding:20px;background:var(--card2);border-top:1px solid var(--border)}
h3{font-size:15px;color:var(--accent);margin:20px 0 10px;padding-left:12px;border-left:3px solid var(--accent)}
strong{color:#0f172a}
ul,ol{padding-left:24px;margin:10px 0}
li{margin-bottom:10px}
blockquote{background:rgba(139,92,246,0.08);border-left:4px solid var(--accent2);padding:15px 20px;margin:15px 0;border-radius:0 8px 8px 0;font-style:italic;color:#6b21a8}
.topic-detail{background:rgba(59,130,246,0.03);border-radius:8px;padding:15px;margin:10px 0}
.recommendation{background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(59,130,246,0.08));border:1px solid var(--success);border-radius:12px;padding:20px;margin:20px 0}
.recommendation h3{color:var(--success);border-color:var(--success)}
table{width:100%;border-collapse:collapse;margin:15px 0}
th,td{border:1px solid var(--border);padding:10px;text-align:left}
th{background:var(--card2)}"""

    css = dark_css if theme == "dark" else light_css

    section_icons = {
        'саммари': '📋', 'summary': '📋', 'қысқаша': '📋', 'resumen': '📋', '摘要': '📋',
        'темы': '🎯', 'topics': '🎯', 'тақырып': '🎯', 'temas': '🎯', '主题': '🎯',
        'позиции': '👥', 'positions': '👥', 'participant': '👥', 'posicion': '👥', '参与': '👥',
        'решения': '✅', 'decisions': '✅', 'шешім': '✅', 'decisiones': '✅', '决定': '✅',
        'задачи': '📌', 'tasks': '📌', 'тапсырма': '📌', 'tareas': '📌', '任务': '📌',
        'вопросы': '❓', 'questions': '❓', 'сұрақ': '❓', 'preguntas': '❓', '问题': '❓',
        'цитаты': '💬', 'quotes': '💬', 'дәйексөз': '💬', 'citas': '💬', '引用': '💬',
        'рекомендации': '💡', 'recommendations': '💡', 'ұсыныс': '💡', 'recomendaciones': '💡', '建议': '💡',
        'план': '🚀', 'action': '🚀', 'жоспар': '🚀', 'plan': '🚀', '计划': '🚀',
        'выводы': '🎯', 'conclusions': '🎯', 'қорытынды': '🎯', 'conclusiones': '🎯', '结论': '🎯',
        'тема': '📌', 'topic': '📌',
    }

    html = content
    sections = re.split(r'^## ', html, flags=re.MULTILINE)
    processed = []

    for i, section in enumerate(sections):
        if i == 0:
            section = re.sub(r'^# (.+)$', r'<h1>\1</h1>', section, flags=re.MULTILINE)
            processed.append(section)
        else:
            lines = section.split('\n', 1)
            title = lines[0].strip()
            body = lines[1] if len(lines) > 1 else ""

            icon = '📄'
            for key, emoji in section_icons.items():
                if key.lower() in title.lower():
                    icon = emoji
                    break

            # Обработка подразделов h3
            body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', body, flags=re.MULTILINE)
            body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body)
            body = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', body, flags=re.MULTILINE)
            
            # Таблицы
            def convert_table(match):
                lines = match.group(0).strip().split('\n')
                if len(lines) < 2:
                    return match.group(0)
                html_table = '<table><thead><tr>'
                headers = [h.strip() for h in lines[0].split('|') if h.strip()]
                for h in headers:
                    html_table += f'<th>{h}</th>'
                html_table += '</tr></thead><tbody>'
                for line in lines[2:]:
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if cells:
                        html_table += '<tr>'
                        for c in cells:
                            html_table += f'<td>{c}</td>'
                        html_table += '</tr>'
                html_table += '</tbody></table>'
                return html_table
            
            body = re.sub(r'(\|.+\|[\n\r]+\|[-:| ]+\|[\n\r]+(?:\|.+\|[\n\r]*)+)', convert_table, body)
            
            # Списки
            body = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', body, flags=re.MULTILINE)
            body = re.sub(r'^- (.+)$', r'<li>\1</li>', body, flags=re.MULTILINE)
            body = re.sub(r'(<li>.*?</li>\n*)+', lambda m: f'<ul>{m.group(0)}</ul>', body, flags=re.DOTALL)
            body = re.sub(r'\n\n+', '</p><p>', body)
            body = f'<p>{body}</p>'
            body = body.replace('<p></p>', '').replace('<p><ul>', '<ul>').replace('</ul></p>', '</ul>')
            body = body.replace('<p><h3>', '<h3>').replace('</h3></p>', '</h3>')
            body = body.replace('<p><blockquote>', '<blockquote>').replace('</blockquote></p>', '</blockquote>')
            body = body.replace('<p><table>', '<table>').replace('</table></p>', '</table>')

            extra_class = ''
            if 'рекоменд' in title.lower() or 'recommend' in title.lower() or 'совет' in title.lower():
                extra_class = 'recommendation'

            processed.append(f'<details><summary><span class="icon">{icon}</span> {title}</summary><div class="{extra_class}">{body}</div></details>')

    html_body = '\n'.join(processed)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    lang_names = {'ru': 'Русский', 'en': 'English', 'kk': 'Қазақша', 'es': 'Español', 'zh': '中文'}
    
    title_text = meeting_title if meeting_title else "Meeting Analysis"

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_text} — {date_str}</title>
<style>{css}</style>
</head>
<body>
<div class="meta">🤖 Цифровой Умник | 📅 {date_str} | 🌍 {lang_names.get(lang, lang)}</div>
{html_body}
<script>document.querySelectorAll('details').forEach((d, i) => {{ if(i < 3) d.open = true; }});</script>
</body>
</html>'''


def extract_meeting_title(analysis_text):
    """Извлекает тему встречи из анализа для имени файла"""
    # Ищем заголовок или первую тему
    match = re.search(r'^# (.+)$', analysis_text, re.MULTILINE)
    if match:
        title = match.group(1)
        # Убираем эмодзи и спецсимволы для имени файла
        title = re.sub(r'[🤖📋🎯👥✅📌❓💬💡🚀]', '', title)
        title = re.sub(r'[^\w\s-]', '', title).strip()
        if title and len(title) > 3:
            return title[:50]  # Ограничиваем длину
    return None


def save_html(content, theme, lang):
    """Сохраняет HTML с именем: Тема_ДАТА.html"""
    meeting_title = extract_meeting_title(content)
    html = generate_html(content, theme, lang, meeting_title)
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    if meeting_title:
        # Транслит для имени файла
        safe_title = re.sub(r'[^\w\s-]', '', meeting_title).replace(' ', '_')[:30]
        filename = f"{safe_title}_{date_str}.html"
    else:
        filename = f"meeting_{date_str}.html"
    
    path = f"/tmp/{filename}"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return path


def save_txt(content):
    """Сохраняет TXT с именем: Тема_ДАТА.txt"""
    meeting_title = extract_meeting_title(content)
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    
    if meeting_title:
        safe_title = re.sub(r'[^\w\s-]', '', meeting_title).replace(' ', '_')[:30]
        filename = f"{safe_title}_{date_str}.txt"
    else:
        filename = f"meeting_{date_str}.txt"
    
    path = f"/tmp/{filename}"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path


# ═══════════════════════════════════════════════════════════════
# TRANSCRIPTION (Deepgram) - АВТО ОПРЕДЕЛЕНИЕ ЯЗЫКА
# ═══════════════════════════════════════════════════════════════

def transcribe_file(file_path):
    """Транскрибация с АВТО определением языка"""
    try:
        dg_key = DEEPGRAM_KEY.strip() if DEEPGRAM_KEY else None
        if not dg_key:
            return None, "DEEPGRAM_API_KEY not set!"

        headers = {"Authorization": f"Token {dg_key}"}
        # detect_language=true - Deepgram сам определит язык!
        params = "model=nova-2&detect_language=true&diarize=true&smart_format=true&utterances=true&punctuate=true"

        with open(file_path, "rb") as f:
            file_data = f.read()

        resp = http_requests.post(
            f"https://api.deepgram.com/v1/listen?{params}",
            headers=headers,
            data=file_data,
            timeout=1800
        )

        if resp.status_code == 401:
            return None, "Invalid Deepgram key!"
        if resp.status_code != 200:
            return None, f"Deepgram error: {resp.status_code}"

        result = resp.json()
        
        # Определяем язык аудио
        detected_lang = "en"
        if "results" in result and "channels" in result["results"]:
            channels = result["results"]["channels"]
            if channels and channels[0].get("detected_language"):
                detected_lang = channels[0]["detected_language"]
        
        # Маппинг Deepgram кодов
        lang_map = {
            'ru': 'ru', 'russian': 'ru',
            'en': 'en', 'en-US': 'en', 'en-GB': 'en', 'english': 'en',
            'kk': 'kk', 'kazakh': 'kk',
            'es': 'es', 'spanish': 'es',
            'zh': 'zh', 'zh-CN': 'zh', 'zh-TW': 'zh', 'chinese': 'zh',
        }
        detected_lang = lang_map.get(detected_lang, 'en')

        parts = []
        speakers = set()

        speaker_labels = {'ru': 'Спикер', 'en': 'Speaker', 'kk': 'Спикер', 'es': 'Orador', 'zh': '发言人'}
        label = speaker_labels.get(detected_lang, 'Speaker')

        if "results" in result and "utterances" in result["results"]:
            for u in result["results"]["utterances"]:
                spk = f"{label} {u.get('speaker', '?')}"
                speakers.add(u.get('speaker', 0))
                parts.append(f"**{spk}:** {u.get('transcript', '')}")

        if not parts and "results" in result:
            ch = result["results"].get("channels", [])
            if ch and ch[0].get("alternatives"):
                parts = [ch[0]["alternatives"][0].get("transcript", "")]

        if not parts:
            return None, "Could not recognize speech"

        return {
            "transcript": "\n\n".join(parts),
            "duration": result.get("metadata", {}).get("duration", 0),
            "speakers": len(speakers) or 1,
            "detected_language": detected_lang
        }, None

    except Exception as e:
        return None, str(e)


# ═══════════════════════════════════════════════════════════════
# ANALYSIS PROMPTS - С УСЛОВНЫМИ ПОЗИЦИЯМИ
# ═══════════════════════════════════════════════════════════════

ANALYSIS_PROMPTS = {
    'ru': """Ты — Цифровой Умник, остроумный AI-аналитик встреч. Твой стиль: дружелюбный, немного саркастичный, говоришь просто и без канцелярита.

Создай ДЕТАЛЬНЫЙ анализ встречи:

# 🤖 Разбор от Цифрового Умника

## 📋 Краткое саммари
3-5 предложений: суть встречи, ключевой итог. Добавь свой комментарий!

## 🎯 Ключевые темы
Для КАЖДОЙ темы создай подраздел:

### 📌 [Название темы 1]
- **Суть:** что обсуждали
- **Детали:** ключевые моменты
- **Цитаты:** дословные цитаты участников
- **Итог:** к чему пришли

### 📌 [Название темы 2]
(так же для каждой темы)

## 👥 Позиции участников
⚠️ ВАЖНО: Этот раздел ТОЛЬКО если были РЕАЛЬНЫЕ разногласия или разные точки зрения!
Если все согласны — НЕ выдумывай конфликты, просто напиши "Участники были единодушны" или пропусти раздел.

Если были разногласия:
### Позиция 1: [Суть]
- Кто придерживался: ...
- Аргументы: ...
- Цитаты: ...

### Позиция 2: [Суть]
(аналогично)

## ✅ Принятые решения
Пронумерованный список с контекстом. Если решений не было — так и напиши.

## 📌 Задачи
| Задача | Ответственный | Срок | Комментарий |
|--------|---------------|------|-------------|

Если задачи не назначались — напиши "Конкретные задачи не назначены"

## ❓ Открытые вопросы
Что осталось нерешённым, требует обсуждения.

## 💬 Ключевые цитаты
Самые показательные высказывания дословно.

## 💡 Мои рекомендации
5-7 конкретных советов. Говори прямо!

## 🚀 Что делать дальше
- **Срочно:**
- **На неделе:**
- **В перспективе:**

## 🎯 Главные выводы
Топ-5 выводов встречи.

ВАЖНО: 
- Будь подробным, приводи цитаты
- НЕ выдумывай конфликты если их не было
- Каждая тема — отдельный подраздел с деталями""",

    'en': """You are Digital Smarty, a witty AI meeting analyst. Style: friendly, slightly sarcastic, speak simply.

Create a DETAILED meeting analysis:

# 🤖 Analysis by Digital Smarty

## 📋 Executive Summary
3-5 sentences with your commentary!

## 🎯 Key Topics
For EACH topic create a subsection:

### 📌 [Topic 1 Name]
- **Core:** what was discussed
- **Details:** key points
- **Quotes:** verbatim participant quotes
- **Outcome:** what was decided

### 📌 [Topic 2 Name]
(same for each topic)

## 👥 Participant Positions
⚠️ IMPORTANT: This section ONLY if there were REAL disagreements!
If everyone agreed — DON'T invent conflicts, just write "Participants were unanimous" or skip section.

If there were disagreements:
### Position 1: [Core]
- Who held it: ...
- Arguments: ...
- Quotes: ...

## ✅ Decisions Made
Numbered list with context. If no decisions — say so.

## 📌 Tasks
| Task | Owner | Deadline | Comment |
|------|-------|----------|---------|

If no tasks assigned — write "No specific tasks assigned"

## ❓ Open Questions

## 💬 Key Quotes

## 💡 My Recommendations
5-7 specific tips. Be direct!

## 🚀 Action Plan
- **Urgent:**
- **This week:**
- **Long-term:**

## 🎯 Key Takeaways

IMPORTANT:
- Be detailed, include quotes
- DON'T invent conflicts if there weren't any
- Each topic — separate subsection with details"""
}

# Копируем для остальных языков
ANALYSIS_PROMPTS['kk'] = ANALYSIS_PROMPTS['en']
ANALYSIS_PROMPTS['es'] = ANALYSIS_PROMPTS['en']
ANALYSIS_PROMPTS['zh'] = ANALYSIS_PROMPTS['en']


def analyze(transcript, duration, speakers, output_lang='ru', audio_lang='ru'):
    """Анализ с переводом если нужно"""
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        
        # Если языки разные - добавляем инструкцию перевода
        if output_lang != audio_lang:
            lang_names = {
                'ru': 'РУССКОМ языке',
                'en': 'ENGLISH',
                'kk': 'ҚАЗАҚ ТІЛІНДЕ',
                'es': 'ESPAÑOL',
                'zh': '中文'
            }
            translate_instruction = f"\n\n⚠️ ВАЖНО: Транскрипт может быть на другом языке. Сделай ВЕСЬ анализ на {lang_names.get(output_lang, output_lang)}! Переведи всё."
        else:
            translate_instruction = ""
        
        prompt = ANALYSIS_PROMPTS.get(output_lang, ANALYSIS_PROMPTS['en']) + translate_instruction

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Транскрипт встречи:\n\n{transcript[:50000]}"}
            ],
            temperature=0.4,
            max_tokens=8000
        )

        result = resp.choices[0].message.content
        mins = int(duration // 60)
        secs = int(duration % 60)
        words = len(transcript.split())

        stats = {
            'ru': f"\n\n---\n📊 **Статистика:** {mins} мин {secs} сек | {speakers} спикер(ов) | {words} слов",
            'en': f"\n\n---\n📊 **Stats:** {mins} min {secs} sec | {speakers} speaker(s) | {words} words",
            'kk': f"\n\n---\n📊 **Статистика:** {mins} мин {secs} сек | {speakers} спикер | {words} сөз",
            'es': f"\n\n---\n📊 **Estadísticas:** {mins} min {secs} seg | {speakers} orador(es) | {words} palabras",
            'zh': f"\n\n---\n📊 **统计:** {mins} 分 {secs} 秒 | {speakers} 位发言人 | {words} 词",
        }

        return result + stats.get(output_lang, stats['en'])

    except Exception as e:
        return f"Analysis error: {e}"


def custom_analyze(transcript, question, output_lang='ru'):
    """Кастомный анализ на выбранном языке"""
    try:
        client = OpenAI(api_key=OPENAI_KEY)

        lang_instructions = {
            'ru': f"Ты — Цифровой Умник. Ответь на вопрос ПОДРОБНО, с цитатами. Отвечай на РУССКОМ языке. НЕ выдумывай то, чего не было.\n\nВопрос: {question}",
            'en': f"You are Digital Smarty. Answer in DETAIL, with quotes. Answer in ENGLISH. DON'T invent things that weren't said.\n\nQuestion: {question}",
            'kk': f"Сен — Цифрлық Данышпан. Сұраққа ТОЛЫҚ жауап бер. ҚАЗАҚ тілінде жауап бер.\n\nСұрақ: {question}",
            'es': f"Eres Digital Smarty. Responde en DETALLE. Responde en ESPAÑOL.\n\nPregunta: {question}",
            'zh': f"你是数字智者。详细回答。用中文回答。\n\n问题: {question}",
        }

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": lang_instructions.get(output_lang, lang_instructions['en'])},
                {"role": "user", "content": f"Transcript:\n\n{transcript[:50000]}"}
            ],
            temperature=0.4,
            max_tokens=4000
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def lang_kb(uid):
    """Выбор языка РЕЗУЛЬТАТА"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, 'lang_auto'), callback_data="lang_auto")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kk"),
         InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
        [InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh")]
    ])


def main_kb(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, 'html_light'), callback_data="html_light"),
         InlineKeyboardButton(t(uid, 'html_dark'), callback_data="html_dark")],
        [InlineKeyboardButton(t(uid, 'txt'), callback_data="txt")],
        [InlineKeyboardButton(t(uid, 'deep_dive'), callback_data="deep_dive")],
        [InlineKeyboardButton(t(uid, 'custom_q'), callback_data="custom")],
        [InlineKeyboardButton(t(uid, 'transcript'), callback_data="transcript")],
        [InlineKeyboardButton(t(uid, 'regenerate'), callback_data="regenerate")]
    ])


def topics_kb(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, 'all_decisions'), callback_data="topic_decisions")],
        [InlineKeyboardButton(t(uid, 'all_tasks'), callback_data="topic_tasks")],
        [InlineKeyboardButton(t(uid, 'speakers'), callback_data="topic_speakers")],
        [InlineKeyboardButton(t(uid, 'quotes'), callback_data="topic_quotes")],
        [InlineKeyboardButton(t(uid, 'open_q'), callback_data="topic_open")],
        [InlineKeyboardButton(t(uid, 'recommendations'), callback_data="topic_recommendations")],
        [InlineKeyboardButton(t(uid, 'back'), callback_data="back_main")]
    ])


def continue_kb(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, 'html_light'), callback_data="html_light_c"),
         InlineKeyboardButton(t(uid, 'html_dark'), callback_data="html_dark_c")],
        [InlineKeyboardButton(t(uid, 'custom_q'), callback_data="custom")],
        [InlineKeyboardButton(t(uid, 'back'), callback_data="back_main")]
    ])


# ═══════════════════════════════════════════════════════════════
# BOT
# ═══════════════════════════════════════════════════════════════

app = Client("meeting_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH or "", bot_token=BOT_TOKEN or "")


@app.on_message(filters.command("start"))
async def start_cmd(client, msg):
    uid = msg.from_user.id
    cache = get_cache(uid)
    cache['output_lang'] = 'ru'
    await msg.reply(t(uid, 'welcome'))


@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client, msg):
    if msg.document:
        mime = msg.document.mime_type or ""
        if not any(x in mime for x in ["audio", "video", "octet"]):
            return

    uid = msg.from_user.id
    cache = get_cache(uid)
    cache['file_msg'] = msg
    cache['output_lang'] = 'ru'  # Default для кнопок
    await msg.reply(t(uid, 'choose_lang'), reply_markup=lang_kb(uid))


@app.on_callback_query()
async def callback(client, cb):
    uid = cb.from_user.id
    data = cb.data
    cache = get_cache(uid)

    async def safe_edit(text, reply_markup=None):
        try:
            await cb.message.edit_text(text, reply_markup=reply_markup)
        except Exception:
            pass

    try:
        if data.startswith("lang_"):
            lang_choice = data.replace("lang_", "")
            cache['lang_choice'] = lang_choice

            if 'file_msg' not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return

            msg = cache['file_msg']
            await cb.answer("⏳")
            await safe_edit(t(uid, 'downloading'))

            try:
                with tempfile.TemporaryDirectory() as tmp:
                    path = await msg.download(file_name=f"{tmp}/media")
                    await safe_edit(t(uid, 'transcribing'))

                    # Транскрибируем с АВТО определением языка
                    result, err = transcribe_file(path)
                    if err:
                        await safe_edit(f"{t(uid, 'error')}: {err}")
                        return

                    cache["transcript"] = result["transcript"]
                    cache["duration"] = result["duration"]
                    cache["speakers"] = result["speakers"]
                    cache["audio_lang"] = result["detected_language"]
                    
                    # Определяем язык вывода
                    if lang_choice == "auto":
                        output_lang = result["detected_language"]
                    else:
                        output_lang = lang_choice
                    
                    cache["output_lang"] = output_lang

                    mins = int(result['duration'] // 60)
                    
                    lang_names = {'ru': '🇷🇺 Русский', 'en': '🇬🇧 English', 'kk': '🇰🇿 Қазақша', 'es': '🇪🇸 Español', 'zh': '🇨🇳 中文'}
                    detected_name = lang_names.get(result["detected_language"], result["detected_language"])
                    output_name = lang_names.get(output_lang, output_lang)
                    
                    status_text = t(uid, 'transcribed', speakers=result['speakers'], mins=mins)
                    status_text += f"\n\n🎤 Аудио: {detected_name}\n📄 Результат: {output_name}"
                    await safe_edit(status_text)

                    # Анализируем
                    summary = analyze(
                        result["transcript"], 
                        result["duration"], 
                        result["speakers"], 
                        output_lang=output_lang,
                        audio_lang=result["detected_language"]
                    )
                    cache["summary"] = summary

                    try:
                        await cb.message.delete()
                    except Exception:
                        pass

                    preview = summary[:3500] + "\n\n_...полная версия в файле_" if len(summary) > 3500 else summary
                    await msg.reply(f"{t(uid, 'analysis_ready')}\n\n{preview}")
                    await msg.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))

            except Exception as e:
                await safe_edit(f"{t(uid, 'error')}: {e}")

        elif data.startswith("html_"):
            parts = data.split("_")
            theme = parts[1]
            is_custom = len(parts) > 2 and parts[2] == "c"
            key = "custom_result" if is_custom else "summary"

            if key not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return

            await cb.answer("⏳")
            lang = cache.get('output_lang', 'ru')
            path = save_html(cache[key], theme, lang)
            await cb.message.reply_document(path, caption=t(uid, 'file_ready'))
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))

        elif data == "txt":
            if "summary" not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return
            await cb.answer("⏳")
            path = save_txt(cache["summary"])
            await cb.message.reply_document(path, caption="📄 TXT")
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))

        elif data == "deep_dive":
            if "transcript" not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return
            await cb.answer()
            await safe_edit(t(uid, 'deep_dive_menu'), reply_markup=topics_kb(uid))

        elif data.startswith("topic_"):
            if "transcript" not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return

            topic = data.replace("topic_", "")
            lang = cache.get('output_lang', 'ru')

            prompts = {
                'decisions': {
                    'ru': 'Перечисли ВСЕ принятые решения подробно с контекстом и цитатами. Если решений не было — так и скажи.',
                    'en': 'List ALL decisions in detail with context and quotes. If no decisions — say so.'
                },
                'tasks': {
                    'ru': 'Перечисли ВСЕ задачи в виде таблицы: что сделать, кто делает, когда, детали. Если задач не было — так и скажи.',
                    'en': 'List ALL tasks as a table: what, who, when, details. If no tasks — say so.'
                },
                'speakers': {
                    'ru': 'Опиши что говорил КАЖДЫЙ спикер: основные тезисы, позиция, цитаты. НЕ выдумывай конфликты если их не было.',
                    'en': 'Describe what EACH speaker said: main points, position, quotes. DON\'T invent conflicts.'
                },
                'quotes': {
                    'ru': 'Выпиши самые показательные и важные цитаты ДОСЛОВНО с указанием кто это сказал.',
                    'en': 'List the most revealing quotes VERBATIM with attribution.'
                },
                'open': {
                    'ru': 'Что осталось нерешённым? Какие вопросы открыты? Что требует дополнительного обсуждения?',
                    'en': 'What remains unresolved? What needs further discussion?'
                },
                'recommendations': {
                    'ru': 'Дай подробные рекомендации: что улучшить, на что обратить внимание, какие риски, что делать дальше. 7-10 пунктов.',
                    'en': 'Give detailed recommendations: what to improve, risks, next steps. 7-10 points.'
                }
            }

            prompt = prompts.get(topic, {}).get(lang, prompts.get(topic, {}).get('en', ''))

            await cb.answer("🧠")
            await safe_edit(t(uid, 'analyzing_topic'))

            result = custom_analyze(cache["transcript"], prompt, lang)
            cache["custom_result"] = result

            await cb.message.reply(f"{t(uid, 'result')}\n\n{result[:4000]}")
            if len(result) > 4000:
                await cb.message.reply(result[4000:8000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=continue_kb(uid))

        elif data == "custom":
            cache["stage"] = "waiting_question"
            await cb.answer()
            await safe_edit(t(uid, 'enter_question'))

        elif data == "transcript":
            if "transcript" not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return
            await cb.answer()
            tr = cache["transcript"]
            await cb.message.reply("📜 **Транскрипт:**")
            for i in range(0, len(tr), 4000):
                await cb.message.reply(tr[i:i+4000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))

        elif data == "regenerate":
            if "transcript" not in cache:
                await cb.answer(t(uid, 'no_data'), show_alert=True)
                return
            await cb.answer("🔄")
            await safe_edit(t(uid, 'analyzing'))

            output_lang = cache.get('output_lang', 'ru')
            audio_lang = cache.get('audio_lang', 'ru')
            summary = analyze(
                cache["transcript"],
                cache.get("duration", 0),
                cache.get("speakers", 1),
                output_lang=output_lang,
                audio_lang=audio_lang
            )
            cache["summary"] = summary

            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await cb.message.reply(f"{t(uid, 'analysis_ready')}\n\n{preview}")
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))

        elif data == "back_main":
            await cb.answer()
            await safe_edit(t(uid, 'choose_action'), reply_markup=main_kb(uid))

    except Exception as e:
        await cb.message.reply(f"❌ Error: {e}")


@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, msg):
    uid = msg.from_user.id
    cache = get_cache(uid)

    if cache.get("stage") == "waiting_question" and "transcript" in cache:
        lang = cache.get('output_lang', 'ru')
        status = await msg.reply(t(uid, 'analyzing_topic'))

        try:
            result = custom_analyze(cache["transcript"], msg.text, lang)
            cache["custom_result"] = result
            cache["stage"] = None
            await status.delete()

            await msg.reply(f"{t(uid, 'result')}\n\n{result[:4000]}")
            if len(result) > 4000:
                await msg.reply(result[4000:8000])
            await msg.reply(t(uid, 'choose_action'), reply_markup=continue_kb(uid))

        except Exception as e:
            await status.edit_text(f"❌ Error: {e}")
    else:
        await msg.reply(t(uid, 'send_file_first'))


if __name__ == "__main__":
    print("🤖 Цифровой Умник запускается...")
    print("🌍 Языки: RU, EN, KK, ES, ZH")
    print("📁 Имена файлов: Тема_Дата.html/txt")
    app.run()
