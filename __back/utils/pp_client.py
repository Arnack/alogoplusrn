import logging

from API.workers import get_api_worker_id_by_inn, api_create_worker, api_update_worker_phone


async def send_phone_to_pp(worker_inn: str, phone: str) -> None:
    """
    Обновить номер телефона самозанятого в системе Рабочие Руки (fin-api.handswork.pro).
    Если самозанятый уже зарегистрирован — обновляет телефон через PATCH.
    Если не зарегистрирован — создаёт нового с этим телефоном.
    """
    try:
        phone_digits = phone.lstrip('+')
        worker_id = await get_api_worker_id_by_inn(inn=worker_inn)
        if worker_id:
            await api_update_worker_phone(worker_id=worker_id, phone_number=phone_digits)
        else:
            await api_create_worker(phone_number=phone_digits, inn=worker_inn)
    except Exception as e:
        logging.exception(f'[pp_client] Ошибка при обновлении телефона в РР (ИНН={worker_inn}): {e}')
