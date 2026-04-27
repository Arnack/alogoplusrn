"""Совместимый слой для старых импортов логгеров.

Логирование временно отключено: функции оставлены как no-op, чтобы старый код
мог импортироваться без падений.
"""

import logging
from typing import Any


friend_logger = logging.getLogger('friend_logger')
help_logger = logging.getLogger('help_logger')


def _noop(*args: Any, **kwargs: Any) -> None:
    return None


write_worker_op_log = _noop
write_accountant_op_log = _noop
write_api_log = _noop
write_worker_wp_log = _noop
write_accountant_wp_log = _noop
write_registration_log = _noop
write_contracts_log = _noop
write_receipts_log = _noop
write_documents_log = _noop
write_rr_payments_log = _noop


__all__ = [
    'friend_logger',
    'help_logger',
    'write_worker_op_log',
    'write_accountant_op_log',
    'write_api_log',
    'write_worker_wp_log',
    'write_accountant_wp_log',
    'write_registration_log',
    'write_contracts_log',
    'write_receipts_log',
    'write_documents_log',
    'write_rr_payments_log',
]
