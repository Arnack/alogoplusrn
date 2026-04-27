from .workers import *
from .contracts import *
from .org import *
from .registry import *
from .documents import *
from .fin.receipt_payment import create_receipt_payment


__all__ = [
    # workers
    'api_create_worker', 'api_check_fns_status', 'api_get_worker_full_name',
    'get_worker_by_phone_number_or_inn', 'update_worker_bank_card',
    # contracts (fin API — жёлтый кабинет)
    'get_worker_contracts', 'get_worker_contract_pdf', 'get_preview_contract_bytes',
    'create_worker_contract', 'sign_contract_by_worker',
    'create_all_contracts_for_worker', 'sign_all_worker_contracts',
    # org
    'get_organization_balance', 'change_current_organization',
    # registry (желтый кабинет)
    'create_payment', 'get_registry_updated_date', 'send_registry_for_payment',
    'get_registry_transactions', 'get_registry_status',
    # documents
    'get_unsigned_document', 'sign_worker_document',
    # receipt payment stub (п.10)
    'create_receipt_payment',
]
