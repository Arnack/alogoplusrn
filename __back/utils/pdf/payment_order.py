from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus.flowables import Flowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.paragraph import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from functools import partial
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
    print(f"Предупреждение: не удалось загрузить шрифты DejaVu в payment_order: {e}")


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
        margin_right = 50  # Совпадает с rightMargin документа

        # Рисуем относительно позиции Flowable в документе, а не абсолютно от края страницы
        x_position = page_width - self.block_width - margin_right
        y_position = 0

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


def on_later_pages(_canvas, _document):
    """Функция для последующих страниц (без дополнительных элементов)"""
    pass


def on_first_page(canvas, _document, page_height):
    # Рисуем только логотип, остальное будет в elements
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        canvas.drawImage(
            logo_path, 50, page_height - 155, width=150, height=150
        )


def create_payment_order_pdf(
        pdf_data: dict,
        admin_mode: bool = False
):
    from datetime import datetime

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

    # Формирование таблицы
    table_data = [['№\nп/п', 'ИНН исполнителя\n(НПД)', 'ФИО исполнителя', 'Вознаграждение за\nоказанные услуги, руб.']]

    sorted_workers = sorted(
        pdf_data['workers'],
        key=lambda w: w[1]
    )

    for idx, worker in enumerate(sorted_workers, 1):
        table_data.append([
            idx,
            *worker,
        ])

    for row in table_data[1:]:
        wrapped_fio = wrap_text(row[2], 26)
        row[2] = wrapped_fio

    column_4 = []
    for row in table_data[1:]:
        column_4.append(row[3])
    table_data.append(['', '', 'Итого сумма вознаграждений за оказанные услуги:', sum(column_4)])

    # Ширина колонок (шире для лучшего отображения)
    col_widths = [40, 120, 180, 130]

    # Создаем таблицу
    table = Table(table_data, colWidths=col_widths)
    styles = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # цвет фона заголовка
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Горизонтальное выравнивание по центру
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Вертикальное выравнивание по центру
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),  # цвет текста заголовка
        ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSerif-Bold'),  # шрифт заголовков
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # отступ снизу строки заголовка
        ('GRID', (0, 0), (-1, -2), 1, '#000000'),  # сетка вокруг всей таблицы
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
        ('FONTNAME', (2, -1), (2, -1), 'DejaVuSerif-Bold'),
        ('ALIGN', (2, -1), (2, -1), 'RIGHT'),
        ('FONTNAME', (-1, 1), (-1, -1), 'DejaVuSerif-Bold'),
        ('LINEBEFORE', (3, -1), (4, -1), 1, colors.black),
        ('LINEAFTER', (3, -1), (3, -1), 1, colors.black),
        ('LINEBELOW', (3, -1), (4, -1), 1, colors.black),
    ])
    table.setStyle(styles)

    elements.append(Spacer(1, 160))

    # Добавляем заголовок документа
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='DejaVuSerif-Bold',
        fontSize=11,
        alignment=1,  # По центру
        spaceAfter=20
    )
    elements.append(
        Paragraph(
            'ПЛАТЁЖНОЕ ПОРУЧЕНИЕ НА ВЫПЛАТУ ВОЗНАГРАЖДЕНИЙ ЗА ОКАЗАННЫЕ УСЛУГИ',
            title_style
        )
    )

    # Добавляем информацию о дате, получателе и периоде в виде таблицы для правильного выравнивания
    customer_name = pdf_data['customer'] if not admin_mode else 'Платформа_«Алгоритм_плюс»'

    info_table_data = [
        [f"{pdf_data['date']} год", Paragraph(f"{pdf_data['city']}, Получатель услуг: <font name='DejaVuSerif-Bold'>{customer_name}</font>", ParagraphStyle(name='CustomerText', fontName='DejaVuSerif', fontSize=9, alignment=2))],
        [Paragraph(f"<font name='DejaVuSerif-Bold'>{pdf_data['shift']}</font> период оказания услуг", ParagraphStyle(name='ShiftText', fontName='DejaVuSerif', fontSize=9, alignment=0)), ""]
    ]

    info_table = Table(info_table_data, colWidths=[250, 250])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSerif'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 15))

    elements.append(table)

    bad_workers = pdf_data.get('bad_workers', [])
    if bad_workers:
        elements.append(Spacer(1, 10))
        elements.append(
            Paragraph(
                text=(
                    'В отношении указанных заявок применяются положения договора и правил Платформы, регулирующие расчёты при отсутствии факта оказания услуг:'
                ),
                style=ParagraphStyle(
                    name='TitleStyle', fontName='DejaVuSerif-Bold', fontSize=10, alignment=0, spaceAfter=5
                )
            )
        )
        elements.append(
            Paragraph(
                text=', '.join(bad_workers),
                style=ParagraphStyle(
                    name='TitleStyle', fontName='DejaVuSerif', fontSize=10, alignment=0
                )
            )
        )

    # Добавляем отступ перед печатью (увеличенный, чтобы печать не перекрывала таблицу)
    elements.append(Spacer(1, 120))

    # Получаем текущую дату и время
    current_datetime = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    # Добавляем печать как элемент документа (будет на последней странице)
    elements.append(StampFlowable(current_datetime))

    callback_function_first = partial(
        on_first_page,
        page_height=A4[1]
    )

    # Используем onLaterPages для пустых последующих страниц
    doc.build(elements, onFirstPage=callback_function_first, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer.getvalue()
