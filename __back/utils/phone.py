from typing import Union
import re


def normalize_phone_number(
        phone_number: str
) -> Union[None, str]:
    """
        Функция, которая приводит номер телефона к формату: +79998887766
        :param phone_number: Строка с номером телефона
        :return: Отформатированный номер телефона или None при некорректном номере
    """
    cleaned = re.sub(r'\D', '', phone_number)

    if len(cleaned) > 1 and cleaned.startswith('+7'):
        cleaned = '7' + cleaned[2:]
    elif len(cleaned) == 11 and cleaned.startswith(('7', '8')):
        cleaned = '7' + cleaned[1:]

    if len(cleaned) != 11 or not cleaned.isdigit() or not cleaned.startswith(('7', '8')):
        return None

    return f"+{cleaned}"
