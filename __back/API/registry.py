"""
Точка входа для работы с реестрами выплат.
Использует старый (желтый) кабинет: fin-api.handswork.pro + Token {main_rr_token}
"""
from API.fin.registry import (
    create_payment,
    get_registry_updated_date,
    send_registry_for_payment,
    get_registry_transactions,
    get_registry_status,
)
