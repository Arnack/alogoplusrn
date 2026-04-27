from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Spacer
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
from typing import List
from datetime import datetime
import os

from database import User
import database as db


# Регистрация шрифтов для поддержки кириллицы
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))

    bold_font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif-Bold.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', bold_font_path))
except Exception as e:
    print(f"Предупреждение: не удалось загрузить шрифты DejaVu в workers_list: {e}")


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
        margin_right = 30
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


def format_phone_number(phone: str) -> str:
    """
    Форматирует номер телефона в формат +7XXXXXXXXXX

    Args:
        phone: Номер телефона (в формате +7XXXXXXXXXX)

    Returns:
        Отформатированный номер или 'Телефон не указан'
    """
    if not phone or len(phone) != 12 or not phone.startswith('+7'):
        return 'Телефон не указан'

    return phone


async def generate_workers_pdf(
        workers: List[User],
        city: str,
        workers_ip: dict = None,
) -> BytesIO:
    """
    Генерирует PDF со списком самозанятых из города

    Args:
        workers: Список самозанятых (уже отсортированный по алфавиту)
        city: Название города
        workers_ip: Словарь {user_id: ip_str} с последними WEB IP (опционально)

    Returns:
        BytesIO объект с PDF файлом
    """
    if workers_ip is None:
        workers_ip = {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
    )
    elements = []

    # Заголовок
    style_title = ParagraphStyle(
        name='TitleStyle',
        fontName='DejaVuSerif-Bold',
        fontSize=14,
        alignment=TA_CENTER
    )
    title = Paragraph(f'СПИСОК ИСПОЛНИТЕЛЕЙ (НПД)<br/>{city.upper()}', style_title)
    elements.append(title)
    elements.append(Spacer(1, 0.3 * inch))

    # Данные для таблицы
    table_data = [['Ф.И.О.', 'Телефон', 'Реальный телефон', 'Max ID', 'WEB IP']]

    for worker in workers:
        # Формируем полное ФИО
        full_name = f'{worker.last_name} {worker.first_name}'
        if worker.middle_name:
            full_name += f' {worker.middle_name}'

        # Форматируем телефон
        phone = format_phone_number(worker.phone_number)

        # Получаем реальный номер телефона из DataForSecurity
        real_data = await db.get_user_real_data_by_id(user_id=worker.id)
        real_phone = format_phone_number(real_data.phone_number) if real_data and real_data.phone_number else 'Телефон не указан'

        max_id = worker.max_id if worker.max_id else 0

        web_ip = workers_ip.get(worker.id) or '—'

        table_data.append([full_name, phone, real_phone, str(max_id), web_ip])

    # Создаем таблицу: ФИО, Телефон, Реальный телефон, Max ID, WEB IP
    # Суммарная ширина колонок = 6.15" при usable ≈ 6.7" (A4 - margins 50pt*2)
    table = Table(
        table_data,
        colWidths=[2.0 * inch, 1.3 * inch, 1.3 * inch, 0.65 * inch, 0.9 * inch],
    )

    # Стиль таблицы
    table.setStyle(TableStyle([
        # Заголовок
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

        # Данные
        ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))

    elements.append(table)

    # Добавляем отступ перед печатью
    elements.append(Spacer(1, 0.2 * inch))

    # Получаем текущую дату и время
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    # Добавляем печать как элемент документа (будет на последней странице)
    elements.append(StampFlowable(current_datetime))

    # Генерируем PDF
    doc.build(elements)
    buffer.seek(0)

    return buffer
