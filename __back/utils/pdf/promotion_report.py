from __future__ import annotations

import io
from datetime import datetime
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


async def generate_promotion_report_pdf(
    bonuses: list,   # list of (PromotionBonus, PromotionParticipation, Promotion) rows
    date_from: datetime,
    date_to: datetime,
) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        spaceAfter=12,
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica',
    )

    story = []
    story.append(Paragraph('Отчёт по акциям', title_style))
    story.append(Paragraph(
        f'Период: {date_from.strftime("%d.%m.%Y")} – {date_to.strftime("%d.%m.%Y")}',
        subtitle_style
    ))

    # Build table
    headers = ['ФИО исполнителя', 'Акция', 'Сумма (₽)', 'Дата начисления']
    table_data = [[Paragraph(h, header_style) for h in headers]]

    total = 0
    for row in bonuses:
        bonus, participation, promo = row
        # Get worker real name
        from database.models import async_session
        from database.models import DataForSecurity
        from sqlalchemy import select
        async with async_session() as session:
            real_data = await session.scalar(
                select(DataForSecurity).where(DataForSecurity.user_id == bonus.worker_id)
            )
        if real_data:
            full_name = f'{real_data.last_name} {real_data.first_name} {real_data.middle_name or ""}'.strip()
        else:
            full_name = f'ID {bonus.worker_id}'

        table_data.append([
            Paragraph(full_name, cell_style),
            Paragraph(bonus.promotion_name, cell_style),
            Paragraph(str(bonus.amount), cell_style),
            Paragraph(bonus.accrued_at.strftime('%d.%m.%Y %H:%M'), cell_style),
        ])
        total += bonus.amount

    # Total row
    table_data.append([
        Paragraph('ИТОГО', header_style),
        Paragraph('', cell_style),
        Paragraph(str(total), header_style),
        Paragraph('', cell_style),
    ])

    col_widths = [2.4 * inch, 1.8 * inch, 0.9 * inch, 1.3 * inch]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007aff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Всего начислено: <b>{total} ₽</b>', subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
