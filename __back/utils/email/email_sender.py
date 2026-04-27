import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional
from datetime import datetime

from config_reader import config
from utils.day_by_date import get_day_of_week_by_date


def create_email_body(order_date: str, shift_name: str) -> str:
    """Создает тело письма согласно шаблону"""
    day_of_week = get_day_of_week_by_date(order_date).upper()
    shift_type = 'ДНЕВНОЙ' if shift_name == 'Д' else 'НОЧНОЙ'
    return f"""Уважаемые коллеги!

В рамках ранее размещённой Заявки направляем Реестр лиц, допущенных для оказания услуг на объект Получателя услуг в указанный период оказания услуг {day_of_week} {order_date}  Период оказания услуг: {shift_type}

Направляемый документ является информационным реестром и предоставляется исключительно в целях:
 • организации пропускного режима;
 • обеспечения допуска указанных лиц на объект Получателя услуг.

📎 Реестр лиц, допущенных для оказания услуг, прилагается в формате PDF.

Документ не является:
 • табелем учёта рабочего времени;
 • подтверждением занятости;
 • назначением графиков, обязанностей либо элементов трудового режима;
 • подтверждением трудовых отношений.

Все указанные в Реестре лица являются пользователями Платформы «Алгоритм Плюс»,
самостоятельно и добровольно выразившими готовность приступить к оказанию услуг по соответствующей Заявке.

⸻

❗ Порядок действий при невозможности допуска

В случае если по соображениям безопасности либо внутренним правилам Получателя услуг какое-либо лицо, указанное в Реестре, не может быть допущено на объект,
просим обязательно уведомить Платформу заблаговременно,
не позднее чем за 12 часов до начала заявленного периода оказания услуг.

Уведомление необходимо направить по электронной почте:
igor.avsievichalgoritmplus@mail.ru
(Исполнительный директор Платформы «Алгоритм Плюс»).

⸻

⚠️ Важно

В случае отсутствия указанного предварительного уведомления и при недопуске лица, включённого в Реестр, на посту охраны по причинам, не зависящим от Исполнителя и Платформы,
по соответствующей Заявке фиксируется факт оказания услуг в полном объёме
и производится расчёт в соответствии с условиями Договора Получателя услуг.

⸻

С уважением,
Платформа «Алгоритм Плюс»

⸻

ℹ️ Настоящий адрес электронной почты используется исключительно для автоматической передачи информационных материалов.
Все вопросы и дальнейшее взаимодействие осуществляются по контактам, указанным в Договоре
"""


def create_email_subject(order_date: str, shift_name: str, work_cycle: int) -> str:
    """Создает тему письма в зависимости от типа (первичное или скорректированное)"""
    if work_cycle == 1:
        return f"Информация для организации допуска на объект по Заявке от {order_date} ({shift_name})"
    else:
        return f"❗ СКОРРЕКТИРОВАНО: Информация для организации допуска на объект по Заявке от {order_date} ({shift_name})"


async def send_worker_list_email(
    recipient_emails: List[str],
    order_date: str,
    shift_name: str,
    work_cycle: int,
    pdf_bytes: bytes,
    pdf_filename: str
) -> tuple[bool, Optional[str]]:
    """
    Отправляет PDF-список самозанятых на указанные email адреса

    Args:
        recipient_emails: Список email адресов получателей
        order_date: Дата заявки в формате DD.MM.YYYY
        shift_name: Название смены (Д или Н)
        work_cycle: Номер рабочего цикла (1 = первичное, >1 = скорректированное)
        pdf_bytes: Содержимое PDF файла в байтах
        pdf_filename: Имя файла PDF

    Returns:
        tuple: (успех: bool, сообщение об ошибке: Optional[str])
    """
    try:
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = config.smtp_email.get_secret_value()
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = create_email_subject(order_date, shift_name, work_cycle)

        # Добавляем тело письма
        body = create_email_body(order_date, shift_name)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Прикрепляем PDF файл
        pdf_part = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(pdf_part)

        # Подключаемся к SMTP серверу и отправляем
        smtp_host = config.smtp_host.get_secret_value()
        smtp_port = int(config.smtp_port.get_secret_value())
        smtp_email = config.smtp_email.get_secret_value()
        smtp_password = config.smtp_password.get_secret_value()

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)

        return True, None

    except Exception as e:
        error_msg = f"Ошибка отправки email: {str(e)}"
        logging.exception(error_msg)
        return False, error_msg


def parse_email_addresses(email_string: str) -> List[str]:
    """
    Парсит строку с email адресами, разделенными точкой с запятой

    Args:
        email_string: Строка с email адресами, разделенными ';'

    Returns:
        List[str]: Список валидных email адресов
    """
    if not email_string:
        return []

    emails = [email.strip() for email in email_string.split(';')]
    # Фильтруем пустые строки
    emails = [email for email in emails if email]

    return emails


def validate_email(email: str) -> bool:
    """
    Простая валидация email адреса

    Args:
        email: Email адрес для проверки

    Returns:
        bool: True если email валиден, False иначе
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_email_list(email_string: str) -> tuple[bool, str]:
    """
    Валидирует список email адресов

    Args:
        email_string: Строка с email адресами, разделенными ';'

    Returns:
        tuple: (валиден: bool, сообщение: str)
    """
    emails = parse_email_addresses(email_string)

    if not emails:
        return False, "Список email адресов пуст"

    invalid_emails = []
    for email in emails:
        if not validate_email(email):
            invalid_emails.append(email)

    if invalid_emails:
        return False, f"Некорректные email адреса: {', '.join(invalid_emails)}"

    return True, "OK"
