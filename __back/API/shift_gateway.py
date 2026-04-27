"""Локальный gateway для операций по сменам без CRM.

В актуальном fin-api из swagger не видно старых shift-endpoint'ов CRM, поэтому
эти операции временно оставлены как безопасные no-op, чтобы бизнес-логика не
использовала crm api вообще.
"""

import logging


async def add_worker_to_shift(shift_id: str, worker_id: int) -> bool:
    logging.info('[shift_gateway] skip add_worker_to_shift shift=%s worker=%s', shift_id, worker_id)
    return True


async def save_worker_time(shift_id: str, worker_id: int, hours: float) -> bool:
    logging.info('[shift_gateway] skip save_worker_time shift=%s worker=%s hours=%s', shift_id, worker_id, hours)
    return True


async def save_worker_additional_price(shift_id: str, worker_id: int, price: float, mass: bool = False) -> bool:
    logging.info(
        '[shift_gateway] skip save_worker_additional_price shift=%s worker=%s price=%s mass=%s',
        shift_id,
        worker_id,
        price,
        mass,
    )
    return True


async def close_shift(shift_id: str) -> bool:
    logging.info('[shift_gateway] skip close_shift shift=%s', shift_id)
    return True


__all__ = ['add_worker_to_shift', 'save_worker_time', 'save_worker_additional_price', 'close_shift']
