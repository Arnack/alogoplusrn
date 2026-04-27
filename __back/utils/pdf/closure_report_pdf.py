import calendar
from collections import defaultdict
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

import os

# Шрифты уже регистрируются в pdf_generator.py, но на всякий случай
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif.ttf')
    bold_font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif-Bold.ttf')
    if 'DejaVuSerif' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))
    if 'DejaVuSerif-Bold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', bold_font_path))
except Exception:
    pass

# Цвета
WEEKEND_BG = colors.Color(1.0, 0.92, 0.92)  # бледно-красный
SUBTOTAL_BG = colors.Color(0.92, 0.95, 1.0)  # бледно-голубой
HEADER_BG = colors.Color(0.85, 0.85, 0.85)
ROW_LABELS = ['Д Заявка', 'Д Вышло', 'Д %', 'Н Заявка', 'Н Вышло', 'Н %', 'ЗА ДЕНЬ %']
BOTTOM_LABELS = ['Заявка за сутки', 'Вышло за сутки', '% закрытия', 'День недели']
WEEKDAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
PCT_LABELS = {'Д %', 'Н %', 'ЗА ДЕНЬ %', '% закрытия'}


def _pct_color(pct_str):
    """Цвет фона по проценту: красный(0%) → жёлтый(50%) → зелёный(100%+). Бледные тона."""
    if not pct_str:
        return None
    try:
        val = float(pct_str.replace('%', ''))
    except ValueError:
        return None
    # 100%+ = зелёный, 50% = оранжевый, 0% = красный
    if val >= 100:
        return colors.Color(0.7, 1.0, 0.7)  # бледно-зелёный
    val = max(0.0, val)
    if val <= 50:
        # 0% красный → 50% оранжевый
        t = val / 50.0
        r = 1.0
        g = 0.7 + 0.15 * t  # 0.7 → 0.85
        b = 0.7
    else:
        # 50% оранжевый → 100% жёлто-зелёный (почти зелёный)
        t = (val - 50) / 50.0
        r = 1.0 - 0.3 * t   # 1.0 → 0.7
        g = 0.85 + 0.15 * t  # 0.85 → 1.0
        b = 0.7
    return colors.Color(r, g, b)


def _fmt_pct(numerator, denominator):
    """Форматирование процента. Если знаменатель 0 — пустая строка."""
    if not denominator:
        return ''
    val = numerator / denominator * 100
    return f"{val:.2f}%"


def _fmt_val(val):
    """Значение: 0 или None → пустая строка."""
    if not val:
        return ''
    return str(val)


def _aggregate_data(raw_orders, month, year):
    """
    Агрегирует сырые данные из БД.

    Возвращает:
        recipients: dict[customer_name] -> dict[day_num] -> {d_req, d_out, n_req, n_out}
        days_in_month: int
    """
    days_in_month = calendar.monthrange(year, month)[1]

    # recipients[customer_name][day] = {d_req, d_out, n_req, n_out}
    recipients = defaultdict(lambda: defaultdict(lambda: {'d_req': 0, 'd_out': 0, 'n_req': 0, 'n_out': 0}))

    for order in raw_orders:
        name = order['customer_name']
        # Парсим день из даты DD.MM.YYYY
        try:
            day_num = int(order['date'].split('.')[0])
        except (ValueError, IndexError):
            continue

        if day_num < 1 or day_num > days_in_month:
            continue

        is_day = order['day_shift'] is not None
        is_night = order['night_shift'] is not None

        if is_day:
            recipients[name][day_num]['d_req'] += order['workers_count']
            recipients[name][day_num]['d_out'] += order['worked_count']
        if is_night:
            recipients[name][day_num]['n_req'] += order['workers_count']
            recipients[name][day_num]['n_out'] += order['worked_count']

    return dict(recipients), days_in_month


def _sum_range(data_by_day, start, end, key):
    """Сумма значений по ключу за диапазон дней."""
    return sum(data_by_day.get(d, {}).get(key, 0) for d in range(start, end + 1))


def generate_closure_report_pdf(raw_orders, month, year):
    """
    Генерирует PDF-отчет закрываемости.

    Args:
        raw_orders: список словарей из get_archive_orders_for_month
        month: int
        year: int

    Returns:
        bytes — содержимое PDF
    """
    recipients, days_in_month = _aggregate_data(raw_orders, month, year)
    sorted_names = sorted(recipients.keys())

    # --- Построение столбцов ---
    # Получатель | Показатель | 1..15 | 1-15 | 16..N | 16-N | ИТОГО
    day_cols = list(range(1, days_in_month + 1))

    # Определяем выходные
    weekends = set()
    for d in day_cols:
        wd = date(year, month, d).weekday()
        if wd >= 5:
            weekends.add(d)

    # Индексы столбцов (0-based)
    # col 0 = Получатель, col 1 = Показатель
    # col 2..16 = дни 1-15
    # col 17 = "1-15"
    # col 18.. = дни 16-N
    # col next = "16-N"
    # col next = "ИТОГО"

    header_row = ['', '']
    for d in range(1, 16):
        header_row.append(str(d))
    header_row.append('1-15')
    for d in range(16, days_in_month + 1):
        header_row.append(str(d))
    header_row.append(f'16-{days_in_month}')
    header_row.append('ИТОГО')

    total_cols = len(header_row)

    # Маппинг: column_index -> day_number (для данных)
    col_to_day = {}
    idx = 2
    for d in range(1, 16):
        col_to_day[idx] = d
        idx += 1
    subtotal_1_col = idx  # "1-15"
    idx += 1
    for d in range(16, days_in_month + 1):
        col_to_day[idx] = d
        idx += 1
    subtotal_2_col = idx  # "16-N"
    idx += 1
    total_col = idx  # "ИТОГО"

    # Индексы столбцов выходных
    weekend_cols = set()
    for ci, d in col_to_day.items():
        if d in weekends:
            weekend_cols.add(ci)

    # --- Заполнение данных ---
    data_rows = [header_row]

    for name in sorted_names:
        rdata = recipients[name]
        block = []
        for row_label in ROW_LABELS:
            row = ['' if block else name, row_label]
            for ci in range(2, total_cols):
                if ci in col_to_day:
                    d = col_to_day[ci]
                    dd = rdata.get(d, {'d_req': 0, 'd_out': 0, 'n_req': 0, 'n_out': 0})
                    val = _cell_value(row_label, dd)
                    row.append(val)
                elif ci == subtotal_1_col:
                    val = _range_value(row_label, rdata, 1, 15)
                    row.append(val)
                elif ci == subtotal_2_col:
                    val = _range_value(row_label, rdata, 16, days_in_month)
                    row.append(val)
                elif ci == total_col:
                    val = _range_value(row_label, rdata, 1, days_in_month)
                    row.append(val)
                else:
                    row.append('')
            block.append(row)
        data_rows.extend(block)

    # --- Нижний блок (ИТОГО) ---
    # Пустая строка-разделитель
    data_rows.append([''] * total_cols)

    bottom_start_row = len(data_rows)

    for bl_label in BOTTOM_LABELS:
        row = ['ИТОГО' if bl_label == BOTTOM_LABELS[0] else '', bl_label]
        for ci in range(2, total_cols):
            if bl_label == 'День недели':
                if ci in col_to_day:
                    d = col_to_day[ci]
                    wd = date(year, month, d).weekday()
                    row.append(WEEKDAY_NAMES[wd])
                else:
                    row.append('')
            elif ci in col_to_day:
                d = col_to_day[ci]
                row.append(_bottom_cell(bl_label, sorted_names, recipients, d, d))
            elif ci == subtotal_1_col:
                row.append(_bottom_cell(bl_label, sorted_names, recipients, 1, 15))
            elif ci == subtotal_2_col:
                row.append(_bottom_cell(bl_label, sorted_names, recipients, 16, days_in_month))
            elif ci == total_col:
                row.append(_bottom_cell(bl_label, sorted_names, recipients, 1, days_in_month))
            else:
                row.append('')
        data_rows.append(row)

    # --- Генерация PDF ---
    buffer = BytesIO()
    page_size = landscape(A4)
    margin = 15

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=20,
        bottomMargin=20,
    )

    elements = []

    # Заголовок
    style_title = ParagraphStyle(
        name='ClosureTitle',
        fontName='DejaVuSerif-Bold',
        fontSize=8,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    month_names = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                   'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    title_text = f"Закрываемость — {month_names[month]} {year}"
    elements.append(Paragraph(title_text, style_title))
    elements.append(Spacer(1, 1.5 * mm))

    # Ширины столбцов — рассчитываем чтобы всё влезло на альбомный A4
    usable_width = page_size[0] - 2 * margin  # ~812 pt
    data_col_count = total_cols - 2  # дни + 3 итога
    # Название и показатель — минимальные, остальное на данные
    name_col_w = 55
    label_col_w = 38
    remaining = usable_width - name_col_w - label_col_w
    data_col_w = remaining / data_col_count
    col_widths = [name_col_w, label_col_w] + [data_col_w] * data_col_count

    table = Table(data_rows, colWidths=col_widths, repeatRows=1)

    # --- Стили таблицы ---
    font_size = 3.5
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), font_size),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]

    # Выходные — бледно-красный фон (только строки данных, не нижний блок)
    for wc in weekend_cols:
        # Строки данных: от 1 (после заголовка) до bottom_start_row - 1
        if bottom_start_row > 1:
            style_cmds.append(('BACKGROUND', (wc, 1), (wc, bottom_start_row - 1), WEEKEND_BG))

    # Промежуточные итоги — выделение столбцов
    for sc in [subtotal_1_col, subtotal_2_col]:
        style_cmds.append(('BACKGROUND', (sc, 0), (sc, bottom_start_row - 1), SUBTOTAL_BG))
        style_cmds.append(('FONTNAME', (sc, 0), (sc, -1), 'DejaVuSerif-Bold'))

    # Итого столбец
    style_cmds.append(('FONTNAME', (total_col, 0), (total_col, -1), 'DejaVuSerif-Bold'))

    # Жирный шрифт для имён получателей (столбец 0)
    style_cmds.append(('FONTNAME', (0, 1), (0, -1), 'DejaVuSerif-Bold'))

    # Цветовой градиент для ячеек с процентами
    for ri, row in enumerate(data_rows):
        if ri == 0:
            continue
        # Определяем, является ли строка процентной (по столбцу 1 — показатель)
        label = row[1] if len(row) > 1 else ''
        if label not in PCT_LABELS:
            continue
        for ci in range(2, len(row)):
            clr = _pct_color(row[ci])
            if clr:
                style_cmds.append(('BACKGROUND', (ci, ri), (ci, ri), clr))

    # Нижний блок — жирный
    if bottom_start_row < len(data_rows):
        style_cmds.append(('FONTNAME', (0, bottom_start_row), (-1, -1), 'DejaVuSerif-Bold'))
        style_cmds.append(('FONTSIZE', (0, bottom_start_row), (-1, -1), font_size))

    # Merge для имени получателя (по 7 строк) + жирная линия-разделитель снизу
    row_idx = 1  # после заголовка
    for _ in sorted_names:
        if row_idx + 6 < len(data_rows):
            style_cmds.append(('SPAN', (0, row_idx), (0, row_idx + 6)))
            style_cmds.append(('VALIGN', (0, row_idx), (0, row_idx + 6), 'MIDDLE'))
            # Жирная линия под блоком получателя
            style_cmds.append(('LINEBELOW', (0, row_idx + 6), (-1, row_idx + 6), 1.5, colors.black))
        row_idx += 7

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _cell_value(label, dd):
    """Значение ячейки для конкретного дня и показателя."""
    if label == 'Д Заявка':
        return _fmt_val(dd['d_req'])
    elif label == 'Д Вышло':
        return _fmt_val(dd['d_out'])
    elif label == 'Д %':
        return _fmt_pct(dd['d_out'], dd['d_req'])
    elif label == 'Н Заявка':
        return _fmt_val(dd['n_req'])
    elif label == 'Н Вышло':
        return _fmt_val(dd['n_out'])
    elif label == 'Н %':
        return _fmt_pct(dd['n_out'], dd['n_req'])
    elif label == 'ЗА ДЕНЬ %':
        total_req = dd['d_req'] + dd['n_req']
        total_out = dd['d_out'] + dd['n_out']
        return _fmt_pct(total_out, total_req)
    return ''


def _range_value(label, rdata, start, end):
    """Значение для промежуточного итога (диапазон дней)."""
    if label in ('Д Заявка', 'Д Вышло', 'Н Заявка', 'Н Вышло'):
        key_map = {'Д Заявка': 'd_req', 'Д Вышло': 'd_out', 'Н Заявка': 'n_req', 'Н Вышло': 'n_out'}
        total = _sum_range(rdata, start, end, key_map[label])
        return _fmt_val(total)
    elif label == 'Д %':
        req = _sum_range(rdata, start, end, 'd_req')
        out = _sum_range(rdata, start, end, 'd_out')
        return _fmt_pct(out, req)
    elif label == 'Н %':
        req = _sum_range(rdata, start, end, 'n_req')
        out = _sum_range(rdata, start, end, 'n_out')
        return _fmt_pct(out, req)
    elif label == 'ЗА ДЕНЬ %':
        d_req = _sum_range(rdata, start, end, 'd_req')
        d_out = _sum_range(rdata, start, end, 'd_out')
        n_req = _sum_range(rdata, start, end, 'n_req')
        n_out = _sum_range(rdata, start, end, 'n_out')
        return _fmt_pct(d_out + n_out, d_req + n_req)
    return ''


def _bottom_cell(label, sorted_names, recipients, start, end):
    """Значение ячейки нижнего блока."""
    if label == 'Заявка за сутки':
        total = 0
        for name in sorted_names:
            rdata = recipients[name]
            total += _sum_range(rdata, start, end, 'd_req')
            total += _sum_range(rdata, start, end, 'n_req')
        return _fmt_val(total)
    elif label == 'Вышло за сутки':
        total = 0
        for name in sorted_names:
            rdata = recipients[name]
            total += _sum_range(rdata, start, end, 'd_out')
            total += _sum_range(rdata, start, end, 'n_out')
        return _fmt_val(total)
    elif label == '% закрытия':
        total_req = 0
        total_out = 0
        for name in sorted_names:
            rdata = recipients[name]
            total_req += _sum_range(rdata, start, end, 'd_req')
            total_req += _sum_range(rdata, start, end, 'n_req')
            total_out += _sum_range(rdata, start, end, 'd_out')
            total_out += _sum_range(rdata, start, end, 'n_out')
        return _fmt_pct(total_out, total_req)
    return ''
