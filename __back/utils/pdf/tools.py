from reportlab.platypus.flowables import Flowable


def wrap_text(text, width):
    """Разбивает строку на фрагменты с использованием пробелов,
    чтобы длина фрагмента была меньше указанной ширины."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > width:
            lines.append(current_line.strip())
            current_line = word
        else:
            current_line += " " + word

    if current_line:
        lines.append(current_line.strip())

    return "\n".join(lines)


class VerticalText(Flowable):
    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        canvas = self.canv
        font_name = canvas._fontname
        font_size = canvas._fontsize

        str_width = canvas.stringWidth(self.text, font_name, font_size)

        canvas.saveState()

        canvas.rotate(270)

        canvas.translate(-str_width, 0)

        canvas.drawString(0, 0, self.text)

        canvas.restoreState()

    def wrap(self, availWidth, availHeight):
        canvas = self.canv
        font_name = canvas._fontname
        font_size = canvas._fontsize
        leading = canvas._leading

        str_width = canvas.stringWidth(self.text, font_name, font_size)

        req_width = leading
        req_height = str_width

        return req_width, req_height


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
