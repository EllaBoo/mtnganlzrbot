import os
from jinja2 import Template
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime
from config import Config

class ReportGenerator:
    
    def __init__(self):
        self.template = self._get_template()
        self.css = self._get_css()
    
    def _get_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">Digital Smarty</div>
            <h1>{{ title }}</h1>
            <div class="meta">
                <span>{{ date }}</span>
                <span>{{ duration }} min</span>
                <span>{{ participants }} participants</span>
                {% if detected_language %}
                <span>{{ detected_language }}</span>
                {% endif %}
            </div>
        </header>

        {% if smarty_comment %}
        <div class="smarty-quote">
            <em>"{{ smarty_comment }}"</em>
            <span class="signature">- Digital Smarty</span>
        </div>
        {% endif %}

        <section class="topics">
            <h2>Key Topics</h2>
            {% for topic in key_topics %}
            <div class="topic-card {{ topic.importance }}">
                <h3>{{ topic.topic }}</h3>
                <p>{{ topic.summary }}</p>
                <span class="badge">{{ topic.importance }}</span>
            </div>
            {% endfor %}
        </section>

        <section class="speakers">
            <h2>Speaker Positions</h2>
            {% for speaker in speaker_positions %}
            <div class="speaker-card">
                <h3>{{ speaker.speaker }}</h3>
                <p class="stance">{{ speaker.stance }}</p>
                <ul>
                {% for point in speaker.main_points %}
                    <li>{{ point }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </section>

        {% if decisions %}
        <section class="decisions">
            <h2>Decisions Made</h2>
            <ol>
            {% for d in decisions %}
                <li>
                    <strong>{{ d.decision }}</strong>
                    {% if d.context %}<br><small>{{ d.context }}</small>{% endif %}
                </li>
            {% endfor %}
            </ol>
        </section>
        {% endif %}

        {% if action_items %}
        <section class="tasks">
            <h2>Action Items</h2>
            <div class="task-list">
            {% for task in action_items %}
                <div class="task-item">
                    <span class="checkbox">[ ]</span>
                    <span class="task-text">{{ task.task }}</span>
                    <span class="responsible">-> {{ task.responsible }}</span>
                    {% if task.deadline and task.deadline != "null" %}
                    <span class="deadline">{{ task.deadline }}</span>
                    {% endif %}
                </div>
            {% endfor %}
            </div>
        </section>
        {% endif %}

        {% if open_questions or risks %}
        <section class="warnings">
            <h2>Open Questions and Risks</h2>
            
            {% if open_questions %}
            <div class="questions">
                <h3>Questions</h3>
                <ul>
                {% for q in open_questions %}
                    <li>{{ q.question }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if risks %}
            <div class="risks">
                <h3>Risks</h3>
                {% for r in risks %}
                <div class="risk-item {{ r.severity }}">
                    <span class="severity-dot"></span>
                    {{ r.risk }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </section>
        {% endif %}

        {% if reality_check %}
        <section class="reality-check">
            <h2>Reality Check</h2>
            <div class="feasibility">
                <strong>Feasibility Assessment:</strong>
                <p>{{ reality_check.feasibility }}</p>
            </div>
            
            {% if reality_check.concerns %}
            <div class="concerns">
                <strong>Potential Issues:</strong>
                <ul>
                {% for c in reality_check.concerns %}
                    <li>{{ c }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            {% if reality_check.recommendations %}
            <div class="recommendations">
                <strong>Recommendations:</strong>
                <ul>
                {% for r in reality_check.recommendations %}
                    <li>{{ r }}</li>
                {% endfor %}
                </ul>
            </div>
            {% endif %}
        </section>
        {% endif %}

        <section class="insights">
            <h2>Key Insights</h2>
            <ol class="insights-list">
            {% for insight in key_insights %}
                <li>{{ insight }}</li>
            {% endfor %}
            </ol>
        </section>

        <footer>
            <p>Generated by Digital Smarty v4.0 | {{ generated_at }}</p>
        </footer>
    </div>
</body>
</html>'''

    def _get_css(self) -> str:
        return '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    color: #1a1a2e;
    background: #ffffff;
}

.container { max-width: 800px; margin: 0 auto; padding: 40px; }

header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #eef2f7;
}

.logo { font-size: 24px; margin-bottom: 10px; }

header h1 {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 15px;
}

.meta {
    display: flex;
    justify-content: center;
    gap: 20px;
    color: #64748b;
    font-size: 13px;
}

.smarty-quote {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px 25px;
    border-radius: 12px;
    margin-bottom: 30px;
}

.smarty-quote em { font-size: 16px; }

.smarty-quote .signature {
    display: block;
    text-align: right;
    margin-top: 10px;
    font-size: 12px;
    opacity: 0.8;
}

section { margin-bottom: 30px; }

h2 {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 1px solid #eef2f7;
}

h3 { font-size: 15px; font-weight: 600; margin-bottom: 8px; }

.topic-card {
    background: #f8fafc;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    border-left: 4px solid #667eea;
}

.topic-card.high { border-left-color: #ef4444; }
.topic-card.medium { border-left-color: #f59e0b; }
.topic-card.low { border-left-color: #10b981; }

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    background: #e2e8f0;
    color: #64748b;
}

.speaker-card {
    background: #f8fafc;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}

.speaker-card .stance {
    color: #64748b;
    font-style: italic;
    margin-bottom: 10px;
}

.speaker-card ul { margin-left: 20px; }

.task-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid #eef2f7;
}

.checkbox { font-size: 18px; color: #667eea; }
.task-text { flex: 1; }
.responsible { color: #667eea; font-weight: 500; font-size: 13px; }
.deadline { color: #f59e0b; font-size: 12px; }

.risk-item {
    padding: 10px 15px;
    background: #fef2f2;
    border-radius: 6px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.risk-item.high { background: #fef2f2; }
.risk-item.medium { background: #fffbeb; }
.risk-item.low { background: #f0fdf4; }

.severity-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
}

.risk-item.medium .severity-dot { background: #f59e0b; }
.risk-item.low .severity-dot { background: #10b981; }

.reality-check {
    background: #f0f9ff;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #bae6fd;
}

.reality-check h2 { border-bottom: none; margin-bottom: 15px; }
.feasibility, .concerns, .recommendations { margin-bottom: 15px; }

.insights-list { counter-reset: insights; list-style: none; }

.insights-list li {
    counter-increment: insights;
    padding: 12px 15px 12px 45px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 8px;
    position: relative;
}

.insights-list li::before {
    content: counter(insights);
    position: absolute;
    left: 15px;
    width: 22px;
    height: 22px;
    background: #667eea;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
}

footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #eef2f7;
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
}
'''

    def generate_html(self, analysis: dict, transcript_data: dict) -> str:
        template = Template(self.template)
        
        html = template.render(
            css=self.css,
            title=analysis.get("title", "Meeting Summary"),
            date=analysis.get("date_mentioned") or datetime.now().strftime("%d.%m.%Y"),
            duration=analysis.get("duration_minutes", 0),
            participants=analysis.get("participants_count", 1),
            detected_language=analysis.get("detected_language"),
            smarty_comment=analysis.get("smarty_comment"),
            key_topics=analysis.get("key_topics", []),
            speaker_positions=analysis.get("speaker_positions", []),
            decisions=analysis.get("decisions", []),
            action_items=analysis.get("action_items", []),
            open_questions=analysis.get("open_questions", []),
            risks=analysis.get("risks", []),
            reality_check=analysis.get("reality_check"),
            key_insights=analysis.get("key_insights", []),
            generated_at=datetime.now().strftime("%d.%m.%Y %H:%M")
        )
        return html
    
    def generate_pdf(self, html_content: str, output_path: str) -> str:
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        html.write_pdf(output_path, font_config=font_config)
        return output_path
    
    def generate_transcript_file(self, transcript_data: dict, output_path: str) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("TRANSCRIPT")
        lines.append(f"Duration: {int(transcript_data.get('duration', 0) / 60)} min")
        lines.append(f"Participants: {transcript_data.get('speakers_count', 1)}")
        lines.append("=" * 60)
        lines.append("")
        
        for segment in transcript_data.get("speakers", []):
            speaker = f"Speaker {segment['speaker'] + 1}"
            lines.append(f"[{speaker}]")
            lines.append(segment["text"])
            lines.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        return output_path
