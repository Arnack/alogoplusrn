from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import Tuple


def is_number(
        number: str
) -> bool:
    try:
        float(number.replace(',', '.'))
        return True
    except ValueError:
        return False


def is_date(
        date: str
) -> bool:
    try:
        datetime.strptime(date, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def validate_number(
        number: str
) -> bool:
    try:
        num = float(number.replace(',', '.'))

        if not Decimal(num) % Decimal('0.5') == 0 or not 0.5 <= num <= 22:
            return False
        else:
            return True

    except ValueError:
        return False


def validate_date(
        date_str: str
) -> Tuple[bool, str]:
    try:
        # Добавляем ведущие нули
        date_parts = date_str.split('.')
        if len(date_parts) != 2 and len(date_parts) != 3:
            pass

        day = int(date_parts[0])
        month = int(date_parts[1])

        # Проверяем наличие года
        year_part = None
        if len(date_parts) == 3:
            year_part = date_parts[2]

            # Обрабатываем двузначный год
            if len(year_part) == 2:
                current_year_full = datetime.now().year
                current_century = str(current_year_full)[:2]
                year_part = f"{current_century}{year_part}"

            year = int(year_part)
        else:
            # Если год не указан, используем текущий год
            year = datetime.now().year

        # Создаем объект даты для проверки валидности
        valid_date = datetime(
            year=year,
            month=month,
            day=day
        )

        return True, valid_date.strftime('%d.%m.%Y')  # Возвращаем строку с датой в нужном формате
    except:
        return False, ""


def luhn_check(
        card_number: str
) -> bool:
    """
        Проверка номера карты с помощью алгоритма Луна
        :param card_number: Номер карты без пробелов, только цифры. Пример: 2202111122223333
        :return: True - карта действительна, False - введена неверно
    """
    # Преобразуем строку номера карты в список целых чисел
    digits = list(map(int, card_number))

    # Удваиваем каждую вторую цифру, начиная с конца списка
    for i in range(len(digits) - 2, -1, -2):
        doubled_digit = digits[i] * 2

        # Если число > 9, уменьшаем его на 9
        if doubled_digit > 9:
            doubled_digit -= 9

        digits[i] = doubled_digit

    # Проверяем сумму всех элементов на деление на 10
    return sum(digits) % 10 == 0


def truncate_decimal(
        number: str,
) -> str:
    """ Оставляет максимум 2 символа после запятой (точки), остальное отсекает """
    parts = number.replace(',', '.').split('.')
    return '.'.join([parts[0], parts[1][:2]]) if len(parts) > 1 else number


def self_collation_difference_is_more_than_31_days(
        start_date: str,
        end_date: str
) -> bool:
    if (datetime.strptime(end_date, "%d.%m.%Y").date() - datetime.strptime(start_date, "%d.%m.%Y").date()).days > 31:
        return True
    return False


def check_run_date(
        date: str,
        start_time: str,
        end_time: str,
) -> str | None:
    """ Если время окончания смены меньше начала, функция добавит к дате заказа сутки """
    if time.fromisoformat(end_time) < time.fromisoformat(start_time):
        date = datetime.strptime(date, '%d.%m.%Y') + timedelta(days=1)
        return datetime.strftime(date, '%d.%m.%Y')
    return None
