"""
Report Generator — PDF + HTML for Цифровой Умник
Generates professional meeting analysis reports in two formats.
"""
import json
import logging
import os
import tempfile
from datetime import datetime

logger = logging.getLogger("report")


def generate_html_report(analysis: dict, lang: str = "ru") -> str:
    """Generate interactive HTML with collapsible sections."""
    title = analysis.get("title", "Анализ встречи")
    now = datetime.now().strftime("%d.%m.%Y в %H:%M")
    summary = analysis.get("executive_summary", "")
    ctx = analysis.get("context", {})
    goals = analysis.get("goals", {})
    topics = analysis.get("key_topics", [])
    decisions = analysis.get("decisions", [])
    action_items = analysis.get("action_items", [])
    recommendations = analysis.get("recommendations", {})
    open_questions = analysis.get("open_questions", [])
    swot = analysis.get("swot", {})
    risks = analysis.get("risks", [])
    action_plan = analysis.get("action_plan", {})
    kpi = analysis.get("kpi", [])
    hidden_dynamics = analysis.get("hidden_dynamics", [])
    conclusion = analysis.get("conclusion", {})
    positions = analysis.get("positions", {})
    agreement = analysis.get("agreement_points", [])
    disagreement = analysis.get("disagreement_points", [])
    labels = _get_labels(lang)

    def make_list(items):
        if not items:
            return "<p style='color:#888;'>—</p>"
        return "".join(f"<li>{_esc(item)}</li>" for item in items)

    def make_section(id_, icon, title, content, rec=None):
        rec_html = ""
        if rec:
            rec_html = f'<div class="rec-box"><div class="rec-label">💡 {labels["smarty_rec"]}</div><p>{_esc(rec)}</p></div>'
        return f'<div class="section" id="sec-{id_}"><div class="section-header" onclick="toggle(\'{id_}\')"><span>{icon} {title}</span><span class="chevron" id="chev-{id_}">▶</span></div><div class="section-body" id="body-{id_}" style="display:none;">{content}{rec_html}</div></div>'

    sections = []
    sections.append(f'<div class="section"><div class="section-header open"><span>📋 {labels["summary"]}</span></div><div class="section-body" style="display:block;"><p>{_esc(summary)}</p></div></div>')

    ctx_html = f'<table class="info-table"><tr><td class="label">{labels["industry"]}</td><td>{_esc(ctx.get("industry","—"))}</td></tr><tr><td class="label">{labels["meeting_type"]}</td><td>{_esc(ctx.get("meeting_type","—"))}</td></tr><tr><td class="label">{labels["complexity"]}</td><td>{_esc(ctx.get("complexity","—"))}</td></tr></table>'
    sections.append(make_section("ctx", "🏢", labels["context"], ctx_html))

    goals_html = f'<h4>{labels["explicit_goals"]}</h4><ul>{make_list(goals.get("explicit",[]))}</ul><h4>{labels["hidden_goals"]}</h4><ul>{make_list(goals.get("hidden",[]))}</ul>'
    sections.append(make_section("goals", "🎯", labels["goals"], goals_html))

    topics_html = "<ol>" + "".join(f'<li><strong>{_esc(t.get("topic",t) if isinstance(t,dict) else t)}</strong>' + (f'<p>{_esc(t.get("details",""))}</p>' if isinstance(t,dict) and t.get("details") else "") + '</li>' for t in topics) + "</ol>"
    sections.append(make_section("topics", "📑", labels["topics"], topics_html))

    if positions:
        pos_html = ""
        for sk in ["side_a","side_b"]:
            s = positions.get(sk,{})
            if s:
                lb = s.get("label",sk.replace("_"," ").title())
                pos_html += f'<div class="position-box"><h4>{_esc(lb)}</h4><p><strong>{labels["position"]}:</strong> {_esc(s.get("position","—"))}</p><p><strong>{labels["interests"]}:</strong> {_esc(s.get("interests","—"))}</p></div>'
        sections.append(make_section("pos", "⚖️", labels["positions"], pos_html))

    agree_html = f'<h4>✅ {labels["agreement"]}</h4><ul>{make_list(agreement)}</ul><h4>❌ {labels["disagreement"]}</h4><ul>{make_list(disagreement)}</ul>'
    sections.append(make_section("agree", "🤝", labels["consensus"], agree_html))

    sections.append(make_section("dec", "📌", labels["decisions"], f'<ul>{make_list(decisions)}</ul>'))

    ai_html = f'<table class="ai-table"><tr><th>{labels["task"]}</th><th>{labels["responsible"]}</th><th>{labels["deadline"]}</th></tr>'
    for item in action_items:
        if isinstance(item, dict):
            ai_html += f'<tr><td>{_esc(item.get("task",""))}</td><td>{_esc(item.get("responsible","—"))}</td><td>{_esc(item.get("deadline","—"))}</td></tr>'
        else:
            ai_html += f'<tr><td colspan="3">{_esc(item)}</td></tr>'
    ai_html += "</table>"
    sections.append(make_section("ai", "✅", labels["action_items"], ai_html))

    swot_html = '<div class="swot-grid">'
    for key, (icon, label) in {"strengths":("💪",labels.get("strengths","S")),"weaknesses":("⚠️",labels.get("weaknesses","W")),"opportunities":("🚀",labels.get("opportunities","O")),"threats":("🔥",labels.get("threats","T"))}.items():
        swot_html += f'<div class="swot-cell swot-{key}"><h4>{icon} {label}</h4><ul>{make_list(swot.get(key,[]))}</ul></div>'
    swot_html += "</div>"
    sections.append(make_section("swot", "📊", "SWOT", swot_html))

    rec_html = f'<h4>💡 {labels["rec_substance"]}</h4><ul>{make_list(recommendations.get("substance",[]))}</ul><h4>🛠 {labels["rec_method"]}</h4><ul>{make_list(recommendations.get("methodology",[]))}</ul>'
    sections.append(make_section("rec", "💡", labels["recommendations"], rec_html))

    risk_html = f'<table class="ai-table"><tr><th>{labels["risk"]}</th><th>{labels["severity"]}</th><th>{labels["mitigation"]}</th></tr>'
    for r in risks:
        if isinstance(r,dict):
            risk_html += f'<tr><td>{_esc(r.get("risk",""))}</td><td>{_esc(r.get("severity",""))}</td><td>{_esc(r.get("mitigation",""))}</td></tr>'
    risk_html += "</table>"
    sections.append(make_section("risks", "⚡", labels["risks_title"], risk_html))

    sections.append(make_section("oq", "❓", labels["open_questions"], f'<ul>{make_list(open_questions)}</ul>'))

    plan_html = ""
    for pk, pl in [("urgent",labels["urgent"]),("medium",labels["medium"]),("long_term",labels["long_term"])]:
        items = action_plan.get(pk,[])
        if items:
            plan_html += f'<h4>⏰ {pl}</h4><ul>{make_list(items)}</ul>'
    if kpi:
        plan_html += f'<h4>📈 KPI</h4><ul>{make_list(kpi)}</ul>'
    sections.append(make_section("plan", "🗓", labels["action_plan"], plan_html))

    if hidden_dynamics:
        sections.append(make_section("hd", "🔍", labels["hidden_dynamics"], f'<ul>{make_list(hidden_dynamics)}</ul>'))

    concl_html = f'<div class="conclusion-box"><h4>🎯 {labels["main_insight"]}</h4><p>{_esc(conclusion.get("main_insight",""))}</p><h4>💡 {labels["key_rec"]}</h4><p>{_esc(conclusion.get("key_recommendation",""))}</p><h4>🔮 {labels["forecast"]}</h4><p>{_esc(conclusion.get("forecast",""))}</p></div>'
    sections.append(make_section("concl", "🏁", labels["conclusion"], concl_html))

    all_sections = "\n".join(sections)
    html = f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>{_esc(title)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f7fa;color:#2d3748;line-height:1.6}}.container{{max-width:800px;margin:0 auto;padding:20px}}.header{{background:linear-gradient(135deg,#1a365d 0%,#2b6cb0 100%);color:#fff;padding:30px;border-radius:16px;margin-bottom:20px}}.header h1{{font-size:1.5em;margin-bottom:4px}}.header .subtitle{{font-size:.9em;opacity:.85}}.header .meta{{font-size:.8em;opacity:.7;margin-top:8px}}.section{{background:#fff;border-radius:12px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden}}.section-header{{padding:16px 20px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-weight:600;font-size:1.05em;transition:background .2s}}.section-header:hover{{background:#f7fafc}}.section-header.open{{background:#ebf8ff}}.chevron{{font-size:.8em;transition:transform .3s;color:#a0aec0}}.chevron.open{{transform:rotate(90deg)}}.section-body{{padding:0 20px 16px 20px}}.section-body h4{{color:#2b6cb0;margin:12px 0 6px 0;font-size:.95em}}.section-body ul{{padding-left:20px}}.section-body li{{margin-bottom:6px}}.section-body p{{margin:8px 0}}.info-table{{width:100%}}.info-table td{{padding:6px 0}}.info-table .label{{color:#718096;width:40%;font-weight:500}}.ai-table{{width:100%;border-collapse:collapse;margin:8px 0}}.ai-table th{{background:#edf2f7;padding:8px 12px;text-align:left;font-size:.9em}}.ai-table td{{padding:8px 12px;border-bottom:1px solid #edf2f7;font-size:.9em}}.rec-box{{background:#fffff0;border-left:4px solid #ecc94b;padding:12px 16px;margin-top:12px;border-radius:0 8px 8px 0}}.rec-label{{font-weight:600;color:#b7791f;margin-bottom:4px;font-size:.9em}}.conclusion-box{{background:#ebf8ff;padding:16px;border-radius:8px}}.position-box{{background:#f7fafc;padding:12px;border-radius:8px;margin:8px 0}}.swot-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0}}.swot-cell{{padding:12px;border-radius:8px}}.swot-strengths{{background:#f0fff4}}.swot-weaknesses{{background:#fff5f5}}.swot-opportunities{{background:#ebf8ff}}.swot-threats{{background:#fffff0}}.swot-cell h4{{font-size:.9em;margin-bottom:6px}}.swot-cell ul{{font-size:.9em}}.footer{{text-align:center;padding:20px;color:#a0aec0;font-size:.8em}}.badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.75em;font-weight:600}}.badge-fact{{background:#ebf8ff;color:#2b6cb0}}.badge-rec{{background:#fffff0;color:#b7791f}}@media(max-width:600px){{.swot-grid{{grid-template-columns:1fr}}.container{{padding:10px}}.header{{padding:20px}}}}
</style></head><body>
<div class="container">
<div class="header"><h1>🧠 {_esc(title)}</h1><div class="subtitle">{labels['report_by']}</div><div class="meta">{now}</div></div>
{all_sections}
<div class="footer"><span class="badge badge-fact">{labels['facts_badge']}</span> <span class="badge badge-rec">{labels['rec_badge']}</span><br><br>🧠 Цифровой Умник • {now}</div>
</div>
<script>function toggle(id){{const b=document.getElementById('body-'+id);const c=document.getElementById('chev-'+id);if(b.style.display==='none'){{b.style.display='block';c.classList.add('open')}}else{{b.style.display='none';c.classList.remove('open')}}}}</script>
</body></html>"""
    return html


def generate_pdf_report(analysis: dict, lang: str = "ru") -> str:
    """Generate PDF report, return path to temp file."""
    from fpdf import FPDF
    title = analysis.get("title", "Анализ встречи")
    now = datetime.now().strftime("%d.%m.%Y в %H:%M")
    labels = _get_labels(lang)

    class MeetingPDF(FPDF):
        def __init__(self):
            super().__init__()
            fps = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
            if all(os.path.exists(p) for p in fps):
                self.add_font("DejaVu","",fps[0])
                self.add_font("DejaVu","B",fps[1])
                self.font_name="DejaVu"
            else:
                self.font_name="Helvetica"
            self.set_auto_page_break(auto=True,margin=20)
        def header(self):
            self.set_fill_color(26,54,93)
            self.rect(0,0,210,35,'F')
            self.set_font(self.font_name,"B",14)
            self.set_text_color(255,255,255)
            self.set_y(8)
            self.cell(0,8,labels['report_by'],ln=True,align="C")
            self.set_font(self.font_name,"",9)
            self.cell(0,6,now,ln=True,align="C")
            self.set_text_color(0,0,0)
            self.ln(10)
        def footer(self):
            self.set_y(-15)
            self.set_font(self.font_name,"",8)
            self.set_text_color(150,150,150)
            self.cell(0,10,f"Цифровой Умник - {now} - {self.page_no()}",align="C")
        def sec_title(self,num,icon,text):
            self.set_font(self.font_name,"B",12)
            self.set_text_color(43,108,176)
            self.ln(4)
            self.cell(0,8,f"  {icon} {num}. {text}",ln=True)
            self.set_draw_color(43,108,176)
            self.line(10,self.get_y(),200,self.get_y())
            self.ln(2)
            self.set_text_color(0,0,0)
        def body_text(self,text):
            self.set_font(self.font_name,"",10)
            self.multi_cell(0,6,text)
            self.ln(2)
        def bullet(self,text):
            self.set_font(self.font_name,"",10)
            self.cell(8,6,"  *")
            self.multi_cell(0,6,text)

    pdf = MeetingPDF()
    pdf.add_page()
    pdf.set_font(pdf.font_name,"B",16)
    pdf.cell(0,10,title,ln=True,align="C")
    pdf.ln(4)

    pdf.sec_title(1,"",labels["summary"].upper())
    pdf.body_text(analysis.get("executive_summary","—"))

    ctx=analysis.get("context",{})
    pdf.sec_title(2,"",labels["context"].upper())
    for k,lb in [("industry",labels["industry"]),("meeting_type",labels["meeting_type"]),("complexity",labels["complexity"])]:
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(60,6,f"  {lb}:")
        pdf.set_font(pdf.font_name,"",10)
        pdf.cell(0,6,ctx.get(k,"—"),ln=True)

    goals=analysis.get("goals",{})
    pdf.sec_title(3,"",labels["goals"].upper())
    pdf.set_font(pdf.font_name,"B",10)
    pdf.cell(0,6,f"  {labels['explicit_goals']}:",ln=True)
    for g in goals.get("explicit",[]):
        pdf.bullet(g)
    pdf.set_font(pdf.font_name,"B",10)
    pdf.cell(0,6,f"  {labels['hidden_goals']}:",ln=True)
    for g in goals.get("hidden",[]):
        pdf.bullet(g)

    topics=analysis.get("key_topics",[])
    pdf.sec_title(4,"",labels["topics"].upper())
    for i,t in enumerate(topics,1):
        tt=t.get("topic",t) if isinstance(t,dict) else str(t)
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,f"  {i}. {tt}",ln=True)
        if isinstance(t,dict) and t.get("details"):
            pdf.set_font(pdf.font_name,"",9)
            pdf.multi_cell(0,5,f"     {t['details']}")

    pos=analysis.get("positions",{})
    if pos:
        pdf.sec_title(5,"",labels["positions"].upper())
        for sk in ["side_a","side_b"]:
            s=pos.get(sk,{})
            if s:
                pdf.set_font(pdf.font_name,"B",10)
                pdf.cell(0,6,f"  {s.get('label',sk)}:",ln=True)
                pdf.body_text(f"    {labels['position']}: {s.get('position','—')}")
                pdf.body_text(f"    {labels['interests']}: {s.get('interests','—')}")

    pdf.sec_title(6,"",labels["consensus"].upper())
    pdf.set_font(pdf.font_name,"B",10)
    pdf.cell(0,6,f"  {labels['agreement']}:",ln=True)
    for a in analysis.get("agreement_points",[]):
        pdf.bullet(a)
    pdf.set_font(pdf.font_name,"B",10)
    pdf.cell(0,6,f"  {labels['disagreement']}:",ln=True)
    for d in analysis.get("disagreement_points",[]):
        pdf.bullet(d)

    pdf.sec_title(7,"",labels["decisions"].upper())
    for d in analysis.get("decisions",[]):
        pdf.bullet(d)

    ais=analysis.get("action_items",[])
    pdf.sec_title(8,"",labels["action_items"].upper())
    for item in ais:
        if isinstance(item,dict):
            pdf.bullet(f"{item.get('task','')} | {item.get('deadline','—')} | {item.get('responsible','—')}")
        else:
            pdf.bullet(str(item))

    swot=analysis.get("swot",{})
    pdf.sec_title(9,"","SWOT")
    for k,(ic,lb) in [("strengths",("S",labels.get("strengths","S"))),("weaknesses",("W",labels.get("weaknesses","W"))),("opportunities",("O",labels.get("opportunities","O"))),("threats",("T",labels.get("threats","T")))]:
        items=swot.get(k,[])
        if items:
            pdf.set_font(pdf.font_name,"B",10)
            pdf.cell(0,6,f"  {lb}:",ln=True)
            for item in items:
                pdf.bullet(item)

    recs=analysis.get("recommendations",{})
    pdf.sec_title(10,"",labels["recommendations"].upper())
    for r in recs.get("substance",[]):
        pdf.bullet(r)
    if recs.get("methodology"):
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,f"  {labels['rec_method']}:",ln=True)
        for r in recs.get("methodology",[]):
            pdf.bullet(r)

    risks=analysis.get("risks",[])
    pdf.sec_title(11,"",labels["risks_title"].upper())
    for r in risks:
        if isinstance(r,dict):
            pdf.bullet(f"{r.get('risk','')} | {r.get('severity','')} | {r.get('mitigation','')}")

    pdf.sec_title(12,"",labels["open_questions"].upper())
    for q in analysis.get("open_questions",[]):
        pdf.bullet(q)

    ap=analysis.get("action_plan",{})
    pdf.sec_title(13,"",labels["action_plan"].upper())
    for pk,pl in [("urgent",labels["urgent"]),("medium",labels["medium"]),("long_term",labels["long_term"])]:
        items=ap.get(pk,[])
        if items:
            pdf.set_font(pdf.font_name,"B",10)
            pdf.cell(0,6,f"  {pl}:",ln=True)
            for item in items:
                pdf.bullet(item)
    kpi=analysis.get("kpi",[])
    if kpi:
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,"  KPI:",ln=True)
        for k in kpi:
            pdf.bullet(k)

    hd=analysis.get("hidden_dynamics",[])
    if hd:
        pdf.sec_title(14,"",labels["hidden_dynamics"].upper())
        for h in hd:
            pdf.bullet(h)

    concl=analysis.get("conclusion",{})
    pdf.sec_title(15,"",labels["conclusion"].upper())
    if concl.get("main_insight"):
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,f"  {labels['main_insight']}:",ln=True)
        pdf.body_text(f"    {concl['main_insight']}")
    if concl.get("key_recommendation"):
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,f"  {labels['key_rec']}:",ln=True)
        pdf.body_text(f"    {concl['key_recommendation']}")
    if concl.get("forecast"):
        pdf.set_font(pdf.font_name,"B",10)
        pdf.cell(0,6,f"  {labels['forecast']}:",ln=True)
        pdf.body_text(f"    {concl['forecast']}")

    tmp=tempfile.mktemp(suffix=".pdf")
    pdf.output(tmp)
    return tmp


def _esc(text):
    if not text:
        return ""
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def _get_labels(lang: str) -> dict:
    labels = {
        "ru": {"report_by":"Экспертный отчёт от Цифрового Умника","summary":"Краткое содержание","context":"Контекст и область","industry":"Сфера/индустрия","meeting_type":"Тип встречи","complexity":"Уровень сложности","goals":"Цели встречи","explicit_goals":"Явные цели","hidden_goals":"Скрытые цели","topics":"Ключевые темы","positions":"Выявленные позиции","position":"Позиция","interests":"Истинные интересы","consensus":"Точки согласия и расхождения","agreement":"Точки согласия","disagreement":"Точки расхождения","decisions":"Принятые решения","action_items":"Задачи (Action Items)","task":"Задача","responsible":"Ответственный","deadline":"Срок","recommendations":"Рекомендации","rec_substance":"По существу","rec_method":"Инструменты и методологии","smarty_rec":"Рекомендация от Цифрового Умника","risks_title":"Риски","risk":"Риск","severity":"Вероятность","mitigation":"Митигация","open_questions":"Открытые вопросы","action_plan":"План действий","urgent":"Срочно (1-7 дней)","medium":"Среднесрок (1-4 недели)","long_term":"Долгосрок (1-3 месяца)","hidden_dynamics":"Скрытая динамика","conclusion":"Заключение Цифрового Умника","main_insight":"Главный инсайт","key_rec":"Ключевая рекомендация","forecast":"Прогноз","facts_badge":"Факты из встречи","rec_badge":"Рекомендации Умника","strengths":"Сильные стороны","weaknesses":"Слабые стороны","opportunities":"Возможности","threats":"Угрозы"},
        "en": {"report_by":"Expert Report by Digital Smarty","summary":"Executive Summary","context":"Context & Scope","industry":"Industry","meeting_type":"Meeting Type","complexity":"Complexity","goals":"Meeting Goals","explicit_goals":"Explicit Goals","hidden_goals":"Hidden Goals","topics":"Key Topics","positions":"Identified Positions","position":"Position","interests":"True Interests","consensus":"Agreement & Disagreement","agreement":"Agreement Points","disagreement":"Disagreement Points","decisions":"Decisions Made","action_items":"Action Items","task":"Task","responsible":"Owner","deadline":"Deadline","recommendations":"Recommendations","rec_substance":"Substantive","rec_method":"Tools & Methodologies","smarty_rec":"Digital Smarty's Recommendation","risks_title":"Risks","risk":"Risk","severity":"Severity","mitigation":"Mitigation","open_questions":"Open Questions","action_plan":"Action Plan","urgent":"Urgent (1-7 days)","medium":"Medium-term (1-4 weeks)","long_term":"Long-term (1-3 months)","hidden_dynamics":"Hidden Dynamics","conclusion":"Digital Smarty's Conclusion","main_insight":"Key Insight","key_rec":"Key Recommendation","forecast":"Forecast","facts_badge":"Meeting Facts","rec_badge":"Smarty's Recommendations","strengths":"Strengths","weaknesses":"Weaknesses","opportunities":"Opportunities","threats":"Threats"},
        "kk": {"report_by":"Цифрлық Зерек сарапшылық есебі","summary":"Қысқаша мазмұны","context":"Контекст және аумақ","industry":"Сала","meeting_type":"Кездесу түрі","complexity":"Күрделілік деңгейі","goals":"Кездесу мақсаттары","explicit_goals":"Айқын мақсаттар","hidden_goals":"Жасырын мақсаттар","topics":"Негізгі тақырыптар","positions":"Анықталған ұстанымдар","position":"Ұстаным","interests":"Шынайы мүдделер","consensus":"Келісу және келіспеу","agreement":"Келісу нүктелері","disagreement":"Келіспеу нүктелері","decisions":"Қабылданған шешімдер","action_items":"Тапсырмалар","task":"Тапсырма","responsible":"Жауапты","deadline":"Мерзімі","recommendations":"Ұсыныстар","rec_substance":"Мәні бойынша","rec_method":"Құралдар мен әдістемелер","smarty_rec":"Цифрлық Зерек ұсынысы","risks_title":"Тәуекелдер","risk":"Тәуекел","severity":"Ықтималдығы","mitigation":"Азайту","open_questions":"Ашық сұрақтар","action_plan":"Іс-қимыл жоспары","urgent":"Шұғыл (1-7 күн)","medium":"Орта мерзім (1-4 апта)","long_term":"Ұзақ мерзім (1-3 ай)","hidden_dynamics":"Жасырын динамика","conclusion":"Цифрлық Зерек қорытындысы","main_insight":"Басты түсінік","key_rec":"Негізгі ұсыныс","forecast":"Болжам","facts_badge":"Кездесу фактілері","rec_badge":"Зерек ұсыныстары","strengths":"Күшті жақтары","weaknesses":"Әлсіз жақтары","opportunities":"Мүмкіндіктер","threats":"Қауіптер"},
        "es": {"report_by":"Informe Experto de Digital Smarty","summary":"Resumen Ejecutivo","context":"Contexto y Alcance","industry":"Industria","meeting_type":"Tipo de reunión","complexity":"Complejidad","goals":"Objetivos","explicit_goals":"Objetivos explícitos","hidden_goals":"Objetivos ocultos","topics":"Temas clave","positions":"Posiciones identificadas","position":"Posición","interests":"Intereses reales","consensus":"Acuerdos y desacuerdos","agreement":"Puntos de acuerdo","disagreement":"Puntos de desacuerdo","decisions":"Decisiones tomadas","action_items":"Tareas pendientes","task":"Tarea","responsible":"Responsable","deadline":"Plazo","recommendations":"Recomendaciones","rec_substance":"De fondo","rec_method":"Herramientas y metodologías","smarty_rec":"Recomendación de Digital Smarty","risks_title":"Riesgos","risk":"Riesgo","severity":"Severidad","mitigation":"Mitigación","open_questions":"Preguntas abiertas","action_plan":"Plan de acción","urgent":"Urgente (1-7 días)","medium":"Medio plazo (1-4 semanas)","long_term":"Largo plazo (1-3 meses)","hidden_dynamics":"Dinámica oculta","conclusion":"Conclusión de Digital Smarty","main_insight":"Insight principal","key_rec":"Recomendación clave","forecast":"Pronóstico","facts_badge":"Hechos","rec_badge":"Recomendaciones","strengths":"Fortalezas","weaknesses":"Debilidades","opportunities":"Oportunidades","threats":"Amenazas"},
    }
    return labels.get(lang, labels.get("en", labels["ru"]))


def safe_filename(title: str) -> str:
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
    return safe.strip()[:60] or "meeting_report"
