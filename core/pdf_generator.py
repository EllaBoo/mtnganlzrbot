"""
Digital Smarty v4.0 - PDF Report Generator
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import config


def register_fonts() -> str:
    """Register custom fonts, return font name to use."""
    font_paths = [
        config.FONTS_DIR / "DejaVuSans.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    ]
    
    for font_path in font_paths:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", str(font_path)))
                return "DejaVuSans"
            except Exception:
                continue
    
    return "Helvetica"


def generate_pdf_report(
    text: str,
    analysis: dict,
    language: str = "ru",
    output_path: Optional[Path] = None
) -> Path:
    """Generate PDF report with transcription and analysis."""
    
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = config.TMP_DIR / f"report_{timestamp}.pdf"
    
    font_name = register_fonts()
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles with font
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        spaceAfter=12,
        textColor=colors.HexColor('#2C3E50')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#34495E')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=16,
        spaceAfter=8
    )
    
    # Build document content
    story = []
    
    # Title
    titles = {
        "ru": "Анализ речи",
        "en": "Speech Analysis",
        "es": "Análisis del habla"
    }
    story.append(Paragraph(titles.get(language, titles["en"]), title_style))
    story.append(Spacer(1, 10*mm))
    
    # Transcription section
    trans_titles = {
        "ru": "Транскрипция",
        "en": "Transcription", 
        "es": "Transcripción"
    }
    story.append(Paragraph(trans_titles.get(language, trans_titles["en"]), heading_style))
    
    # Clean and add transcription text
    clean_text = text.replace('\n', '<br/>')
    story.append(Paragraph(clean_text, body_style))
    story.append(Spacer(1, 8*mm))
    
    # Analysis section
    analysis_titles = {
        "ru": "Анализ",
        "en": "Analysis",
        "es": "Análisis"
    }
    story.append(Paragraph(analysis_titles.get(language, analysis_titles["en"]), heading_style))
    
    # Summary
    if analysis.get("summary"):
        summary_titles = {
            "ru": "Краткое содержание:",
            "en": "Summary:",
            "es": "Resumen:"
        }
        story.append(Paragraph(f"<b>{summary_titles.get(language, summary_titles['en'])}</b>", body_style))
        story.append(Paragraph(analysis["summary"], body_style))
        story.append(Spacer(1, 4*mm))
    
    # Key points
    if analysis.get("key_points"):
        points_titles = {
            "ru": "Ключевые моменты:",
            "en": "Key Points:",
            "es": "Puntos clave:"
        }
        story.append(Paragraph(f"<b>{points_titles.get(language, points_titles['en'])}</b>", body_style))
        for point in analysis["key_points"]:
            story.append(Paragraph(f"• {point}", body_style))
        story.append(Spacer(1, 4*mm))
    
    # Recommendations
    if analysis.get("recommendations"):
        rec_titles = {
            "ru": "Рекомендации:",
            "en": "Recommendations:",
            "es": "Recomendaciones:"
        }
        story.append(Paragraph(f"<b>{rec_titles.get(language, rec_titles['en'])}</b>", body_style))
        for rec in analysis["recommendations"]:
            story.append(Paragraph(f"• {rec}", body_style))
    
    # Statistics table
    if analysis.get("statistics"):
        story.append(Spacer(1, 8*mm))
        stats_titles = {
            "ru": "Статистика",
            "en": "Statistics",
            "es": "Estadísticas"
        }
        story.append(Paragraph(stats_titles.get(language, stats_titles["en"]), heading_style))
        
        stats = analysis["statistics"]
        stat_labels = {
            "ru": ["Слов", "Предложений", "Время речи"],
            "en": ["Words", "Sentences", "Speaking time"],
            "es": ["Palabras", "Oraciones", "Tiempo de habla"]
        }
        labels = stat_labels.get(language, stat_labels["en"])
        
        table_data = [
            [labels[0], str(stats.get("word_count", "N/A"))],
            [labels[1], str(stats.get("sentence_count", "N/A"))],
            [labels[2], stats.get("duration", "N/A")],
        ]
        
        table = Table(table_data, colWidths=[80*mm, 60*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DEE2E6')),
        ]))
        story.append(table)
    
    # Footer with timestamp
    story.append(Spacer(1, 15*mm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        textColor=colors.HexColor('#95A5A6')
    )
    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(f"Generated by Digital Smarty • {timestamp_text}", footer_style))
    
    # Build PDF
    doc.build(story)
    
    return output_path
