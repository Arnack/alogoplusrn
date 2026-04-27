"""
Обёртка для обратной совместимости.
Вся логика перенесена на fin API (fin-api.handswork.pro).
"""
from API.fin.workers import (
    fin_create_worker,
    fin_update_worker_bank_card,
    fin_update_worker_phone,
    fin_get_worker_full_name,
    fin_check_fns_status,
    fin_get_worker_by_inn,
    fin_get_worker_by_phone,
)


async def update_worker_bank_card(api_worker_id: int, bank_card: str) -> bool:
    return await fin_update_worker_bank_card(api_worker_id, bank_card)


async def get_api_worker_id_by_inn(inn: str) -> int | None:
    worker = await fin_get_worker_by_inn(inn)
    return worker.get('id') if worker else None


async def api_update_worker_phone(worker_id: int, phone_number: str) -> bool:
    # Нормализуем до 10 цифр (без кода страны)
    digits = phone_number.lstrip('+')
    if digits.startswith('7') and len(digits) == 11:
        digits = digits[1:]
    return await fin_update_worker_phone(worker_id, digits)


async def api_create_worker(
        phone_number: str,
        inn: str,
        card_number: str = None,
) -> int | None:
    # Нормализуем до 10 цифр (без кода страны)
    digits = phone_number.lstrip('+') if phone_number else phone_number
    if digits and digits.startswith('7') and len(digits) == 11:
        digits = digits[1:]
    return await fin_create_worker(phone_number=digits, inn=inn, card_number=card_number)


async def get_worker_by_phone_number_or_inn(value: str) -> dict | None:
    """
    Поиск работника по телефону или ИНН через fin API.
    value может быть:
      - 10-значный телефон (9XXXXXXXXX)
      - 11-значный телефон (7XXXXXXXXX или +7XXXXXXXXX)
      - ИНН (12 цифр)
    """
    if not value:
        return None
    v = value.lstrip('+')
    # ИНН — 12 цифр
    if v.isdigit() and len(v) == 12:
        return await fin_get_worker_by_inn(v)
    # Телефон — нормализуем до 10 цифр
    phone = v[1:] if v.startswith('7') and len(v) == 11 else v
    if phone.isdigit() and len(phone) == 10:
        return await fin_get_worker_by_phone(phone)
    # Fallback — пробуем как ИНН
    return await fin_get_worker_by_inn(v)


async def api_check_fns_status(api_worker_id: int) -> tuple:
    return await fin_check_fns_status(api_worker_id)


async def api_get_worker_full_name(api_worker_id: int) -> dict | None:
    return await fin_get_worker_full_name(api_worker_id)
