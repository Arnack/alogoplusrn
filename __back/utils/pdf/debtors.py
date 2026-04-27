from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.paragraph import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from datetime import datetime
from io import BytesIO
import os

from .tools import wrap_text


# Регистрация шрифтов для поддержки кириллицы
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))

    bold_font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif-Bold.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', bold_font_path))
except Exception as e:
    print(f"Предупреждение: не удалось загрузить шрифты DejaVu в debtors: {e}")


async def create_archive_pdf(cycles: list) -> bytes:
    """
    Генерация PDF-отчёта: Архив удержаний.
    Таблица: № | ФИО | Даты неявок | Сумма удержания / "П"
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=30,
        bottomMargin=30
    )
    elements = []

    # Заголовок
    title_style = ParagraphStyle(
        name='Title',
        fontName='DejaVuSerif-Bold',
        fontSize=12,
        alignment=1,
        spaceAfter=20
    )
    elements.append(Paragraph('АРХИВ УДЕРЖАНИЙ ДОГОВОРНОЙ КОМИССИИ', title_style))
    elements.append(Spacer(1, 10))

    # Сортировка по ФИО (от А до Я)
    cycles_sorted = sorted(
        cycles,
        key=lambda c: (
            c.worker.security.last_name.lower(),
            c.worker.security.first_name.lower(),
            c.worker.security.middle_name.lower()
        )
    )

    # Формирование таблицы
    table_data = [['№', 'ФИО', 'Даты неявок', 'Сумма удержания']]

    total_amount = 0

    for idx, cycle in enumerate(cycles_sorted, 1):
        worker_data = cycle.worker.security
        full_name = f"{worker_data.last_name} {worker_data.first_name} {worker_data.middle_name}"

        # Собрать даты невыходов
        dates_str = ', '.join(event.no_show_date for event in cycle.no_show_events)
        dates_style = ParagraphStyle(
            name='Dates',
            fontName='DejaVuSerif',
            fontSize=10,
            leading=13,
        )
        dates_paragraph = Paragraph(dates_str.replace(', ', ',<br/>'), dates_style)

        # Определить сумму или "П"
        if cycle.status == 'annulled':
            amount_str = 'П'
        else:
            amount_str = f"{cycle.deducted_amount:,} ₽"
            total_amount += cycle.deducted_amount

        table_data.append([
            idx,
            wrap_text(full_name, 30),
            dates_paragraph,
            amount_str
        ])

    # Создание таблицы
    col_widths = [30, 190, 160, 130]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    # Легенда
    elements.append(Spacer(1, 15))
    note_style = ParagraphStyle(
        name='Note',
        fontName='DejaVuSerif',
        fontSize=8,
        alignment=0
    )
    elements.append(Paragraph(
        "* П — договорная комиссия аннулирована администратором.",
        note_style
    ))

    # Итоговая сумма + Штамп (вместе, чтобы не разрывались по страницам)
    from .payment_order import StampFlowable
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    total_style = ParagraphStyle(
        name='Total',
        fontName='DejaVuSerif-Bold',
        fontSize=11,
        alignment=0
    )
    elements.append(KeepTogether([
        Spacer(1, 10),
        Paragraph(
            f"Итоговая сумма удержаний за выбранный период: {total_amount:,} ₽",
            total_style
        ),
        Spacer(1, 40),
        StampFlowable(current_datetime),
    ]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


async def create_unfulfilled_pdf(cycles: list) -> bytes:
    """
    Генерация PDF-отчёта: Неисполненные заявки (активные должники).
    Таблица: № | ФИО | Даты неявок | Назначенная сумма (MAX)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=30,
        bottomMargin=30
    )
    elements = []

    # Заголовок
    title_style = ParagraphStyle(
        name='Title',
        fontName='DejaVuSerif-Bold',
        fontSize=12,
        alignment=1,
        spaceAfter=20
    )
    current_date = datetime.now().strftime('%d.%m.%Y')
    elements.append(Paragraph(
        f'САМОЗАНЯТЫЕ С НЕИСПОЛНЕННЫМИ ДОГОВОРНЫМИ КОМИССИЯМИ<br/>(на {current_date})',
        title_style
    ))
    elements.append(Spacer(1, 10))

    # Группировка циклов по работникам
    from collections import defaultdict
    workers_data = defaultdict(lambda: {'cycles': [], 'worker': None})

    for cycle in cycles:
        workers_data[cycle.worker_id]['cycles'].append(cycle)
        workers_data[cycle.worker_id]['worker'] = cycle.worker

    # Сортировка по ФИО (от А до Я)
    workers_sorted = sorted(
        workers_data.values(),
        key=lambda w: (
            w['worker'].security.last_name.lower(),
            w['worker'].security.first_name.lower(),
            w['worker'].security.middle_name.lower()
        )
    )

    # Формирование таблицы
    table_data = [['№', 'ФИО', 'Даты неявок', 'Сумма удержания']]

    total_assigned = 0

    for idx, worker_info in enumerate(workers_sorted, 1):
        worker_data = worker_info['worker'].security
        full_name = f"{worker_data.last_name} {worker_data.first_name} {worker_data.middle_name}"

        # Собрать все даты невыходов из всех циклов работника
        all_dates = []
        all_amounts = []
        for cycle in worker_info['cycles']:
            for event in cycle.no_show_events:
                all_dates.append(event.no_show_date)
                all_amounts.append(event.assigned_amount)

        dates_str = '; '.join(all_dates)

        # Найти максимальную назначенную сумму
        max_amount = max(all_amounts, default=0)
        total_assigned += max_amount

        dates_style = ParagraphStyle(
            name='Dates',
            fontName='DejaVuSerif',
            fontSize=10,
            leading=13,
        )

        table_data.append([
            idx,
            wrap_text(full_name, 30),
            Paragraph(dates_str.replace('; ', ';<br/>'), dates_style),
            f"{max_amount:,} ₽"
        ])

    # Создание таблицы
    col_widths = [30, 190, 160, 130]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)

    # Итоговая сумма + Штамп (вместе, чтобы не разрывались по страницам)
    from .payment_order import StampFlowable
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    total_style = ParagraphStyle(
        name='Total',
        fontName='DejaVuSerif-Bold',
        fontSize=11,
        alignment=0
    )
    elements.append(KeepTogether([
        Spacer(1, 15),
        Paragraph(
            f"Общая сумма назначенных удержаний: {total_assigned:,} ₽",
            total_style
        ),
        Spacer(1, 40),
        StampFlowable(current_datetime),
    ]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
