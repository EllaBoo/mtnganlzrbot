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
    'ru': {'name': '🇷🇺 Русский', 'code': 'ru', 'deepgram': 'ru'},
    'en': {'name': '🇬🇧 English', 'code': 'en', 'deepgram': 'en'},
    'kk': {'name': '🇰🇿 Қазақша', 'code': 'kk', 'deepgram': 'kk'},
    'es': {'name': '🇪🇸 Español', 'code': 'es', 'deepgram': 'es'},
    'zh': {'name': '🇨🇳 中文', 'code': 'zh', 'deepgram': 'zh'},
}

TRANSLATIONS = {
    'ru': {
        'welcome': '👋 **Meeting Analyzer**\n\nОтправь аудио или видео встречи и получи детальный анализ с рекомендациями эксперта!\n\n🎤 **Жду файл!**',
        'choose_lang': '🌍 **Выбери язык анализа:**\n\nИли я определю язык автоматически.',
        'auto_lang': '🔄 Авто (язык аудио)',
        'downloading': '⏳ Скачиваю файл...',
        'transcribing': '🎤 Транскрибирую аудио...',
        'analyzing': '🧠 Анализирую содержание...',
        'done': '✅ Готово!',
        'error': '❌ Ошибка',
        'choose_action': '✨ **Выбери действие:**',
        'html_light': '🌐 HTML светлая',
        'html_dark': '🌑 HTML тёмная',
        'txt': '📄 TXT файл',
        'deep_dive': '🔍 Подробнее',
        'custom_q': '✏️ Свой вопрос',
        'transcript': '📜 Транскрипт',
        'regenerate': '🔄 Заново',
        'back': '⬅️ Назад',
        'all_decisions': '📋 Все решения',
        'all_tasks': '📌 Все задачи',
        'speakers': '👥 Позиции спикеров',
        'quotes': '💬 Ключевые цитаты',
        'open_q': '❓ Открытые вопросы',
        'recommendations': '💡 Рекомендации',
        'enter_question': '✏️ **Введи свой вопрос:**\n\nНапример:\n• Какие бюджеты обсуждались?\n• Что решили по срокам?\n• Какие риски упоминали?',
    },
    'en': {
        'welcome': '👋 **Meeting Analyzer**\n\nSend audio or video of your meeting and get a detailed analysis with expert recommendations!\n\n🎤 **Waiting for file!**',
        'choose_lang': '🌍 **Choose analysis language:**\n\nOr I will detect automatically.',
        'auto_lang': '🔄 Auto (audio language)',
        'downloading': '⏳ Downloading file...',
        'transcribing': '🎤 Transcribing audio...',
        'analyzing': '🧠 Analyzing content...',
        'done': '✅ Done!',
        'error': '❌ Error',
        'choose_action': '✨ **Choose action:**',
        'html_light': '🌐 HTML light',
        'html_dark': '🌑 HTML dark',
        'txt': '📄 TXT file',
        'deep_dive': '🔍 Deep dive',
        'custom_q': '✏️ Ask question',
        'transcript': '📜 Transcript',
        'regenerate': '🔄 Regenerate',
        'back': '⬅️ Back',
        'all_decisions': '📋 All decisions',
        'all_tasks': '📌 All tasks',
        'speakers': '👥 Speaker positions',
        'quotes': '💬 Key quotes',
        'open_q': '❓ Open questions',
        'recommendations': '💡 Recommendations',
        'enter_question': '✏️ **Enter your question:**\n\nFor example:\n• What budgets were discussed?\n• What was decided about deadlines?\n• What risks were mentioned?',
    },
    'kk': {
        'welcome': '👋 **Meeting Analyzer**\n\nКездесу аудио немесе видеосын жіберіңіз және сарапшы ұсыныстарымен толық талдау алыңыз!\n\n🎤 **Файлды күтемін!**',
        'choose_lang': '🌍 **Талдау тілін таңдаңыз:**',
        'auto_lang': '🔄 Авто (аудио тілі)',
        'downloading': '⏳ Файл жүктелуде...',
        'transcribing': '🎤 Аудио транскрипциясы...',
        'analyzing': '🧠 Мазмұнды талдау...',
        'done': '✅ Дайын!',
        'error': '❌ Қате',
        'choose_action': '✨ **Әрекетті таңдаңыз:**',
        'html_light': '🌐 HTML ашық',
        'html_dark': '🌑 HTML қараңғы',
        'txt': '📄 TXT файл',
        'deep_dive': '🔍 Толығырақ',
        'custom_q': '✏️ Сұрақ қою',
        'transcript': '📜 Транскрипт',
        'regenerate': '🔄 Қайта жасау',
        'back': '⬅️ Артқа',
        'all_decisions': '📋 Барлық шешімдер',
        'all_tasks': '📌 Барлық тапсырмалар',
        'speakers': '👥 Спикерлер',
        'quotes': '💬 Дәйексөздер',
        'open_q': '❓ Ашық сұрақтар',
        'recommendations': '💡 Ұсыныстар',
        'enter_question': '✏️ **Сұрағыңызды енгізіңіз:**',
    },
    'es': {
        'welcome': '👋 **Meeting Analyzer**\n\nEnvía audio o video de tu reunión y obtén un análisis detallado con recomendaciones de expertos!\n\n🎤 **¡Esperando archivo!**',
        'choose_lang': '🌍 **Elige el idioma del análisis:**',
        'auto_lang': '🔄 Auto (idioma del audio)',
        'downloading': '⏳ Descargando archivo...',
        'transcribing': '🎤 Transcribiendo audio...',
        'analyzing': '🧠 Analizando contenido...',
        'done': '✅ ¡Listo!',
        'error': '❌ Error',
        'choose_action': '✨ **Elige acción:**',
        'html_light': '🌐 HTML claro',
        'html_dark': '🌑 HTML oscuro',
        'txt': '📄 Archivo TXT',
        'deep_dive': '🔍 Más detalles',
        'custom_q': '✏️ Tu pregunta',
        'transcript': '📜 Transcripción',
        'regenerate': '🔄 Regenerar',
        'back': '⬅️ Atrás',
        'all_decisions': '📋 Todas las decisiones',
        'all_tasks': '📌 Todas las tareas',
        'speakers': '👥 Posiciones',
        'quotes': '💬 Citas clave',
        'open_q': '❓ Preguntas abiertas',
        'recommendations': '💡 Recomendaciones',
        'enter_question': '✏️ **Escribe tu pregunta:**',
    },
    'zh': {
        'welcome': '👋 **Meeting Analyzer**\n\n发送会议音频或视频，获取详细分析和专家建议！\n\n🎤 **等待文件！**',
        'choose_lang': '🌍 **选择分析语言：**',
        'auto_lang': '🔄 自动（音频语言）',
        'downloading': '⏳ 下载文件中...',
        'transcribing': '🎤 转录音频中...',
        'analyzing': '🧠 分析内容中...',
        'done': '✅ 完成！',
        'error': '❌ 错误',
        'choose_action': '✨ **选择操作：**',
        'html_light': '🌐 HTML 浅色',
        'html_dark': '🌑 HTML 深色',
        'txt': '📄 TXT 文件',
        'deep_dive': '🔍 详细信息',
        'custom_q': '✏️ 提问',
        'transcript': '📜 转录文本',
        'regenerate': '🔄 重新生成',
        'back': '⬅️ 返回',
        'all_decisions': '📋 所有决定',
        'all_tasks': '📌 所有任务',
        'speakers': '👥 发言人立场',
        'quotes': '💬 关键引用',
        'open_q': '❓ 未决问题',
        'recommendations': '💡 建议',
        'enter_question': '✏️ **输入您的问题：**',
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

def t(uid, key):
    """Get translation for user"""
    cache = get_cache(uid)
    lang = cache.get('output_lang', 'ru')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ru']).get(key, TRANSLATIONS['ru'].get(key, key))

# ═══════════════════════════════════════════════════════════════
# HTML GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_html(content, theme="light", lang="ru"):
    
    dark_css = """
:root{--bg:#0f0f0f;--card:#1a1a2e;--card2:#16213e;--text:#e4e4e7;--text2:#a1a1aa;--accent:#3b82f6;--accent2:#8b5cf6;--success:#10b981;--border:#2d2d44}
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
.recommendation{background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(59,130,246,0.1));border:1px solid var(--success);border-radius:12px;padding:20px;margin:20px 0}
.recommendation h3{color:var(--success);border-color:var(--success)}
.action-plan{background:linear-gradient(135deg,rgba(59,130,246,0.1),rgba(139,92,246,0.1));border:1px solid var(--accent);border-radius:12px;padding:20px;margin:20px 0}
.stats{display:flex;gap:20px;flex-wrap:wrap;margin-top:30px;padding-top:20px;border-top:1px solid var(--border)}
.stat{background:var(--card);padding:15px 20px;border-radius:8px;text-align:center}
.stat-value{font-size:24px;font-weight:bold;color:var(--accent)}
.stat-label{font-size:12px;color:var(--text2);margin-top:5px}
"""

    light_css = """
:root{--bg:#f8fafc;--card:#fff;--card2:#f1f5f9;--text:#1e293b;--text2:#64748b;--accent:#3b82f6;--accent2:#8b5cf6;--success:#10b981;--border:#e2e8f0}
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
.recommendation{background:linear-gradient(135deg,rgba(16,185,129,0.08),rgba(59,130,246,0.08));border:1px solid var(--success);border-radius:12px;padding:20px;margin:20px 0}
.recommendation h3{color:var(--success);border-color:var(--success)}
.action-plan{background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(139,92,246,0.08));border:1px solid var(--accent);border-radius:12px;padding:20px;margin:20px 0}
.stats{display:flex;gap:20px;flex-wrap:wrap;margin-top:30px;padding-top:20px;border-top:1px solid var(--border)}
.stat{background:var(--card);padding:15px 20px;border-radius:8px;text-align:center;border:1px solid var(--border)}
.stat-value{font-size:24px;font-weight:bold;color:var(--accent)}
.stat-label{font-size:12px;color:var(--text2);margin-top:5px}
"""

    css = dark_css if theme == "dark" else light_css
    
    section_icons = {
        'Краткое саммари': '📋', 'Summary': '📋', 'Қысқаша': '📋', 'Resumen': '📋', '摘要': '📋',
        'Ключевые темы': '🎯', 'Key Topics': '🎯', 'Негізгі тақырыптар': '🎯', 'Temas clave': '🎯', '关键主题': '🎯',
        'Позиции участников': '👥', 'Participant Positions': '👥', 'Қатысушылар': '👥', 'Posiciones': '👥', '参与者立场': '👥',
        'Принятые решения': '✅', 'Decisions Made': '✅', 'Шешімдер': '✅', 'Decisiones': '✅', '决定': '✅',
        'Задачи': '📌', 'Tasks': '📌', 'Тапсырмалар': '📌', 'Tareas': '📌', '任务': '📌',
        'Открытые вопросы': '❓', 'Open Questions': '❓', 'Ашық сұрақтар': '❓', 'Preguntas': '❓', '未决问题': '❓',
        'Ключевые цитаты': '💬', 'Key Quotes': '💬', 'Дәйексөздер': '💬', 'Citas': '💬', '关键引用': '💬',
        'Рекомендации': '💡', 'Recommendations': '💡', 'Ұсыныстар': '💡', 'Recomendaciones': '💡', '建议': '💡',
        'План действий': '🚀', 'Action Plan': '🚀', 'Іс-қимыл жоспары': '🚀', 'Plan de acción': '🚀', '行动计划': '🚀',
        'Выводы': '🎯', 'Conclusions': '🎯', 'Қорытындылар': '🎯', 'Conclusiones': '🎯', '结论': '🎯',
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
            
            body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', body, flags=re.MULTILINE)
            body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body)
            body = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', body, flags=re.MULTILINE)
            body = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', body, flags=re.MULTILINE)
            body = re.sub(r'^- (.+)$', r'<li>\1</li>', body, flags=re.MULTILINE)
            body = re.sub(r'(<li>.*?</li>\n*)+', lambda m: f'<ul>{m.group(0)}</ul>', body, flags=re.DOTALL)
            body = re.sub(r'\n\n+', '</p><p>', body)
            body = f'<p>{body}</p>'
            body = body.replace('<p></p>', '').replace('<p><ul>', '<ul>').replace('</ul></p>', '</ul>')
            body = body.replace('<p><h3>', '<h3>').replace('</h3></p>', '</h3>')
            body = body.replace('<p><blockquote>', '<blockquote>').replace('</blockquote></p>', '</blockquote>')
            
            extra_class = ''
            if 'рекоменд' in title.lower() or 'recommend' in title.lower():
                extra_class = ' recommendation'
            elif 'план' in title.lower() or 'action' in title.lower():
                extra_class = ' action-plan'
            
            processed.append(f'<details><summary><span class="icon">{icon}</span> {title}</summary><div class="{extra_class}">{body}</div></details>')
    
    html_body = '\n'.join(processed)
    
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    lang_names = {'ru': 'Русский', 'en': 'English', 'kk': 'Қазақша', 'es': 'Español', 'zh': '中文'}
    theme_label = "Dark" if theme == "dark" else "Light"
    
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Analysis</title>
    <style>{css}</style>
</head>
<body>
    <div class="meta">📅 {date_str} &nbsp;|&nbsp; 🌍 {lang_names.get(lang, lang)} &nbsp;|&nbsp; 🎨 {theme_label}</div>
    {html_body}
    <script>
        document.querySelectorAll('details').forEach((d, i) => {{ if(i < 3) d.open = true; }});
    </script>
</body>
</html>'''

def save_html(content, theme, lang):
    html = generate_html(content, theme, lang)
    path = f"/tmp/meeting_{uuid.uuid4().hex[:8]}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return path

def save_txt(content):
    path = f"/tmp/meeting_{uuid.uuid4().hex[:8]}.txt"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    return path

# ═══════════════════════════════════════════════════════════════
# TRANSCRIPTION (Deepgram)
# ═══════════════════════════════════════════════════════════════

def transcribe_file(file_path, lang='ru'):
    try:
        dg_key = DEEPGRAM_KEY.strip() if DEEPGRAM_KEY else None
        if not dg_key:
            return None, "DEEPGRAM_API_KEY not set!"
        
        dg_lang = LANGUAGES.get(lang, {}).get('deepgram', 'ru')
        headers = {"Authorization": f"Token {dg_key}"}
        params = f"model=nova-2&language={dg_lang}&diarize=true&smart_format=true&utterances=true&punctuate=true"
        
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
        parts = []
        speakers = set()
        
        speaker_labels = {
            'ru': 'Спикер', 'en': 'Speaker', 'kk': 'Спикер',
            'es': 'Orador', 'zh': '发言人'
        }
        label = speaker_labels.get(lang, 'Speaker')
        
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
            "speakers": len(speakers) or 1
        }, None
        
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════════
# ANALYSIS (OpenAI GPT-4)
# ═══════════════════════════════════════════════════════════════

PROMPTS = {
    'ru': """Ты — профессиональный бизнес-аналитик и консультант с 20-летним опытом. Создай ДЕТАЛЬНЫЙ структурированный анализ встречи.

# 📊 Анализ встречи

## 📋 Краткое саммари
3-5 предложений: суть встречи, ключевой итог, важность.

## 🎯 Ключевые темы
Для КАЖДОЙ обсуждаемой темы создай подраздел:
### [Название темы]
- **Суть:** что обсуждали
- **Детали:** подробности дискуссии
- **Мнения:** разные точки зрения
- **Цитаты:** дословные высказывания
- **Итог:** к чему пришли

## 👥 Позиции участников
Для КАЖДОГО спикера:
### Спикер N
- **Основная позиция:** 
- **Ключевые аргументы:**
- **Цитаты:**
- **С кем соглашался/спорил:**

## ✅ Принятые решения
Пронумерованный список:
1. **[Решение]** — контекст, кто предложил

## 📌 Задачи и поручения
| Задача | Ответственный | Срок | Контекст |
Список всех задач с деталями.

## ❓ Открытые вопросы
Что требует дополнительного обсуждения или решения.

## 💬 Ключевые цитаты
Самые важные и показательные высказывания.

## 💡 Рекомендации эксперта
Как профессиональный консультант, дай 5-7 конкретных рекомендаций:
- Что улучшить в процессах
- На что обратить внимание
- Какие риски учесть
- Как повысить эффективность

## 🚀 План следующих действий
Конкретный пошаговый план на основе встречи:
1. **Немедленно (24-48 часов):** 
2. **Краткосрочно (неделя):**
3. **Среднесрочно (месяц):**

## 🎯 Главные выводы
Топ-5 ключевых выводов встречи.

ВАЖНО: Будь максимально подробным! Приводи много цитат!""",

    'en': """You are a professional business analyst and consultant with 20 years of experience. Create a DETAILED structured analysis of the meeting.

# 📊 Meeting Analysis

## 📋 Executive Summary
3-5 sentences: meeting essence, key outcome, importance.

## 🎯 Key Topics
For EACH discussed topic create a subsection:
### [Topic Name]
- **Essence:** what was discussed
- **Details:** discussion specifics
- **Opinions:** different viewpoints
- **Quotes:** verbatim statements
- **Outcome:** conclusion reached

## 👥 Participant Positions
For EACH speaker:
### Speaker N
- **Main position:**
- **Key arguments:**
- **Quotes:**
- **Agreed/disagreed with:**

## ✅ Decisions Made
Numbered list:
1. **[Decision]** — context, who proposed

## 📌 Tasks and Assignments
| Task | Responsible | Deadline | Context |
List all tasks with details.

## ❓ Open Questions
What requires additional discussion or decision.

## 💬 Key Quotes
Most important and revealing statements.

## 💡 Expert Recommendations
As a professional consultant, provide 5-7 specific recommendations:
- What to improve in processes
- What to pay attention to
- What risks to consider
- How to increase efficiency

## 🚀 Action Plan
Concrete step-by-step plan based on the meeting:
1. **Immediate (24-48 hours):**
2. **Short-term (week):**
3. **Medium-term (month):**

## 🎯 Key Conclusions
Top 5 key conclusions from the meeting.

IMPORTANT: Be as detailed as possible! Include many quotes!""",

    'kk': """Сіз 20 жылдық тәжірибесі бар кәсіби бизнес-талдаушы және кеңесшісіз. Кездесудің ТОЛЫҚ құрылымдалған талдауын жасаңыз.

# 📊 Кездесу талдауы

## 📋 Қысқаша түйін
3-5 сөйлем: кездесудің мәні, негізгі нәтиже.

## 🎯 Негізгі тақырыптар
Әр тақырып үшін бөлім жасаңыз.

## 👥 Қатысушылардың ұстанымдары
Әр спикер үшін толық сипаттама.

## ✅ Қабылданған шешімдер
Барлық шешімдердің тізімі.

## 📌 Тапсырмалар
Барлық тапсырмалар мен жауаптылар.

## ❓ Ашық сұрақтар
Шешілмеген мәселелер.

## 💬 Маңызды дәйексөздер
Ең маңызды айтылғандар.

## 💡 Сарапшы ұсыныстары
5-7 нақты ұсыныс.

## 🚀 Іс-қимыл жоспары
Қадамдық жоспар.

## 🎯 Негізгі қорытындылар
Топ-5 қорытынды.""",

    'es': """Eres un analista de negocios profesional y consultor con 20 años de experiencia. Crea un análisis DETALLADO y estructurado de la reunión.

# 📊 Análisis de la Reunión

## 📋 Resumen Ejecutivo
3-5 oraciones: esencia de la reunión, resultado clave.

## 🎯 Temas Clave
Para CADA tema discutido crea una subsección.

## 👥 Posiciones de los Participantes
Para CADA orador.

## ✅ Decisiones Tomadas
Lista numerada de todas las decisiones.

## 📌 Tareas y Asignaciones
Todas las tareas con responsables.

## ❓ Preguntas Abiertas
Qué requiere discusión adicional.

## 💬 Citas Clave
Declaraciones más importantes.

## 💡 Recomendaciones del Experto
5-7 recomendaciones específicas.

## 🚀 Plan de Acción
Plan paso a paso concreto.

## 🎯 Conclusiones Principales
Top 5 conclusiones clave.""",

    'zh': """您是一位拥有20年经验的专业商业分析师和顾问。创建会议的详细结构化分析。

# 📊 会议分析

## 📋 执行摘要
3-5句话：会议要点，关键成果。

## 🎯 关键主题
为每个讨论的主题创建子部分。

## 👥 参与者立场
每位发言人的详细描述。

## ✅ 做出的决定
所有决定的编号列表。

## 📌 任务和分配
所有任务及负责人。

## ❓ 未决问题
需要进一步讨论的内容。

## 💬 关键引用
最重要的声明。

## 💡 专家建议
5-7条具体建议。

## 🚀 行动计划
基于会议的具体步骤计划。

## 🎯 主要结论
前5个关键结论。"""
}

def analyze(transcript, duration, speakers, lang='ru'):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        prompt = PROMPTS.get(lang, PROMPTS['en'])
        
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Transcript:\n\n{transcript[:50000]}"}
            ],
            temperature=0.3,
            max_tokens=8000
        )
        
        result = resp.choices[0].message.content
        mins, secs = int(duration // 60), int(duration % 60)
        
        stats = {
            'ru': f"\n\n---\n**📊 Статистика:** {mins} мин {secs} сек | {speakers} спикер(ов) | {len(transcript.split())} слов",
            'en': f"\n\n---\n**📊 Statistics:** {mins} min {secs} sec | {speakers} speaker(s) | {len(transcript.split())} words",
            'kk': f"\n\n---\n**📊 Статистика:** {mins} мин {secs} сек | {speakers} спикер | {len(transcript.split())} сөз",
            'es': f"\n\n---\n**📊 Estadísticas:** {mins} min {secs} seg | {speakers} orador(es) | {len(transcript.split())} palabras",
            'zh': f"\n\n---\n**📊 统计:** {mins} 分 {secs} 秒 | {speakers} 位发言人 | {len(transcript.split())} 词"
        }
        
        return result + stats.get(lang, stats['en'])
        
    except Exception as e:
        return f"Analysis error: {e}"

def custom_analyze(transcript, criteria, lang='ru'):
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        
        system_prompts = {
            'ru': f"Ты — аналитик встреч. Извлеки информацию по запросу. Отвечай подробно на русском языке, приводи цитаты.\n\nЗапрос: {criteria}",
            'en': f"You are a meeting analyst. Extract information based on the request. Answer in detail in English, include quotes.\n\nRequest: {criteria}",
            'kk': f"Сіз кездесу талдаушысыз. Сұрау бойынша ақпаратты шығарыңыз. Қазақ тілінде толық жауап беріңіз.\n\nСұрау: {criteria}",
            'es': f"Eres un analista de reuniones. Extrae información según la solicitud. Responde en español con citas.\n\nSolicitud: {criteria}",
            'zh': f"您是会议分析师。根据请求提取信息。用中文详细回答，包含引用。\n\n请求: {criteria}"
        }
        
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompts.get(lang, system_prompts['en'])},
                {"role": "user", "content": f"Transcript:\n\n{transcript[:50000]}"}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ═══════════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════════

def lang_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Авто / Auto", callback_data="lang_auto")],
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

def help_kb(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💡 Help / Помощь", callback_data="help")],
        [InlineKeyboardButton("🎤 Formats / Форматы", callback_data="formats")]
    ])

# ═══════════════════════════════════════════════════════════════
# BOT HANDLERS
# ═══════════════════════════════════════════════════════════════

app = Client("meeting_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH or "", bot_token=BOT_TOKEN or "")

@app.on_message(filters.command("start"))
async def start_cmd(client, msg):
    uid = msg.from_user.id
    cache = get_cache(uid)
    cache['output_lang'] = 'ru'
    
    text = """👋 **Meeting Analyzer**

🌍 Multilingual meeting analysis bot

Send audio or video and get:
📝 Detailed summary
👥 Participant positions
✅ Decisions & tasks
💡 Expert recommendations
🚀 Action plan

🎤 **Send your file!**

---
🇷🇺 Русский | 🇬🇧 English | 🇰🇿 Қазақша | 🇪🇸 Español | 🇨🇳 中文"""
    
    await msg.reply(text, reply_markup=help_kb(uid))

@app.on_message(filters.audio | filters.video | filters.voice | filters.video_note | filters.document)
async def media_handler(client, msg):
    if msg.document:
        mime = msg.document.mime_type or ""
        if not any(t in mime for t in ["audio", "video", "octet"]):
            return
    
    uid = msg.from_user.id
    cache = get_cache(uid)
    cache['stage'] = 'waiting_lang'
    cache['file_msg'] = msg
    
    await msg.reply("🌍 **Choose analysis language:**\n\n**Выберите язык анализа:**", reply_markup=lang_kb())

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
            lang = data.replace("lang_", "")
            if lang == "auto":
                lang = "ru"
            cache['output_lang'] = lang
            cache['transcribe_lang'] = lang
            
            if 'file_msg' not in cache:
                await cb.answer("❌ Send file first!", show_alert=True)
                return
            
            msg = cache['file_msg']
            await cb.answer("⏳")
            await safe_edit(t(uid, 'downloading'))
            
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    path = await msg.download(file_name=f"{tmp}/media")
                    await safe_edit(t(uid, 'transcribing'))
                    
                    result, err = transcribe_file(path, lang)
                    if err:
                        await safe_edit(f"{t(uid, 'error')}: {err}")
                        return
                    
                    cache["transcript"] = result["transcript"]
                    cache["duration"] = result["duration"]
                    cache["speakers"] = result["speakers"]
                    
                    mins = int(result['duration'] // 60)
                    await safe_edit(f"✅ Transcribed!\n👥 {result['speakers']} speakers\n🕐 {mins} min\n\n{t(uid, 'analyzing')}")
                    
                    summary = analyze(result["transcript"], result["duration"], result["speakers"], lang)
                    cache["summary"] = summary
                    
                    try:
                        await cb.message.delete()
                    except:
                        pass
                    
                    preview = summary[:3500] + "\n\n_...see full in file_" if len(summary) > 3500 else summary
                    await msg.reply(f"📋 **Analysis:**\n\n{preview}")
                    await msg.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
                    
            except Exception as e:
                await safe_edit(f"{t(uid, 'error')}: {e}")
            return
        
        if data.startswith("html_"):
            parts = data.split("_")
            theme = parts[1]
            is_custom = len(parts) > 2 and parts[2] == "c"
            key = "custom_result" if is_custom else "summary"
            
            if key not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            
            await cb.answer("⏳")
            lang = cache.get('output_lang', 'ru')
            path = save_html(cache[key], theme, lang)
            await cb.message.reply_document(path, caption=f"📄 HTML ({theme}) | 💡 Click sections to expand!")
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        elif data == "txt":
            if "summary" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer("⏳")
            path = save_txt(cache["summary"])
            await cb.message.reply_document(path, caption="📄 TXT")
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        elif data == "deep_dive":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer()
            await safe_edit("🔍 **Choose topic:**", reply_markup=topics_kb(uid))
        
        elif data.startswith("topic_"):
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            
            topic = data.replace("topic_", "")
            lang = cache.get('output_lang', 'ru')
            
            prompts = {
                'decisions': {'ru': 'Перечисли ВСЕ принятые решения подробно', 'en': 'List ALL decisions made in detail'},
                'tasks': {'ru': 'Перечисли ВСЕ задачи с ответственными', 'en': 'List ALL tasks with assignees'},
                'speakers': {'ru': 'Опиши позицию КАЖДОГО спикера с цитатами', 'en': 'Describe EACH speaker position with quotes'},
                'quotes': {'ru': 'Выпиши ВСЕ ключевые цитаты', 'en': 'List ALL key quotes'},
                'open': {'ru': 'Перечисли ВСЕ открытые вопросы', 'en': 'List ALL open questions'},
                'recommendations': {'ru': 'Дай подробные экспертные рекомендации и план действий', 'en': 'Give detailed expert recommendations and action plan'}
            }
            
            prompt = prompts.get(topic, {}).get(lang, prompts.get(topic, {}).get('en', ''))
            
            await cb.answer("🧠")
            await safe_edit("🧠 Analyzing...")
            
            result = custom_analyze(cache["transcript"], prompt, lang)
            cache["custom_result"] = result
            
            await cb.message.reply(f"📋 **Result:**\n\n{result[:4000]}")
            if len(result) > 4000:
                await cb.message.reply(result[4000:8000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=continue_kb(uid))
        
        elif data == "custom":
            cache["stage"] = "waiting_criteria"
            await cb.answer()
            await safe_edit(t(uid, 'enter_question'))
        
        elif data == "transcript":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer()
            tr = cache["transcript"]
            await cb.message.reply("📜 **Transcript:**")
            for i in range(0, len(tr), 4000):
                await cb.message.reply(tr[i:i+4000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        elif data == "regenerate":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer("🔄")
            await safe_edit("🧠 Re-analyzing...")
            
            lang = cache.get('output_lang', 'ru')
            summary = analyze(cache["transcript"], cache.get("duration", 0), cache.get("speakers", 1), lang)
            cache["summary"] = summary
            
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await cb.message.reply(f"📋 **New analysis:**\n\n{preview}")
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        elif data == "back_main":
            await cb.answer()
            await safe_edit(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        elif data == "help":
            await cb.answer()
            await safe_edit("""💡 **How it works:**

1️⃣ Send audio/video file
2️⃣ Choose language
3️⃣ Wait for transcription
4️⃣ Get AI analysis
5️⃣ Download HTML/TXT
6️⃣ Ask follow-up questions!

📄 HTML has expandable sections!""", reply_markup=help_kb(uid))
        
        elif data == "formats":
            await cb.answer()
            await safe_edit("""🎤 **Supported formats:**

🎵 MP3, WAV, OGG, M4A, FLAC
🎬 MP4, MOV, AVI, MKV, WEBM
🎙 Telegram voice messages

📦 Up to 2GB (Premium 4GB)""", reply_markup=help_kb(uid))
    
    except Exception as e:
        await cb.message.reply(f"❌ Error: {e}")
            return
        
        # HTML export
        if data.startswith("html_"):
            parts = data.split("_")
            theme = parts[1]
            is_custom = len(parts) > 2 and parts[2] == "c"
            key = "custom_result" if is_custom else "summary"
            
            if key not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            
            await cb.answer("⏳")
            lang = cache.get('output_lang', 'ru')
            path = save_html(cache[key], theme, lang)
            await cb.message.reply_document(path, caption=f"📄 HTML ({theme}) | 💡 Click sections to expand!")
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        # TXT export
        elif data == "txt":
            if "summary" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer("⏳")
            path = save_txt(cache["summary"])
            await cb.message.reply_document(path, caption="📄 TXT")
            os.remove(path)
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        # Deep dive menu
        elif data == "deep_dive":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer()
            await cb.message.edit_text("🔍 **Choose topic:**", reply_markup=topics_kb(uid))
        
        # Topic analysis
        elif data.startswith("topic_"):
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            
            topic = data.replace("topic_", "")
            lang = cache.get('output_lang', 'ru')
            
            prompts = {
                'decisions': {'ru': 'Перечисли ВСЕ принятые решения подробно', 'en': 'List ALL decisions made in detail'},
                'tasks': {'ru': 'Перечисли ВСЕ задачи с ответственными', 'en': 'List ALL tasks with assignees'},
                'speakers': {'ru': 'Опиши позицию КАЖДОГО спикера с цитатами', 'en': 'Describe EACH speaker position with quotes'},
                'quotes': {'ru': 'Выпиши ВСЕ ключевые цитаты', 'en': 'List ALL key quotes'},
                'open': {'ru': 'Перечисли ВСЕ открытые вопросы', 'en': 'List ALL open questions'},
                'recommendations': {'ru': 'Дай подробные экспертные рекомендации и план действий', 'en': 'Give detailed expert recommendations and action plan'}
            }
            
            prompt = prompts.get(topic, {}).get(lang, prompts.get(topic, {}).get('en', ''))
            
            await cb.answer("🧠")
            await cb.message.edit_text("🧠 Analyzing...")
            
            result = custom_analyze(cache["transcript"], prompt, lang)
            cache["custom_result"] = result
            
            await cb.message.reply(f"📋 **Result:**\n\n{result[:4000]}")
            if len(result) > 4000:
                await cb.message.reply(result[4000:8000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=continue_kb(uid))
        
        # Custom question
        elif data == "custom":
            cache["stage"] = "waiting_criteria"
            await cb.answer()
            await cb.message.edit_text(t(uid, 'enter_question'))
        
        # Transcript
        elif data == "transcript":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer()
            tr = cache["transcript"]
            await cb.message.reply("📜 **Transcript:**")
            for i in range(0, len(tr), 4000):
                await cb.message.reply(tr[i:i+4000])
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        # Regenerate
        elif data == "regenerate":
            if "transcript" not in cache:
                await cb.answer("❌ No data!", show_alert=True)
                return
            await cb.answer("🔄")
            await cb.message.edit_text("🧠 Re-analyzing...")
            
            lang = cache.get('output_lang', 'ru')
            summary = analyze(cache["transcript"], cache.get("duration", 0), cache.get("speakers", 1), lang)
            cache["summary"] = summary
            
            preview = summary[:3500] + "..." if len(summary) > 3500 else summary
            await cb.message.reply(f"📋 **New analysis:**\n\n{preview}")
            await cb.message.reply(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        # Back to main menu
        elif data == "back_main":
            await cb.answer()
            await cb.message.edit_text(t(uid, 'choose_action'), reply_markup=main_kb(uid))
        
        # Help
        elif data == "help":
            await cb.answer()
            await cb.message.edit_text("""💡 **How it works:**

1️⃣ Send audio/video file
2️⃣ Choose language
3️⃣ Wait for transcription
4️⃣ Get AI analysis
5️⃣ Download HTML/TXT
6️⃣ Ask follow-up questions!

📄 HTML has expandable sections!""", reply_markup=help_kb(uid))
        
        # Formats
        elif data == "formats":
            await cb.answer()
            await cb.message.edit_text("""🎤 **Supported formats:**

🎵 MP3, WAV, OGG, M4A, FLAC
🎬 MP4, MOV, AVI, MKV, WEBM
🎙 Telegram voice messages

📦 Up to 2GB (Premium 4GB)""", reply_markup=help_kb(uid))
    
    except Exception as e:
        await cb.message.reply(f"❌ Error: {e}")

@app.on_message(filters.text & ~filters.command(["start"]))
async def text_handler(client, msg):
    uid = msg.from_user.id
    cache = get_cache(uid)
    
    if cache.get("stage") == "waiting_criteria" and "transcript" in cache:
        lang = cache.get('output_lang', 'ru')
        status = await msg.reply("🧠 Analyzing...")
        
        try:
            result = custom_analyze(cache["transcript"], msg.text, lang)
            cache["custom_result"] = result
            cache["stage"] = None
            await status.delete()
            
            if len(result) > 4000:
                await msg.reply(f"📋 **Result:**\n\n{result[:4000]}")
                await msg.reply(result[4000:8000])
            else:
                await msg.reply(f"📋 **Result:**\n\n{result}")
            
            await msg.reply(t(uid, 'choose_action'), reply_markup=continue_kb(uid))
            
        except Exception as e:
            await status.edit_text(f"❌ Error: {e}")
    else:
        await msg.reply("🎤 Send audio or video file!", reply_markup=help_kb(uid))

# ═══════════════════════════════════════════════════════════════
# START BOT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🚀 Starting Meeting Analyzer Bot...")
    print("📊 Languages: RU, EN, KK, ES, ZH")
    print("✨ Features: Analysis, Recommendations, Action Plans")
    app.run()
