from database import (
    OrderWorkerArchive, OrderArchive,
    DataForSecurity, async_session
)
from sqlalchemy.orm import joinedload
from sqlalchemy import func, select
from datetime import datetime
from functools import partial
from decimal import Decimal
import decimal
from typing import List
from io import BytesIO
import os

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.lib.colors import grey, white, yellow
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import ParagraphStyle

from .tools import wrap_text, VerticalText
from reportlab.platypus.flowables import Flowable


def difference_is_more_than_36_days(
        start_date: str,
        end_date: str
) -> bool:
    if (datetime.strptime(end_date, "%d.%m.%Y").date() - datetime.strptime(start_date, "%d.%m.%Y").date()).days > 36:
        return True
    return False


def is_weekend(
        date: str
) -> bool:
    date_obj = datetime.strptime(date, '%d.%m.%Y')
    return date_obj.weekday() >= 5


def anonymize_name(last_name: str, first_name: str, middle_name: str) -> str:
    """
    Обезличивает ФИО: первые три буквы фамилии + звездочки + последние 2 буквы фамилии + инициалы
    Пример: Иванов А.В. -> Ива*ов А.В.
    """
    if len(last_name) <= 5:
        # Если фамилия короткая, просто добавляем одну звездочку между 3 и 2 символами
        anonymized = last_name[:3] + '*' + last_name[-2:]
    else:
        # Для длинных фамилий - количество звездочек равно количеству скрытых букв
        middle_count = len(last_name) - 5  # 3 первых + 2 последних = 5
        anonymized = last_name[:3] + '*' * middle_count + last_name[-2:]

    first_initial = first_name[0] + '.' if first_name else ''
    middle_initial = middle_name[0] + '.' if middle_name else ''

    return f"{anonymized} {first_initial}{middle_initial}"


def format_number(num: Decimal) -> str:
    """
    Форматирует число: целые без дробной части, дробные с запятой
    Пример: 56.0 -> "56", 111.5 -> "111,5"
    """
    if num == int(num):
        return str(int(num))
    else:
        return str(num).replace('.', ',')


async def get_workers_data_for_pdf(
        customer_id: int,
        start_date_str: str,
        end_date_str: str,
        dates: List[str]
):
    async with async_session() as session:
        start_date = func.to_date(start_date_str, 'DD.MM.YYYY')
        end_date = func.to_date(end_date_str, 'DD.MM.YYYY')

        workers = await session.scalars(
            select(OrderWorkerArchive.worker_id).join(OrderArchive).join(
                DataForSecurity, DataForSecurity.user_id == OrderWorkerArchive.worker_id
            ).where(
                OrderArchive.customer_id == customer_id,
                OrderWorkerArchive.archive_order_id == OrderArchive.id,
                func.to_date(OrderWorkerArchive.date, 'DD.MM.YY').between(start_date, end_date)
            ).order_by(DataForSecurity.last_name.asc())
        )

        table_data = []
        style_data = []
        day_hours = []

        for worker_id in list(dict.fromkeys(workers.all())):
            worker_orders = await session.scalars(
                select(OrderWorkerArchive).join(OrderArchive).options(
                    joinedload(OrderWorkerArchive.archive_order)
                ).where(
                    OrderArchive.customer_id == customer_id,
                    OrderWorkerArchive.worker_id == worker_id,
                    func.to_date(OrderWorkerArchive.date, 'DD.MM.YY').between(
                        start_date, end_date
                    )
                )
            )

            worker_hours = {}
            for order in worker_orders:
                hours = worker_hours.get(order.date)
                if not hours:
                    # Безопасное преобразование часов (может быть 'Л' для EXTRA)
                    try:
                        hours_str = order.worker_hours.replace(',', '.').replace('Л', '0')
                        hours_decimal = Decimal(hours_str)
                        display_hours = hours_str if hours_decimal > Decimal('0') else ''
                    except (ValueError, decimal.InvalidOperation):
                        display_hours = ''

                    worker_hours[order.date] = (
                        display_hours,
                        "д" if order.archive_order.day_shift else "н"
                    )
                else:
                    # Безопасное преобразование для второй смены
                    try:
                        hours_str = order.worker_hours.replace(',', '.').replace('Л', '0')
                        hours_value = Decimal(hours_str)
                        display_hours = order.worker_hours if hours_value > Decimal('0') else ''
                    except (ValueError, decimal.InvalidOperation):
                        display_hours = ''

                    worker_hours[order.date] = [
                        hours, (display_hours,
                                "д" if order.archive_order.day_shift else "н")
                    ]

            table_row = []
            day_hours_row = []

            def append_hours(hrs):
                if hrs[1] == 'д':
                    day_hours_row.append(
                        hrs[0]
                    )
                else:
                    day_hours_row.append('')

            for date in dates:
                hours = worker_hours.get(date, '')
                if isinstance(hours, list):
                    table_row.append(
                        str(sum(map(
                            Decimal, [
                                hours[0][0] if hours[0][0] != '' else '0',
                                hours[1][0] if hours[1][0] != '' else '0'
                            ]
                        )))
                    )
                    if hours[0][1] == 'д':
                        append_hours(hrs=hours[0])
                    if hours[1][1] == 'д':
                        append_hours(hrs=hours[1])
                else:
                    table_row.append(
                        hours[0] if hours != '' else ''
                    )
                    if isinstance(hours, tuple):
                        append_hours(hrs=hours)
                    else:
                        day_hours_row.append(hours)

            table_row_style = [white]
            for date in dates:
                hours = worker_hours.get(date, '')
                if isinstance(hours, list):
                    table_row_style.append(
                        yellow
                    )
                elif hours == '':
                    table_row_style.append(
                        white
                    )
                else:
                    table_row_style.append(
                        (grey if hours[1] == 'н' else white) if hours[0] != '' else white
                    )

            if len(table_row) < 36:
                table_row.extend(['' for _ in range(36 - len(table_row))])
            if len(day_hours_row) < 36:
                day_hours_row.extend(['' for _ in range(36 - len(day_hours_row))])

            worker = await session.scalar(
                select(DataForSecurity).where(
                    DataForSecurity.user_id == worker_id
                )
            )

            # Используем обезличенное имя
            anonymized_name = anonymize_name(worker.last_name, worker.first_name, worker.middle_name)

            table_data.append(
                [anonymized_name, *table_row]
            )
            day_hours.append(
                [anonymized_name, *day_hours_row]
            )
            style_data.append(
                table_row_style
            )
        indices_to_remove = []
        for i, inner_list in enumerate(table_data):
            if all(item == '' for item in inner_list[1:]):
                indices_to_remove.append(i)
        table_data = [inner_list for idx, inner_list in enumerate(table_data) if idx not in indices_to_remove]
        style_data = [inner_list for idx, inner_list in enumerate(style_data) if idx not in indices_to_remove]
        day_hours = [inner_list for idx, inner_list in enumerate(day_hours) if idx not in indices_to_remove]
        return table_data, style_data, day_hours


class StampFlowable(Flowable):
    """Flowable для печати в правом нижнем углу"""
    def __init__(self, current_datetime):
        Flowable.__init__(self)
        self.current_datetime = current_datetime
        self.block_width = 300
        self.block_height = 90

    def draw(self):
        from reportlab.lib import colors

        canvas = self.canv

        # Получаем размеры страницы
        page_width = canvas._pagesize[0]

        # Параметры блока печати
        margin_right = 20
        margin_bottom = 20

        # Позиция блока (правый нижний угол страницы - абсолютная позиция)
        x_position = page_width - self.block_width - margin_right
        y_position = margin_bottom

        # Сохраняем текущее состояние canvas
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
        text_y -= 12
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'информационной системой (программой для ЭВМ)')
        text_y -= 12
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Платформы «Алгоритм Плюс».')

        # Дата и время
        canvas.setFont('DejaVuSerif', 8)
        text_y -= 18
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Дата и время формирования:')
        text_y -= 10
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                f'{self.current_datetime} (MSK)')

        # Последний текст
        canvas.setFont('DejaVuSerif', 7)
        text_y -= 12
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'Данный Документ сформирован без участия и без ручного')
        text_y -= 8
        canvas.drawCentredString(x_position + self.block_width / 2, text_y,
                                'редактирования со стороны физических лиц.')

        # Восстанавливаем состояние canvas
        canvas.restoreState()

    def wrap(self, availWidth, availHeight):
        # Возвращаем размеры блока
        return (self.block_width, self.block_height)


def on_later_pages(canvas, document):
    """Функция для последующих страниц (без заголовков)"""
    pass  # На последующих страницах ничего не рисуем в header


def on_first_page(canvas, document, page_height, page_width, start_date, end_date, customer):
    # Логотип
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        canvas.drawImage(
            logo_path, 40, page_height - 80, width=80, height=80
        )

    # Основной заголовок (центрированный, ниже логотипа)
    canvas.setFont('DejaVuSerif-Bold', 10)
    title_line1 = 'СВЕРКА ВЗАИМНЫХ РАСЧЁТОВ И ПОДТВЕРЖДЕННЫХ ФАКТОВ ОКАЗАНИЯ УСЛУГ ПО ДОГОВОРУ В'
    title_line2 = 'РАМКАХ ИСПОЛНЕНИЯ ЗАЯВОК ЗАКАЗЧИКА'

    # Вычисляем ширину текста для центрирования
    text_width_1 = canvas.stringWidth(title_line1, 'DejaVuSerif-Bold', 10)
    text_width_2 = canvas.stringWidth(title_line2, 'DejaVuSerif-Bold', 10)

    # Заголовок начинается ниже логотипа (логотип заканчивается на page_height - 80)
    canvas.drawString(x=(page_width - text_width_1) / 2, y=page_height - 95, text=title_line1)
    canvas.drawString(x=(page_width - text_width_2) / 2, y=page_height - 110, text=title_line2)

    # Период и получатель услуг на одной строке (с жирными датами и заказчиком)
    y_position_header = page_height - 135

    # Левая часть: "за период [даты]"
    period_text = f'<font name="DejaVuSerif-Bold">за период {start_date} по {end_date}</font>'
    p_period = Paragraph(period_text, ParagraphStyle(name='Period', fontName='DejaVuSerif', fontSize=9, alignment=0))
    _, h_period = p_period.wrap(page_width - 80, page_height)
    p_period.drawOn(canvas, 40, y_position_header - h_period + 9)  # +9 для выравнивания по базовой линии

    # Правая часть: "Получатель услуг: [заказчик]" (выровнено по правому краю с отступом 40)
    customer_text = f'Получатель услуг: <font name="DejaVuSerif-Bold">{customer}</font>'
    p_customer = Paragraph(customer_text, ParagraphStyle(name='Customer', fontName='DejaVuSerif', fontSize=9, alignment=2))  # alignment=2 - правое выравнивание
    customer_width = page_width - 80  # Вся ширина страницы минус отступы слева (40) и справа (40)
    _, h_customer = p_customer.wrap(customer_width, page_height)
    p_customer.drawOn(canvas, 40, y_position_header - h_customer + 9)  # Начинаем с x=40, текст выравнивается вправо

    # Текст о назначении сверки (с автопереносом)
    y_position = page_height - 160
    text1 = 'Настоящая сверка составлена исключительно в целях подтверждения объёма оказанных услуг и взаимных расчётов между Сторонами.'
    p1 = Paragraph(text1, ParagraphStyle(name='Text1', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10))
    _, h1 = p1.wrap(page_width - 80, page_height)
    p1.drawOn(canvas, 40, y_position - h1)

    # Текст о том, что документ не является табелем (с автопереносом)
    y_position -= (h1 + 20)
    text2 = 'Документ не является табелем учёта рабочего времени, не подтверждает фактическую занятость физических лиц и не свидетельствует о наличии трудовых отношений.'
    p2 = Paragraph(text2, ParagraphStyle(name='Text2', fontName='DejaVuSerif', fontSize=8, alignment=0, leading=10))
    _, h2 = p2.wrap(page_width - 80, page_height)
    p2.drawOn(canvas, 40, y_position - h2)


async def create_pdf(
        pdf_data: List[List[str]],
        style_data: List[List[str]],
        day_hours,
        dates: List[str],
        start_date_str: str,
        end_date_str: str,
        customer: str
):
    page_height = 793 * 0.75
    page_width = 1122 * 0.75

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(page_width, page_height),
        leftMargin=5,
        rightMargin=5,
        topMargin=20,  # Обычный отступ для всех страниц
        bottomMargin=5
    )

    elements = []

    # Spacer для первой страницы (компенсирует место для логотипа и заголовков)
    elements.append(Spacer(1, 190))

    # Заголовки таблицы изменены согласно ТЗ
    table_data = [
        ['Обезличенный\nидентификатор\nдопуска на объект', *[VerticalText(date) for date in dates]],
        *pdf_data
    ]

    converted_data = [[row[0]] + [Decimal(str(cell or '0').replace(',', '.')) for cell in row[1:]] for row in table_data[1::]]
    converted_day_hours = [[row[0]] + [Decimal(str(cell or '0').replace(',', '.')) for cell in row[1:]] for row in day_hours]
    if not converted_day_hours or not converted_day_hours[0]:
        raise ValueError("Нет данных для формирования сверки")

    # Суммируем часы по столбцам
    sum_day_hours = ['Д']
    for col_idx in range(1, len(converted_day_hours[0])):
        column_sum = sum(row[col_idx] for row in converted_day_hours)
        sum_day_hours.append(column_sum)

    sum_hours = ['И']
    for col_idx in range(1, len(converted_data[0])):
        column_sum = sum(row[col_idx] for row in converted_data)
        sum_hours.append(column_sum)
    temp_all_sum = sum_hours[1:]
    temp_day_sum = sum_day_hours[1:]

    sum_night_hours = ['Н']
    for index, data in enumerate(temp_all_sum):
        sum_night_hours.append(
            data - temp_day_sum[index]
        )

    # Форматируем числа в итоговых строках
    sum_day_hours_formatted = ['Д'] + [format_number(val) for val in sum_day_hours[1:]]
    sum_night_hours_formatted = ['Н'] + [format_number(val) for val in sum_night_hours[1:]]
    sum_hours_formatted = ['И'] + [format_number(val) for val in sum_hours[1:]]

    table_data.append(sum_day_hours_formatted)
    table_data.append(sum_night_hours_formatted)
    table_data.append(sum_hours_formatted)

    col_widths = [140, 19.4]

    for row in table_data[1:]:
        row[0] = wrap_text(row[0], 22)

    table = Table(table_data, colWidths=col_widths)

    # Базовые стили таблицы
    styles = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#b7ddf2'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),  # Вертикальное выравнивание по центру для заголовка первой колонки
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (1, 1), (-1, -1), 8),
        ('FONTSIZE', (1, -3), (-1, -1), 6),
        ('FONTSIZE', (0, 0), (0, 0), 7),  # Уменьшен шрифт для длинного заголовка
    ])

    # Жирный шрифт и выравнивание по правому краю для букв Д, Н, И в итоговых строках
    styles.add('FONTNAME', (0, -3), (0, -1), 'DejaVuSerif-Bold')
    styles.add('ALIGN', (0, -3), (0, -1), 'RIGHT')

    # Применяем цвета для ячеек согласно новому ТЗ:
    # Черные ячейки для ночных с белым текстом, желтые для суток
    for row_num, row_values in enumerate(style_data):
        for col_num, cell_color in enumerate(row_values):
            if cell_color == yellow:
                # Сутки - желтая ячейка, черный текст
                styles.add('BACKGROUND', (col_num, row_num + 1), (col_num, row_num + 1), yellow)
                styles.add('TEXTCOLOR', (col_num, row_num + 1), (col_num, row_num + 1), '#000000')
            elif cell_color == grey:
                # Ночной период - черная ячейка, белый текст
                styles.add('BACKGROUND', (col_num, row_num + 1), (col_num, row_num + 1), '#000000')
                styles.add('TEXTCOLOR', (col_num, row_num + 1), (col_num, row_num + 1), white)
            elif cell_color == white:
                # Для выходных дней применяем розовый фон только к белым ячейкам (дневные смены)
                date_index = col_num - 1  # col_num в style_data начинается с 0 (первая колонка - white для ФИО)
                if date_index >= 0 and date_index < len(dates) and is_weekend(dates[date_index]):
                    styles.add('BACKGROUND', (col_num, row_num + 1), (col_num, row_num + 1), '#ffe5e0')

    table.setStyle(styles)

    elements.append(table)
    elements.append(Spacer(1, 10))

    # Условные обозначения
    elements.append(
        Paragraph(
            "*- условные обозначения:",
            ParagraphStyle(
                name='NotesTitle', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(Spacer(1, 5))
    elements.append(
        Paragraph(
            "<font name='DejaVuSerif-Bold'>Д</font> – дневной период оказания услуг",
            ParagraphStyle(
                name='NotesText', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(
        Paragraph(
            "<font name='DejaVuSerif-Bold'>Н</font> – ночной период оказания услуг",
            ParagraphStyle(
                name='NotesText', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(
        Paragraph(
            "<font name='DejaVuSerif-Bold'>И</font> – выполненный объём услуг в рамках соответствующего периода оказания услуг",
            ParagraphStyle(
                name='NotesText', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(Spacer(1, 15))

    # ИТОГО ЗА ПЕРИОД
    total_sum = sum(sum_hours[1::])  # sum_hours содержит Decimal значения до форматирования
    total_sum_formatted = format_number(total_sum)
    elements.append(
        Paragraph(
            f"<font name='DejaVuSerif-Bold'>ИТОГО ЗА ПЕРИОД: {total_sum_formatted} единиц</font> измерения объёма оказанных услуг, определяемых условиями",
            ParagraphStyle(
                name='TotalStyle', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(
        Paragraph(
            "Договора (условные единицы: шт., заявки, коробки, метры и иные, в зависимости от предмета",
            ParagraphStyle(
                name='TotalStyle2', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    elements.append(
        Paragraph(
            "оказания услуг).",
            ParagraphStyle(
                name='TotalStyle3', fontName='DejaVuSerif', fontSize=9, alignment=0
            )
        )
    )
    # Небольшой отступ перед печатью
    elements.append(Spacer(1, 10))

    # Получаем текущее время для блока формирования (печати)
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    # Добавляем печать как элемент документа
    elements.append(StampFlowable(current_datetime))

    # Callback функции для первой и последующих страниц
    callback_function_first = partial(
        on_first_page,
        page_height=page_height,
        page_width=page_width,
        start_date=start_date_str,
        end_date=end_date_str,
        customer=customer
    )

    doc.build(elements, onFirstPage=callback_function_first, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer.getvalue()


async def create_collation(
        start_date_str: str,
        end_date_str: str,
        customer_id: int,
        customer: str
):
    start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
    end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()

    async with async_session() as session:
        orders = await session.scalars(
            select(OrderArchive).where(
                OrderArchive.customer_id == customer_id,
                func.to_date(OrderArchive.date, 'DD.MM.YY').between(
                    start_date, end_date
                )
            )
        )

        sorted_orders = sorted(
            orders,
            key=lambda order: datetime.strptime(
                f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
                '%d.%m.%Y %H:%M'
            )
        )

        dates = list(
            dict.fromkeys(
                [order.date for order in sorted_orders]
            )
        )

        pdf_data = await get_workers_data_for_pdf(
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            customer_id=customer_id,
            dates=dates
        )

        return await create_pdf(
            pdf_data=pdf_data[0],
            style_data=pdf_data[1],
            day_hours=pdf_data[2],
            dates=dates,
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            customer=customer
        )
