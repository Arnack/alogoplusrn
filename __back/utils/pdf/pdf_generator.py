import logging

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Spacer
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from decimal import Decimal
from datetime import datetime
from functools import partial
from io import BytesIO
import pytz
import os

from .tools import wrap_text


# Регистрация шрифтов для поддержки кириллицы
# Используем абсолютный путь относительно корня проекта
try:
    # Получаем корень проекта (два уровня вверх от utils/pdf/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))

    bold_font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif-Bold.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', bold_font_path))
except Exception as e:
    # Если шрифты не найдены (например, при запуске Max бота), используем стандартные
    print(f"Предупреждение: не удалось загрузить шрифты DejaVu: {e}")
    print("PDF генератор будет использовать стандартные шрифты")


class StampFlowable(Flowable):
    """Flowable для печати в правом нижнем углу последней страницы"""
    def __init__(self, current_datetime):
        Flowable.__init__(self)
        self.current_datetime = current_datetime
        self.block_width = 300
        self.block_height = 90

    def draw(self):
        from reportlab.lib import colors

        canvas = self.canv
        page_width = canvas._pagesize[0]
        margin_right = 50
        margin_bottom = 10

        x_position = page_width - self.block_width - margin_right
        y_position = margin_bottom

        canvas.saveState()

        # Рисуем рамку
        canvas.setStrokeColor(colors.HexColor('#0066cc'))
        canvas.setLineWidth(2)
        canvas.rect(x_position, y_position, self.block_width, self.block_height)

        # Заголовок блока
        canvas.setFont('DejaVuSerif-Bold', 9)
        canvas.setFillColor(colors.HexColor('#0066cc'))

        text_y = y_position + self.block_height - 15
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Документ сформирован автоматически')
        text_y -= 11
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'информационной системой (программой для ЭВМ)')
        text_y -= 11
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Платформы «Алгоритм Плюс».')

        # Дата и время
        canvas.setFont('DejaVuSerif', 8)
        text_y -= 16
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Дата и время формирования:')
        text_y -= 10
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                f'{self.current_datetime} (MSK)')

        # Последний текст
        canvas.setFont('DejaVuSerif', 7.5)
        text_y -= 14
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Данный Документ сформирован без участия и без ручного')
        text_y -= 9
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'редактирования со стороны физических лиц.')

        canvas.restoreState()

    def wrap(self, _availWidth, _availHeight):
        return (self.block_width, self.block_height)


def on_later_pages(canvas, _document):
    """Функция для последующих страниц (без дополнительных элементов)"""
    pass


def on_first_page(canvas, _document, page_height, page_width, date_str, city, customer):
    # Логотип
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        canvas.drawImage(
            logo_path, 40, page_height - 80, width=80, height=80
        )

    # Основной заголовок (центрированный, ниже логотипа)
    canvas.setFont('DejaVuSerif-Bold', 10)
    title_line1 = 'РЕЕСТР ФАКТОВ ОКАЗАНИЯ УСЛУГ (ПЕРВИЧНЫЙ УЧЕТНЫЙ ДОКУМЕНТ)'

    # Вычисляем ширину текста для центрирования
    text_width_1 = canvas.stringWidth(title_line1, 'DejaVuSerif-Bold', 10)

    # Заголовок начинается ниже логотипа (логотип заканчивается на page_height - 80)
    canvas.drawString(x=(page_width - text_width_1) / 2, y=page_height - 95, text=title_line1)

    # Дата и получатель услуг на одной строке (с жирными датами и заказчиком)
    y_position_header = page_height - 120

    # Левая часть: "[дата оказания услуг] ... год"
    date_text = f'<font name="DejaVuSerif-Bold">{date_str} год</font>'
    p_date = Paragraph(date_text, ParagraphStyle(name='Date', fontName='DejaVuSerif', fontSize=9, alignment=0))
    _, h_date = p_date.wrap(page_width - 80, page_height)
    p_date.drawOn(canvas, 40, y_position_header - h_date + 9)

    # Правая часть: "[город], Получатель услуг: [заказчик]"
    customer_text = f'<font name="DejaVuSerif">{city}, </font>Получатель услуг: <font name="DejaVuSerif-Bold">{customer}</font>'
    p_customer = Paragraph(customer_text, ParagraphStyle(name='Customer', fontName='DejaVuSerif', fontSize=9, alignment=2))
    customer_width = page_width - 80
    _, h_customer = p_customer.wrap(customer_width, page_height)
    p_customer.drawOn(canvas, 40, y_position_header - h_customer + 9)

    # Текст о назначении документа (с автопереносом)
    y_position = page_height - 145
    text1 = 'Настоящий документ является первичным учётным документом, фиксирующим факты оказания услуг, и используется в целях бухгалтерского учёта и расчётов между Сторонами.'
    p1 = Paragraph(text1, ParagraphStyle(name='Text1', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10))
    _, h1 = p1.wrap(page_width - 80, page_height)
    p1.drawOn(canvas, 40, y_position - h1)

    # Текст о том, что документ не является табелем (с автопереносом)
    y_position -= (h1 + 20)
    text2 = 'Документ не является табелем учёта рабочего времени, не подтверждает фактическую занятость физических лиц и не свидетельствует о наличии трудовых отношений.'
    p2 = Paragraph(text2, ParagraphStyle(name='Text2', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10))
    _, h2 = p2.wrap(page_width - 80, page_height)
    p2.drawOn(canvas, 40, y_position - h2)


def build_manager_signature_text(data: dict) -> str | None:
    manager_name = data.get('manager_name') or data.get('manager')
    manager_tg_id = data.get('manager_tg_id')
    if not manager_tg_id:
        return None

    manager_parts = [part for part in [manager_name, f"Telegram ID: {manager_tg_id}"] if part]
    if not manager_parts:
        return None

    manager_info = " ".join(manager_parts)
    return (
        "<font color='#0000FF'>"
        "Формирование документа осуществлено уполномоченным представителем "
        f"Платформы в рамках администрирования информационной системы: {manager_info}"
        "</font>"
    )


class PdfGenerator:
    def __init__(self):
        self.page_width, self.page_height = A4

    async def generate_pdf_balance_report(self, workers):
        """PDF-отчёт: баланс начислений исполнителей с ненулевым балансом."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        style_title = ParagraphStyle(name='TitleStyle', fontName='DejaVuSerif-Bold', fontSize=12, alignment=TA_CENTER)
        title = Paragraph('БАЛАНС НАЧИСЛЕНИЙ ИСПОЛНИТЕЛЕЙ', style_title)
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        table_data = [['№', 'Ф.И.О.', 'Баланс (₽)']]
        total = 0.0
        for idx, w in enumerate(workers, 1):
            balance_val = w.get('balance_val', 0)
            total += balance_val
            table_data.append([str(idx), w['fio'], w['balance']])

        table_data.append(['', 'ИТОГО:', f"{total:,.2f}"])

        col_widths = [30, 360, 110]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'DejaVuSerif-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ]))
        elements.append(table)

        moscow_tz = pytz.timezone('Europe/Moscow')
        current_datetime = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M:%S')
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(StampFlowable(current_datetime))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_pdf_all_workers(self, data):
        buffer = BytesIO()

        # Альбомный A4: 842 x 595 pt, usable width = 842 - 60 = 782 pt
        page_size = landscape(A4)
        margin = 30

        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=30,
            bottomMargin=40,
        )

        elements = []

        style_title = ParagraphStyle(
            name='TitleStyle',
            fontName='DejaVuSerif-Bold',
            fontSize=13,
            alignment=TA_CENTER,
            spaceAfter=6,
        )
        current_date = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M')
        title = Paragraph(f'СПИСОК ИСПОЛНИТЕЛЕЙ (НПД)', style_title)
        subtitle = Paragraph(
            f'Сформирован: {current_date} (МСК)',
            ParagraphStyle(name='SubTitle', fontName='DejaVuSerif', fontSize=8, alignment=TA_CENTER),
        )
        elements.append(title)
        elements.append(subtitle)
        elements.append(Spacer(1, 0.15 * inch))

        sorted_workers = sorted(data['workers'], key=lambda w: w['fio'])
        table_data = [[
            '№',
            'Ф.И.О.',
            'Номер телефона',
            'Реальное Ф.И.О.',
            'Реальный номер',
            'Telegram ID',
            'Max ID',
            'Рейтинг',
            'Локация',
            'WEB IP',
        ]]

        for idx, worker in enumerate(sorted_workers, 1):
            table_data.append(
                [
                    idx,
                    worker['fio'],
                    worker['phone_number'],
                    worker['real_fio'],
                    worker['real_phone_number'],
                    worker['tg_id'],
                    worker.get('max_id', 0),
                    worker['rating'],
                    worker['city'],
                    worker.get('web_ip', '—'),
                ]
            )

        for row in table_data[1:]:
            row[1] = wrap_text(row[1], 22)
            row[3] = wrap_text(row[3], 22)
            row[8] = wrap_text(row[8], 13)

        # Суммарная ширина = 782 pt (usable landscape A4 с отступами 30pt)
        col_widths = [22, 110, 78, 110, 78, 78, 52, 68, 82, 104]

        header_color = colors.HexColor('#1a3c6e')
        row_even = colors.HexColor('#dce9f7')
        row_odd = colors.white

        styles = [
            # Шрифт
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.5),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # Данные
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # №
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),      # Ф.И.О.
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),    # Телефон
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),      # Реальное Ф.И.О.
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),    # Реальный номер
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),    # Telegram ID
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),    # Max ID
            ('ALIGN', (7, 1), (7, -1), 'CENTER'),    # Рейтинг
            ('ALIGN', (8, 1), (8, -1), 'LEFT'),      # Локация
            ('ALIGN', (9, 1), (9, -1), 'CENTER'),    # WEB IP
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Сетка
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#7a9cbf')),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, header_color),
            # Чередование строк
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_odd, row_even]),
        ]

        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle(styles))

        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_pdf_for_foreman(self, data):
        page_height = A4[1]
        page_width = A4[0]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=20,
            bottomMargin=20
        )

        elements = []

        # Spacer для первой страницы (компенсирует место для логотипа и заголовков)
        elements.append(Spacer(1, 190))

        # Формирование таблицы согласно ТЗ (такая же как финальная, но без заполненных единиц)
        table_data = [[
            '№\nп/п',
            'Идентификационные данные\nлица, допущенного на объект\nПолучателя услуг (в целях\nпропускного режима)',
            'Вид оказанной\nуслуги',
            'Временной интервал\nдопуска на объект (в\nрамках оказания\nуслуг) *',
            'Условные\nединицы\nобъёма\nоказанных\nуслуг'
        ]]

        sorted_workers = sorted(
            data['workers'],
            key=lambda w: w['FullName']
        )

        for idx, worker in enumerate(sorted_workers, 1):
            # Парсим FullName для разделения на части, если нужно
            # Если в данных есть отдельные поля, используем их, иначе используем FullName
            if 'position' in worker:
                position = worker['position']
            else:
                position = ''

            if 'start_shift' in data and 'end_shift' in data:
                time_interval = f"{data['start_shift']} – {data['end_shift']}"
            else:
                time_interval = ''

            table_data.append([
                idx,
                worker['FullName'],
                position,
                time_interval,
                ''  # Пустое поле для единиц
            ])

        for row in table_data[1:]:
            row[1] = wrap_text(text=row[1], width=27)
            if row[2]:  # Если есть должность
                row[2] = wrap_text(text=row[2], width=25)

        # Итоговая строка с объединенными ячейками
        table_data.append(['Подтверждённый объем оказанных услуг:', '', '', '', ''])

        # Ширина колонок
        col_widths = [40, 160, 120, 120, 75]

        # Создаем таблицу
        table = Table(table_data, colWidths=col_widths)
        styles = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            # Рисуем границы для всех ячеек кроме последней строки
            ('BOX', (0, 0), (-1, -2), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -2), 1, colors.black),
            # Стили для итоговой строки
            ('SPAN', (0, -1), (3, -1)),  # Объединяем первые 4 колонки
            ('FONTNAME', (0, -1), (3, -1), 'DejaVuSerif-Bold'),
            ('ALIGN', (0, -1), (3, -1), 'RIGHT'),  # Выравнивание по правому краю
            # Рисуем только верхнюю и правую границу для объединенной ячейки
            ('LINEABOVE', (0, -1), (3, -1), 1, colors.black),
            ('LINEAFTER', (3, -1), (3, -1), 1, colors.black),
            # Рисуем все границы для последней ячейки (с цифрой)
            ('BOX', (4, -1), (4, -1), 1, colors.black),
        ])
        table.setStyle(styles)

        elements.append(table)
        elements.append(Spacer(1, 10))

        # Примечание о временном интервале
        elements.append(
            Paragraph(
                "*Временной интервал допуска на объект указывается исключительно в целях пропускного режима и фиксации факта допуска и не является показателем рабочего времени.",
                ParagraphStyle(name='Note', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10)
            )
        )
        elements.append(Spacer(1, 15))


        # Добавляем отступ перед печатью
        elements.append(Spacer(1, 10))

        # Получаем текущее время для блока формирования (печати)
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_datetime = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M:%S')

        # Добавляем печать как элемент документа (будет на последней странице)
        elements.append(StampFlowable(current_datetime))

        # Callback функция для первой страницы
        callback_function_first = partial(
            on_first_page,
            page_height=page_height,
            page_width=page_width,
            date_str=data['date'],
            city=data['city'],
            customer=data['organization']
        )

        doc.build(elements, onFirstPage=callback_function_first, onLaterPages=on_later_pages)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_pdf_end_shift(self, data):
        page_height = A4[1]
        page_width = A4[0]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=20,
            bottomMargin=20
        )

        elements = []

        # Spacer для первой страницы (компенсирует место для логотипа и заголовков)
        elements.append(Spacer(1, 190))

        # Формирование таблицы согласно ТЗ
        table_data = [[
            '№\nп/п',
            'Идентификационные данные\nлица, допущенного на объект\nПолучателя услуг (в целях\nпропускного режима)',
            'Вид оказанной\nуслуги',
            'Временной интервал\nдопуска на объект (в\nрамках оказания\nуслуг) *',
            'Условные\nединицы\nобъёма\nоказанных\nуслуг'
        ]]
        total_hours = []

        sorted_workers = sorted(
            data['workers'],
            key=lambda w: (w['last_name'], w['first_name'], w['middle_name'])
        )

        for idx, worker in enumerate(sorted_workers, 1):
            total_hours.append(worker['hours'])
            table_data.append([
                idx,
                f"{worker['last_name']} {worker['first_name']} {worker['middle_name']}",
                worker['position'],
                f"{data['start_shift']} – {data['end_shift']}",
                worker['hours']
            ])

        for row in table_data[1:]:
            row[1] = wrap_text(text=row[1], width=27)
            row[2] = wrap_text(text=row[2], width=20)

        # Итоговая строка с объединенными ячейками (убираем 5 ячеек, делаем одну с жирным текстом)
        total_sum = sum(map(lambda x: Decimal(x.replace(',', '.')), total_hours))
        if total_sum % 1 == 0:
            formatted_sum = str(int(total_sum))
        else:
            formatted_sum = format(total_sum, 'f').rstrip('0').replace('.', ',')
        # Используем SPAN для объединения первых 4 колонок
        table_data.append(['Подтверждённый объем оказанных услуг:', '', '', '', formatted_sum])

        # Ширина колонок
        col_widths = [40, 160, 120, 120, 75]

        # Создаем таблицу
        table = Table(table_data, colWidths=col_widths)
        styles = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            # Рисуем границы для всех ячеек кроме последней строки
            ('BOX', (0, 0), (-1, -2), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -2), 1, colors.black),
            # Стили для итоговой строки
            ('SPAN', (0, -1), (3, -1)),  # Объединяем первые 4 колонки
            ('FONTNAME', (0, -1), (3, -1), 'DejaVuSerif-Bold'),
            ('ALIGN', (0, -1), (3, -1), 'RIGHT'),  # Выравнивание по правому краю
            ('FONTNAME', (4, -1), (4, -1), 'DejaVuSerif-Bold'),
            # Рисуем только верхнюю и правую границу для объединенной ячейки
            ('LINEABOVE', (0, -1), (3, -1), 1, colors.black),
            ('LINEAFTER', (3, -1), (3, -1), 1, colors.black),
            # Рисуем все границы для последней ячейки (с цифрой)
            ('BOX', (4, -1), (4, -1), 1, colors.black),
        ])
        table.setStyle(styles)

        elements.append(table)
        elements.append(Spacer(1, 10))

        # Примечание о временном интервале
        elements.append(
            Paragraph(
                "*Временной интервал допуска на объект указывается исключительно в целях пропускного режима и фиксации факта допуска и не является показателем рабочего времени.",
                ParagraphStyle(name='Note', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10)
            )
        )
        elements.append(Spacer(1, 15))

        # Информация о неприступивших работниках (если есть)
        if data.get('bad_workers'):
            bad_workers_text = f"<font name='DejaVuSerif-Bold'>По указанным заявкам согласие на оказание услуг было зафиксировано в системе, однако фактическое оказание услуг в соответствующий период не осуществлялось. Факт оказания услуг отсутствует:</font> {', '.join(data['bad_workers'])}"
            elements.append(
                Paragraph(
                    bad_workers_text,
                    ParagraphStyle(name='BadWorkers', fontName='DejaVuSerif', fontSize=9, alignment=0, leading=12)
                )
            )
            elements.append(Spacer(1, 10))

        # Информация о лишних исполнителях (EXTRA) - если есть
        if data.get('extra_workers'):
            extra_workers_text = f"Данные исполнители вышли на заказ, но оказались сверх лимита заявки, были отправлены домой по техническим причинам Платформы: {', '.join(data['extra_workers'])}"
            elements.append(
                Paragraph(
                    extra_workers_text,
                    ParagraphStyle(name='ExtraWorkers', fontName='DejaVuSerif', fontSize=9, alignment=0, leading=12)
                )
            )
            elements.append(Spacer(1, 10))

        # Текст о формировании документа представителем (синий цвет)
        if data.get('customer_admin'):
            admin_text = f"<font color='#0000FF'>Подтверждение осуществлено уполномоченным представителем Получателя услуг исключительно в части фиксации факта оказания услуг: {data['customer_admin']}</font>"
            elements.append(
                Paragraph(
                    admin_text,
                    ParagraphStyle(name='AdminText', fontName='DejaVuSerif', fontSize=9, alignment=0, leading=12)
                )
            )
            elements.append(Spacer(1, 10))

        # Информация о том, кто сформировал документ
        else:
            formed_text = build_manager_signature_text(data)
            if formed_text:
                elements.append(
                    Paragraph(
                        formed_text,
                        ParagraphStyle(name='FormedText', fontName='DejaVuSerif', fontSize=9, alignment=0, leading=12)
                    )
                )
                elements.append(Spacer(1, 10))

        # Добавляем отступ перед печатью
        elements.append(Spacer(1, 10))

        # Получаем текущее время для блока формирования (печати)
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_datetime = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M:%S')

        # Добавляем печать как элемент документа (будет на последней странице)
        elements.append(StampFlowable(current_datetime))

        # Callback функция для первой страницы
        callback_function_first = partial(
            on_first_page,
            page_height=page_height,
            page_width=page_width,
            date_str=data['date'],
            city=data['city'],
            customer=data['organization']
        )

        doc.build(elements, onFirstPage=callback_function_first, onLaterPages=on_later_pages)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_pdf_start_shift(self, data):
        page_height = A4[1]
        page_width = A4[0]

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=20,
            bottomMargin=20
        )

        elements = []

        # Spacer для первой страницы (компенсирует место для логотипа и заголовков)
        elements.append(Spacer(1, 190))

        # Формирование таблицы согласно ТЗ
        table_data = [[
            '№\nп/п',
            'Идентификационные данные\nлица, допущенного на объект\nПолучателя услуг (в целях\nпропускного режима)',
            'Вид оказанной\nуслуги',
            'Временной интервал\nдопуска на объект (в\nрамках оказания\nуслуг) *',
            'Условные\nединицы\nобъёма\nоказанных\nуслуг'
        ]]

        sorted_workers = sorted(
            data['workers'],
            key=lambda w: (w['last_name'], w['first_name'], w['middle_name'])
        )

        for idx, worker in enumerate(sorted_workers, 1):
            table_data.append([
                idx,
                f"{worker['last_name']} {worker['first_name']} {worker['middle_name']}",
                worker['position'],
                f"{data['start_shift']} – {data['end_shift']}",
                ''
            ])

        for row in table_data[1:]:
            row[1] = wrap_text(text=row[1], width=27)
            row[2] = wrap_text(text=row[2], width=20)

        # Итоговая строка с объединенными ячейками (убираем 5 ячеек, делаем одну с жирным текстом)
        table_data.append(['Подтверждённый объем оказанных услуг:', '', '', '', ''])

        # Ширина колонок
        col_widths = [40, 160, 120, 120, 75]

        # Создаем таблицу
        table = Table(table_data, colWidths=col_widths)
        styles = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            # Рисуем границы для всех ячеек кроме последней строки
            ('BOX', (0, 0), (-1, -2), 1, colors.black),
            ('INNERGRID', (0, 0), (-1, -2), 1, colors.black),
            # Стили для итоговой строки
            ('SPAN', (0, -1), (3, -1)),  # Объединяем первые 4 колонки
            ('FONTNAME', (0, -1), (0, -1), 'DejaVuSerif-Bold'),
            ('ALIGN', (0, -1), (0, -1), 'RIGHT'),  # Выравнивание по правому краю
            # Рисуем только верхнюю и правую границу для объединенной ячейки
            ('LINEABOVE', (0, -1), (3, -1), 1, colors.black),
            ('LINEAFTER', (3, -1), (3, -1), 1, colors.black),
            # Рисуем все границы для последней ячейки (пустая)
            ('BOX', (4, -1), (4, -1), 1, colors.black),
        ])
        table.setStyle(styles)

        elements.append(table)
        elements.append(Spacer(1, 10))

        # Примечание о временном интервале
        elements.append(
            Paragraph(
                "*Временной интервал допуска на объект указывается исключительно в целях пропускного режима и фиксации факта допуска и не является показателем рабочего времени.",
                ParagraphStyle(name='Note', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10)
            )
        )
        elements.append(Spacer(1, 15))

        # Текст о формировании документа представителем (синий цвет)
        manager_text = build_manager_signature_text(data)
        if manager_text:
            elements.append(
                Paragraph(
                    manager_text,
                    ParagraphStyle(name='ManagerText', fontName='DejaVuSerif', fontSize=9, alignment=0, leading=12)
                )
            )
            elements.append(Spacer(1, 10))

        # Добавляем отступ перед печатью
        elements.append(Spacer(1, 10))

        # Получаем текущее время для блока формирования (печати)
        moscow_tz = pytz.timezone('Europe/Moscow')
        current_datetime = datetime.now(moscow_tz).strftime('%d.%m.%Y %H:%M:%S')

        # Добавляем печать как элемент документа (будет на последней странице)
        elements.append(StampFlowable(current_datetime))

        # Callback функция для первой страницы
        callback_function_first = partial(
            on_first_page,
            page_height=page_height,
            page_width=page_width,
            date_str=data['date'],
            city=data['city'],
            customer=data['organization']
        )

        doc.build(elements, onFirstPage=callback_function_first, onLaterPages=on_later_pages)
        buffer.seek(0)
        return buffer.getvalue()
