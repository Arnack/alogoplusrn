from io import BytesIO
import fitz  # PyMuPDF


def convert_pdf_pages_to_byte_streams(pdf_data):
    """
    Функция принимает бинарные данные PDF и возвращает список изображений в виде байтовых объектов.
    :param pdf_data: bytearray or bytes, содержащие PDF-данные
    :return: list of ByteIO objects (каждый элемент списка соответствует странице PDF)
    """
    images_list = []

    # Открываем PDF с передачей raw binary data
    doc = fitz.open(
        stream=pdf_data,
        filetype='pdf'
    )

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)

        # Сохраняем страницу в формате PNG
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(300 / 72, 300 / 72)
        )  # Устанавливаем DPI

        # Создаем ByteIO для каждого изображения
        image_io = BytesIO()
        png_bytes = pixmap.tobytes("png")  # Прямо получаем байты в нужном формате
        image_io.write(png_bytes)
        image_io.seek(0)

        # Возвращаем содержимое ByteIO
        images_list.append(image_io.getvalue())

    return images_list
