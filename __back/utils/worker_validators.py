import re


def validate_inn(inn: str) -> bool:
    """
    Валидация ИНН - должен состоять из 12 цифр

    Args:
        inn: Строка с ИНН

    Returns:
        True если ИНН валиден, False иначе
    """
    if not inn:
        return False

    # Убираем все нецифровые символы
    digits = ''.join(filter(str.isdigit, inn))

    # ИНН должен состоять ровно из 12 цифр
    return len(digits) == 12


def normalize_phone_number(phone: str) -> str:
    """
    Нормализация номера телефона - приведение к формату +7XXXXXXXXXX

    Принимает номер в любом формате:
    - 89031234567
    - 79031234567
    - 9031234567
    - 8 (903) 123-45-67
    - +79031234567
    - и т.д.

    Возвращает номер в формате +7XXXXXXXXXX (12 символов)

    Args:
        phone: Строка с номером телефона

    Returns:
        Нормализованный номер телефона в формате +7XXXXXXXXXX
    """
    if not phone:
        return ''

    # Убираем все нецифровые символы
    digits = ''.join(filter(str.isdigit, phone))

    if not digits:
        return ''

    # Если номер содержит 11 и более цифр и начинается с 7 или 8, убираем первую цифру
    if len(digits) >= 11 and digits[0] in ['7', '8']:
        digits = digits[1:11]  # Берём следующие 10 цифр
    # Если номер ровно 10 цифр, используем как есть
    elif len(digits) == 10:
        pass
    # Если меньше 10 цифр, возвращаем как есть (может быть неполный номер)
    else:
        digits = digits[:10] if len(digits) > 10 else digits

    # Если получили ровно 10 цифр, добавляем префикс +7
    if len(digits) == 10:
        return f'+7{digits}'

    # Если номер неполный, возвращаем как есть (без префикса)
    return digits


def validate_card_number(card_number: str) -> bool:
    """
    Валидация номера банковской карты - должен состоять из 16 цифр

    Args:
        card_number: Строка с номером карты

    Returns:
        True если номер карты валиден, False иначе
    """
    if not card_number:
        return False

    # Убираем все нецифровые символы (пробелы, дефисы и т.д.)
    digits = ''.join(filter(str.isdigit, card_number))

    # Номер карты должен состоять ровно из 16 цифр
    return len(digits) == 16


def validate_telegram_id(telegram_id: str) -> bool:
    """
    Валидация Telegram ID - должен быть числом

    Args:
        telegram_id: Строка с Telegram ID

    Returns:
        True если Telegram ID валиден, False иначе
    """
    if not telegram_id:
        return False

    # Проверяем, что строка содержит только цифры
    return telegram_id.strip().isdigit()
