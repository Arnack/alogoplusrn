"""Выплата через РР по ссылке на чек (п.10 ТЗ).

П.10 ТЗ: Выплата через РР (receipt URL + INN + amount + card).
Карта фиксируется на момент подписания акта.
"""
import logging
from typing import Optional, Dict, Any

from API.fin.client import fin_post


async def create_receipt_payment(
        receipt_url: str,
        inn: str,
        amount: str,
        card_number: str,
        org_id: int,
        worker_id: Optional[int] = None,
        act_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Отправляет запрос на выплату через РР по ссылке на чек.

    Args:
        receipt_url: Ссылка на чек из «Мой налог» (например, https://lknpd.nalog.ru/api/v1/receipt/...)
        inn: ИНН самозанятого
        amount: Сумма выплаты
        card_number: Номер карты для выплаты (фиксируется на момент подписания акта)
        org_id: ID юридического лица (ИП) для выплаты
        worker_id: ID работника (для логирования)
        act_id: ID акта (для привязки)

    Returns:
        dict с результатом выплаты или None при ошибке
        {
            'success': bool,
            'rr_payment_id': str | None,
            'status': str,
            'message': str
        }
    """
    payload = {
        'receipt_url': receipt_url,
        'inn': inn,
        'amount': amount,
        'card_number': card_number.replace(' ', ''),  # убираем пробелы
        'org_id': org_id,
    }

    # Опциональные поля для трассировки
    if worker_id:
        payload['worker_id'] = worker_id
    if act_id:
        payload['act_id'] = act_id

    logging.info(
        f'[receipt_payment] Выплата через РР: inn={inn} amount={amount} '
        f'card={card_number[-4:]} org={org_id} worker={worker_id} act={act_id}'
    )

    # Endpoint для выплаты по чеку (handswork.pro API)
    status, result = await fin_post('/payments/receipt-payout', json=payload)

    if status in (200, 201):
        logging.info(f'[receipt_payment] Выплата успешно создана: {result}')
        return {
            'success': True,
            'rr_payment_id': result.get('id') if isinstance(result, dict) else None,
            'status': 'created',
            'message': 'Выплата успешно создана',
        }
    else:
        logging.error(f'[receipt_payment] Ошибка выплаты: status={status}, result={result}')
        return {
            'success': False,
            'rr_payment_id': None,
            'status': f'error:{status}',
            'message': f'Ошибка при создании выплаты: {status}',
        }
