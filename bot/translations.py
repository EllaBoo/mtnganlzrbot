"""
Translations for Digital Smarty
Полная мультиязычность — ВСЕ тексты на выбранном языке
"""

TRANSLATIONS = {
    "ru": {
        # Welcome & Commands
        "welcome": """👋 Привет! Я **Цифровой Умник** — твой AI-эксперт.

Отправь мне запись (аудио или видео), и я:
• 🎧 Расшифрую речь
• 🧠 Стану экспертом в теме обсуждения
• 🔍 Проведу глубокий профессиональный анализ
• 📄 Создам подробный PDF-отчёт
• 💬 Отвечу на любые вопросы по записи

Я адаптируюсь под тему: маркетинг, продажи, разработка, HR, финансы — что угодно! 🚀""",
        
        "choose_lang": "🌍 На каком языке подготовить анализ?",
        
        # Processing states
        "processing": "⏳ Начинаю обработку...",
        "transcribing": "🎧 Слушаю и расшифровываю речь...",
        "detecting_expertise": "🔍 Определяю тему и становлюсь экспертом...",
        "analyzing_as_expert": "🧠 Анализирую как {expert_role}...",
        "diagnosing": "🔬 Провожу экспертную диагностику...",
        "generating_pdf": "📄 Создаю PDF-отчёт...",
        
        # Results
        "done": "✅ Готово!",
        "analysis_complete": """✅ **Анализ завершён!**

📊 Эффективность: {score_emoji} **{score}/100**
📎 Тип: {meeting_type}
🎭 Анализировал как: {expert_role}
⏱️ {duration} • 👥 {speakers} спикер(ов)

{tip}""",
        
        # Buttons
        "ask_question": "❓ Задать вопрос эксперту",
        "get_transcript": "📜 Получить транскрипт",
        "deep_dive": "🔍 Deep Dive",
        "new_analysis": "🔄 Новый анализ",
        "back": "◀️ Назад",
        
        # Question mode
        "question_prompt": "💬 Задай свой вопрос — отвечу как {expert_role}:",
        "thinking": "🤔 Думаю как {expert_role}...",
        
        # Errors
        "no_data": "❌ Сначала отправь запись для анализа",
        "error": "❌ Произошла ошибка: {error}",
        "file_too_large": "❌ Файл слишком большой. Максимум 100 МБ.",
        "unsupported_format": "❌ Неподдерживаемый формат. Отправь аудио или видео.",
        
        # Expert tip intro
        "expert_tip_intro": "💡 **Совет от {expert_role}:**",
    },
    
    "en": {
        "welcome": """👋 Hi! I'm **Digital Smarty** — your AI expert.

Send me a recording (audio or video), and I will:
• 🎧 Transcribe speech
• 🧠 Become an expert in the topic discussed
• 🔍 Conduct deep professional analysis
• 📄 Create detailed PDF report
• 💬 Answer any questions about the recording

I adapt to any topic: marketing, sales, development, HR, finance — anything! 🚀""",
        
        "choose_lang": "🌍 What language should I use for analysis?",
        
        "processing": "⏳ Starting processing...",
        "transcribing": "🎧 Listening and transcribing...",
        "detecting_expertise": "🔍 Detecting topic and becoming an expert...",
        "analyzing_as_expert": "🧠 Analyzing as {expert_role}...",
        "diagnosing": "🔬 Conducting expert diagnostics...",
        "generating_pdf": "📄 Generating PDF report...",
        
        "done": "✅ Done!",
        "analysis_complete": """✅ **Analysis complete!**

📊 Effectiveness: {score_emoji} **{score}/100**
📎 Type: {meeting_type}
🎭 Analyzed as: {expert_role}
⏱️ {duration} • 👥 {speakers} speaker(s)

{tip}""",
        
        "ask_question": "❓ Ask the expert",
        "get_transcript": "📜 Get transcript",
        "deep_dive": "🔍 Deep Dive",
        "new_analysis": "🔄 New analysis",
        "back": "◀️ Back",
        
        "question_prompt": "💬 Ask your question — I'll answer as {expert_role}:",
        "thinking": "🤔 Thinking as {expert_role}...",
        
        "no_data": "❌ Send a recording first",
        "error": "❌ Error occurred: {error}",
        "file_too_large": "❌ File too large. Maximum 100 MB.",
        "unsupported_format": "❌ Unsupported format. Send audio or video.",
        
        "expert_tip_intro": "💡 **Tip from {expert_role}:**",
    },
    
    "kk": {
        "welcome": """👋 Сәлем! Мен **Цифрлық Данышпан** — сенің AI-сарапшың.

Маған жазба жібер (аудио немесе видео), мен:
• 🎧 Сөзді жазып аламын
• 🧠 Талқыланатын тақырып бойынша сарапшы боламын
• 🔍 Терең кәсіби талдау жүргіземін
• 📄 Толық PDF-есеп жасаймын
• 💬 Жазба бойынша кез келген сұраққа жауап беремін

Мен кез келген тақырыпқа бейімделемін! 🚀""",
        
        "choose_lang": "🌍 Талдауды қай тілде дайындау керек?",
        
        "processing": "⏳ Өңдеуді бастаймын...",
        "transcribing": "🎧 Тыңдап, жазып жатырмын...",
        "detecting_expertise": "🔍 Тақырыпты анықтап, сарапшы болып жатырмын...",
        "analyzing_as_expert": "🧠 {expert_role} ретінде талдаймын...",
        "diagnosing": "🔬 Сараптамалық диагностика жүргізіп жатырмын...",
        "generating_pdf": "📄 PDF-есеп жасап жатырмын...",
        
        "done": "✅ Дайын!",
        "analysis_complete": """✅ **Талдау аяқталды!**

📊 Тиімділік: {score_emoji} **{score}/100**
📎 Түрі: {meeting_type}
🎭 {expert_role} ретінде талданды
⏱️ {duration} • 👥 {speakers} спикер

{tip}""",
        
        "ask_question": "❓ Сарапшыға сұрақ қою",
        "get_transcript": "📜 Транскрипт алу",
        "back": "◀️ Артқа",
        
        "question_prompt": "💬 Сұрағыңды жаз — {expert_role} ретінде жауап беремін:",
        "thinking": "🤔 {expert_role} ретінде ойланамын...",
        
        "no_data": "❌ Алдымен жазба жібер",
        "error": "❌ Қате орын алды: {error}",
        "file_too_large": "❌ Файл тым үлкен. Максимум 100 МБ.",
        "unsupported_format": "❌ Қолдау көрсетілмейтін формат.",
        
        "expert_tip_intro": "💡 **{expert_role} кеңесі:**",
    },
    
    "es": {
        "welcome": """👋 ¡Hola! Soy **Digital Smarty** — tu experto IA.

Envíame una grabación (audio o video), y yo:
• 🎧 Transcribiré el discurso
• 🧠 Me convertiré en experto en el tema discutido
• 🔍 Realizaré un análisis profesional profundo
• 📄 Crearé un informe PDF detallado
• 💬 Responderé cualquier pregunta sobre la grabación

¡Me adapto a cualquier tema: marketing, ventas, desarrollo, RRHH, finanzas — lo que sea! 🚀""",
        
        "choose_lang": "🌍 ¿En qué idioma preparo el análisis?",
        
        "processing": "⏳ Iniciando procesamiento...",
        "transcribing": "🎧 Escuchando y transcribiendo...",
        "detecting_expertise": "🔍 Detectando tema y convirtiéndome en experto...",
        "analyzing_as_expert": "🧠 Analizando como {expert_role}...",
        "diagnosing": "🔬 Realizando diagnóstico experto...",
        "generating_pdf": "📄 Generando informe PDF...",
        
        "done": "✅ ¡Listo!",
        "analysis_complete": """✅ **¡Análisis completado!**

📊 Efectividad: {score_emoji} **{score}/100**
📎 Tipo: {meeting_type}
🎭 Analizado como: {expert_role}
⏱️ {duration} • 👥 {speakers} participante(s)

{tip}""",
        
        "ask_question": "❓ Preguntar al experto",
        "get_transcript": "📜 Obtener transcripción",
        "back": "◀️ Atrás",
        
        "question_prompt": "💬 Haz tu pregunta — responderé como {expert_role}:",
        "thinking": "🤔 Pensando como {expert_role}...",
        
        "no_data": "❌ Primero envía una grabación",
        "error": "❌ Ocurrió un error: {error}",
        "file_too_large": "❌ Archivo demasiado grande. Máximo 100 MB.",
        "unsupported_format": "❌ Formato no soportado. Envía audio o video.",
        
        "expert_tip_intro": "💡 **Consejo de {expert_role}:**",
    },
    
    "zh": {
        "welcome": """👋 你好！我是 **数字智者** — 你的AI专家。

发送录音（音频或视频），我会：
• 🎧 转录语音
• 🧠 成为讨论主题的专家
• 🔍 进行深入专业分析
• 📄 创建详细的PDF报告
• 💬 回答关于录音的任何问题

我能适应任何主题：营销、销售、开发、人力资源、财务——任何领域！🚀""",
        
        "choose_lang": "🌍 用什么语言准备分析？",
        
        "processing": "⏳ 开始处理...",
        "transcribing": "🎧 正在听取和转录...",
        "detecting_expertise": "🔍 正在检测主题并成为专家...",
        "analyzing_as_expert": "🧠 作为{expert_role}进行分析...",
        "diagnosing": "🔬 正在进行专家诊断...",
        "generating_pdf": "📄 正在生成PDF报告...",
        
        "done": "✅ 完成！",
        "analysis_complete": """✅ **分析完成！**

📊 有效性: {score_emoji} **{score}/100**
📎 类型: {meeting_type}
🎭 分析身份: {expert_role}
⏱️ {duration} • 👥 {speakers} 位发言者

{tip}""",
        
        "ask_question": "❓ 向专家提问",
        "get_transcript": "📜 获取转录",
        "back": "◀️ 返回",
        
        "question_prompt": "💬 提出你的问题 — 我将作为{expert_role}回答：",
        "thinking": "🤔 作为{expert_role}思考中...",
        
        "no_data": "❌ 请先发送录音",
        "error": "❌ 发生错误: {error}",
        "file_too_large": "❌ 文件太大。最大100 MB。",
        "unsupported_format": "❌ 不支持的格式。请发送音频或视频。",
        
        "expert_tip_intro": "💡 **{expert_role}的建议：**",
    },
}

# User language preferences storage
user_languages = {}


def t(user_id: int, key: str, **kwargs) -> str:
    """Get translation for user with formatting"""
    lang = user_languages.get(user_id, "ru")
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])
    text = translations.get(key, TRANSLATIONS["ru"].get(key, key))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def set_user_lang(user_id: int, lang: str):
    """Set user language preference"""
    if lang == "auto":
        lang = "ru"  # Default for auto
    user_languages[user_id] = lang


def get_user_lang(user_id: int) -> str:
    """Get user language preference"""
    return user_languages.get(user_id, "ru")


# Language names for prompts (how to tell GPT which language to use)
LANG_NAMES = {
    "ru": "русский",
    "en": "English",
    "kk": "қазақ тілі",
    "es": "español", 
    "zh": "中文",
    "auto": "русский"
}


def get_lang_name(lang_code: str) -> str:
    """Get full language name for prompts"""
    return LANG_NAMES.get(lang_code, "русский")
