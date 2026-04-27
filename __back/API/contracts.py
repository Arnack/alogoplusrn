"""
Обёртка для обратной совместимости.
Логика договоров — через fin-api.handswork.pro (старый жёлтый кабинет).
"""
import logging

from API.fin.contracts import (
    fin_get_worker_contracts,
    fin_get_contract_pdf,
    fin_sign_contract_by_worker,
    fin_create_contracts_for_all_orgs,
    fin_get_worker_contracts_all_orgs,
)
from utils.organizations import orgs_contract_template_id


async def get_worker_contracts(worker_id: int) -> list:
    return await fin_get_worker_contracts(worker_id)


async def get_worker_contract_pdf(api_worker_id: int) -> bytes | None:
    contracts = await fin_get_worker_contracts(api_worker_id)
    if not contracts:
        return None
    contract_id = contracts[0].get('id')
    if not contract_id:
        return None
    return await fin_get_contract_pdf(contract_id)


async def get_preview_contract_bytes(api_worker_id: int, contract_id: int) -> bytes | None:
    return await fin_get_contract_pdf(contract_id)


async def create_worker_contract(api_worker_id: int, contract_id: int) -> int | None:
    return contract_id


async def sign_contract_by_worker(contract_id: int, sign: str = None) -> bool:
    """Подписывает договор от имени работника через администраторский токен."""
    return await fin_sign_contract_by_worker(contract_id)


async def create_all_contracts_for_worker(worker_id: int) -> list | None:
    """Проверяет существующие договоры; создаёт только для ИП, у которых их нет.

    Returns:
        None  — API недоступен (не удалось ни получить, ни создать ничего).
        []    — все 3 договора уже подписаны, подписывать нечего.
        list  — договоры для подписания (новые + ранее неподписанные).
    """
    all_org_ids = list(orgs_contract_template_id.keys())

    # 1. Проверяем существующие договоры по каждому ИП
    existing = await fin_get_worker_contracts_all_orgs(worker_id, all_org_ids)

    existing_org_ids = {c['org_id'] for c in existing}
    unsigned_existing = [c for c in existing if not c.get('signed')]

    # 2. ИП без договора
    missing_map = {
        org_id: tmpl_id
        for org_id, tmpl_id in orgs_contract_template_id.items()
        if org_id not in existing_org_ids
    }

    # 3. Все 3 ИП уже имеют подписанные договоры — ничего делать не нужно
    if not missing_map and not unsigned_existing:
        logging.info(
            f'[contracts] worker={worker_id} — '
            f'все договоры уже подписаны ({sorted(existing_org_ids)}), пропускаем'
        )
        return []

    # 4. Создаём договоры только для ИП без договора
    new_contracts = []
    if missing_map:
        new_contracts = await fin_create_contracts_for_all_orgs(worker_id, missing_map)
        logging.info(
            f'[contracts] worker={worker_id} — '
            f'создано {len(new_contracts)}/{len(missing_map)} договоров '
            f'для ИП: {sorted(missing_map.keys())}'
        )

    # 5. Если API полностью недоступен — нет ни существующих, ни новых
    if not existing and not new_contracts:
        logging.error(
            f'[contracts] worker={worker_id} — '
            f'не удалось получить или создать ни одного договора'
        )
        return None

    to_sign = unsigned_existing + new_contracts
    if unsigned_existing:
        logging.info(
            f'[contracts] worker={worker_id} — '
            f'{len(unsigned_existing)} ранее неподписанных договоров добавлено к списку'
        )
    return to_sign


async def sign_all_worker_contracts(contracts: list) -> bool:
    """Подписывает все договоры из списка, переключая org перед каждым подписанием."""
    from API.fin.contracts import fin_change_organization, _org_switch_lock
    async with _org_switch_lock:
        for contract in contracts:
            contract_id = contract.get('id')
            if not contract_id:
                continue
            org_id = contract.get('org_id')
            if org_id:
                switched = await fin_change_organization(org_id)
                if not switched:
                    logging.warning(f'[contracts] sign: не удалось переключить org_id={org_id} для contract_id={contract_id}')
            ok = await fin_sign_contract_by_worker(contract_id)
            if not ok:
                logging.error(f'[contracts] sign: не удалось подписать contract_id={contract_id}')
                return False
    return True
