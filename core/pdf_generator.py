"""
PDF Report Generator using ReportLab
Supports multiple languages
"""
import re
import logging
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import config

logger = logging.getLogger(__name__)

# Colors
PRIMARY_COLOR = HexColor("#2563eb")
SECONDARY_COLOR = HexColor("#7c3aed")
SUCCESS_COLOR = HexColor("#16a34a")
WARNING_COLOR = HexColor("#d97706")
DANGER_COLOR = HexColor("#dc2626")
GRAY_COLOR = HexColor("#6b7280")
TEXT_COLOR = HexColor("#1f2937")


def register_fonts() -> str:
    """Register fonts for PDF (supports Cyrillic, Chinese, etc.)"""
    fonts_dir = config.FONTS_DIR
    
    # Try Noto Sans (supports many languages)
    noto_regular = fonts_dir / "NotoSans-Regular.ttf"
    noto_bold = fonts_dir / "NotoSans-Bold.ttf"
    
    if noto_regular.exists():
        try:
            pdfmetrics.registerFont(TTFont("NotoSans", str(noto_regular)))
            if noto_bold.exists():
                pdfmetrics.registerFont(TTFont("NotoSans-Bold", str(noto_bold)))
            return "NotoSans"
        except Exception as e:
            logger.warning(f"Could not register Noto Sans: {e}")
    
    # Fallback to Helvetica
    return "Helvetica"


def create_styles(font_name: str) -> dict:
    """Create paragraph styles"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        fontName=font_name,
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=10*mm,
        alignment=1  # Center
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName=font_name,
        fontSize=12,
        textColor=GRAY_COLOR,
        spaceAfter=5*mm,
        alignment=1
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading',
        fontName=font_name,
        fontSize=14,
        textColor=PRIMARY_COLOR,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
    ))
    
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        fontName=font_name,
        fontSize=12,
        textColor=SECONDARY_COLOR,
        spaceBefore=5*mm,
        spaceAfter=3*mm,
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        fontName=font_name,
        fontSize=10,
        textColor=TEXT_COLOR,
        spaceAfter=3*mm,
        leading=14,
    ))
    
    styles.add(ParagraphStyle(
        name='Quote',
        fontName=font_name,
        fontSize=10,
        textColor=GRAY_COLOR,
        leftIndent=10*mm,
        spaceAfter=3*mm,
        fontName=font_name,
    ))
    
    styles.add(ParagraphStyle(
        name='ExpertTip',
        fontName=font_name,
        fontSize=11,
        textColor=SUCCESS_COLOR,
        leftIndent=5*mm,
        rightIndent=5*mm,
        spaceBefore=5*mm,
        spaceAfter=5*mm,
        borderColor=SUCCESS_COLOR,
        borderWidth=1,
        borderPadding=5,
    ))
    
    return styles


def markdown_to_reportlab(text: str, styles) -> list:
    """Convert markdown-like text to ReportLab flowables"""
    flowables = []
    
    for line in text.split('\n'):
        line = line.strip()
        
        if not line:
            flowables.append(Spacer(1, 2*mm))
            continue
        
        # Headers
        if line.startswith('# '):
            flowables.append(Paragraph(line[2:], styles['CustomTitle']))
        elif line.startswith('## '):
            flowables.append(Paragraph(line[3:], styles['CustomHeading']))
        elif line.startswith('### '):
            flowables.append(Paragraph(f"<b>{line[4:]}</b>", styles['CustomBody']))
        # Quotes
        elif line.startswith('>') or line.startswith('"'):
            flowables.append(Paragraph(line.strip('>"'), styles['Quote']))
        # Regular text
        else:
            # Convert markdown formatting
            line = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.+?)\*', r'<i>\1</i>', line)
            line = re.sub(r'`(.+?)`', r'<font face="Courier">\1</font>', line)
            flowables.append(Paragraph(line, styles['CustomBody']))
    
    return flowables


async def generate_pdf_report(
    output_path: str,
    analysis: str,
    diagnostics: str,
    transcript: str,
    duration: float,
    speakers_count: int,
    language: str = "ru",
    expertise: dict = None
):
    """
    Generate PDF report from analysis and diagnostics
    """
    
    font_name = register_fonts()
    styles = create_styles(font_name)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    story = []
    
    # ═══════════════════════════════════════════════════════════════
    # TITLE PAGE
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Paragraph("🧠 DIGITAL SMARTY", styles['CustomTitle']))
    story.append(Paragraph("Цифровой Умник — AI-эксперт", styles['Subtitle']))
    story.append(Spacer(1, 10*mm))
    
    # Expert info
    if expertise:
        expert_info = f"🎭 Analyzed as: <b>{expertise.get('expert_role', 'Expert')}</b>"
        story.append(Paragraph(expert_info, styles['CustomBody']))
        
        domain_info = f"📚 Domain: {expertise.get('domain_localized', expertise.get('domain', ''))}"
        story.append(Paragraph(domain_info, styles['CustomBody']))
        
        type_info = f"📎 Type: {expertise.get('meeting_type_localized', expertise.get('meeting_type', ''))}"
        story.append(Paragraph(type_info, styles['CustomBody']))
    
    story.append(Spacer(1, 5*mm))
    
    # Metadata
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    meta_text = f"📅 {date_str} | ⏱️ {minutes}:{seconds:02d} | 👥 {speakers_count}"
    story.append(Paragraph(meta_text, styles['CustomBody']))
    story.append(Spacer(1, 15*mm))
    
    # ═══════════════════════════════════════════════════════════════
    # ANALYSIS SECTION
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Paragraph("📊 EXPERT ANALYSIS", styles['CustomHeading']))
    story.extend(markdown_to_reportlab(analysis, styles))
    
    story.append(PageBreak())
    
    # ═══════════════════════════════════════════════════════════════
    # DIAGNOSTICS SECTION
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Paragraph("🔬 EXPERT DIAGNOSTICS", styles['CustomHeading']))
    story.extend(markdown_to_reportlab(diagnostics, styles))
    
    # ═══════════════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════════════
    
    story.append(Spacer(1, 15*mm))
    footer = "Generated by 🧠 Digital Smarty (Цифровой Умник) — AI Expert System"
    story.append(Paragraph(
        f"<para alignment='center'><font color='#9ca3af'>{footer}</font></para>",
        styles['CustomBody']
    ))
    
    # Build PDF
    doc.build(story)
    logger.info(f"PDF generated: {output_path}")
