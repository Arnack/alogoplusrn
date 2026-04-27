import logging

from API.mobile.client import mobile_get


async def add_worker_to_shift(shift_id: int) -> bool:
    """Исполнитель берёт свободную смену."""
    status, result = await mobile_get(f'/shifts/add-worker/{shift_id}')
    if status == 200:
        return True
    logging.error(f'[Mobile] add_worker_to_shift shift={shift_id} -> {status}: {result}')
    return False


async def add_worker_to_reserve(shift_id: int) -> bool:
    """Исполнитель уходит в резерв."""
    status, result = await mobile_get(f'/shifts/add-worker-reserve/{shift_id}')
    if status == 200:
        return True
    logging.error(f'[Mobile] add_worker_to_reserve shift={shift_id} -> {status}: {result}')
    return False


async def accept_shift(shift_id: int) -> bool:
    """Исполнитель подтверждает уже взятую смену."""
    status, result = await mobile_get(f'/shifts/accept-shift/{shift_id}')
    if status == 200:
        return True
    logging.error(f'[Mobile] accept_shift shift={shift_id} -> {status}: {result}')
    return False
