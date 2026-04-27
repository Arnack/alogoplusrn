import asyncio
import logging
import aiohttp
from datetime import date

from config_reader import config
from utils.organizations import orgs_id

FIN_API_BASE = 'https://fin-api.handswork.pro/api/v1'

# Lock для переключения организаций — предотвращает race condition при параллельных регистрациях
_org_switch_lock = asyncio.Lock()


def _is_contract_signed(contract: dict) -> bool:
    return bool(
        contract.get('isSigned')
        or contract.get('is_signed')
        or contract.get('signedAt')
        or contract.get('signed_at')
    )


def _pick_relevant_contract(contracts: list) -> dict | None:
    if not contracts:
        return None
    current = next((c for c in contracts if c.get('isCurrent')), None)
    return current or max(contracts, key=lambda c: c.get('id', 0))


def _get_fin_headers() -> dict:
    token = config.main_rr_token
    if not token:
        raise RuntimeError('main_rr_token не настроен в .env')
    return {'authorization': f'Token {token.get_secret_value()}'}


async def fin_change_organization(org_id: int) -> bool:
    """Переключает активную организацию для токена."""
    url = f'{FIN_API_BASE}/account/members/change-current-organization'
    for attempt in range(3):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                url=url,
                headers=_get_fin_headers(),
                json={'organization_id': org_id},
            ) as r:
                if r.status == 200:
                    return True
                text = await r.text()
                if r.status >= 500 and attempt < 2:
                    logging.warning(f'[fin-api] change-org org_id={org_id} → {r.status}, retry {attempt + 1}/2')
                    await asyncio.sleep(1)
                    continue
                logging.error(f'[fin-api] change-org org_id={org_id} → {r.status}: {text[:200]}')
                return False
    return False


async def fin_get_organizations() -> list:
    """Возвращает список организаций (ИП) из fin API."""
    url = f'{FIN_API_BASE}/account/organizations'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=_get_fin_headers()) as r:
                if r.status == 200:
                    data = await r.json()
                    return data if isinstance(data, list) else data.get('results', [])
                text = await r.text()
                logging.error(f'[fin-api] GET /account/organizations → {r.status}: {text[:200]}')
                return []
    except Exception as e:
        logging.exception(f'[fin-api] fin_get_organizations: {e}')
        return []


async def fin_get_organization_balance(org_id: int) -> str | None:
    """Получает баланс организации из fin API по её id."""
    orgs = await fin_get_organizations()
    for org in orgs:
        if org.get('id') == org_id:
            balance = org.get('mainBalance') or org.get('balance')
            return str(balance) if balance is not None else None
    return None


async def fin_get_contract_templates() -> list:
    """Возвращает шаблоны договоров для текущей организации."""
    url = f'{FIN_API_BASE}/documents/get-contract-templates'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=_get_fin_headers()) as r:
            if r.status == 200:
                data = await r.json()
                return data.get('results', data if isinstance(data, list) else [])
            logging.error(f'[fin-api] get-contract-templates → {r.status}')
            return []


async def fin_create_worker_contract(worker_id: int, template_id: int) -> dict | None:
    """
    Создаёт договор для работника по шаблону.
    Возвращает: {id, worker_id, contract_template_id, contract_date, link_uuid, link_short_code, signed, ...}
    """
    url = f'{FIN_API_BASE}/documents/{worker_id}/{template_id}/create-worker-contract'
    payload = {'contract_date': date.today().isoformat()}
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=_get_fin_headers(), json=payload) as r:
            if r.status in (200, 201):
                return await r.json()
            text = await r.text()
            logging.error(
                f'[fin-api] create-contract worker={worker_id} tmpl={template_id} → {r.status}: {text[:200]}'
            )
            return None


async def fin_get_worker_contracts(worker_id: int) -> list:
    """Возвращает все договоры работника."""
    url = f'{FIN_API_BASE}/documents/worker-contracts/{worker_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=_get_fin_headers()) as r:
            if r.status == 200:
                data = await r.json()
                return data if isinstance(data, list) else data.get('results', [])
            logging.error(f'[fin-api] get-worker-contracts worker={worker_id} → {r.status}')
            return []


async def fin_get_contract_pdf(contract_id: int) -> bytes | None:
    """Скачивает PDF договора по его id."""
    url = f'{FIN_API_BASE}/documents/{contract_id}/get-worker-contractby-id-pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=_get_fin_headers()) as r:
            if r.status == 200:
                return await r.read()
            logging.error(f'[fin-api] get-contract-pdf id={contract_id} → {r.status}')
            return None


async def fin_sign_contract_by_worker(contract_id: int, org_id: int = None) -> bool:
    """
    Подписывает договор от имени работника через администраторский токен.
    POST /documents/contract/{contract_id}/sign-document-by-worker
    Если передан org_id — переключает организацию перед подписанием.
    Возвращает True если {'result': 'Документ успешно подписан'}.
    """
    url = f'{FIN_API_BASE}/documents/contract/{contract_id}/sign-document-by-worker'
    async with aiohttp.ClientSession() as session:
        if org_id is not None:
            await fin_change_organization(org_id)
        async with session.post(url=url, headers=_get_fin_headers()) as r:
            if r.status == 200:
                try:
                    data = await r.json(content_type=None)
                except Exception:
                    text = await r.text()
                    logging.warning(f'[fin-api] sign-contract id={contract_id} non-JSON 200: {text[:200]}')
                    # Некоторые версии API возвращают пустой 200 при успехе
                    return True
                result_str = data.get('result', '') if isinstance(data, dict) else ''
                if result_str and ('подписан' in result_str.lower() or 'success' in result_str.lower()):
                    return True
                # Пустой dict или result отсутствует — считаем успехом (API иногда так отвечает)
                if isinstance(data, dict) and not result_str:
                    logging.warning(f'[fin-api] sign-contract id={contract_id} empty result, assuming ok: {data}')
                    return True
                logging.warning(f'[fin-api] sign-contract id={contract_id} unexpected: {data}')
                return False
            text = await r.text()
            if r.status == 400 and 'уже подписан исполнителем' in text.lower():
                logging.info(f'[fin-api] sign-contract id={contract_id} already signed by worker, treating as success')
                return True
            logging.error(f'[fin-api] sign-contract id={contract_id} → {r.status}: {text[:200]}')
            return False


async def fin_get_worker_contracts_all_orgs(worker_id: int, org_ids: list) -> list:
    """
    Собирает договоры работника по всем организациям.
    Переключает org, запрашивает список, берёт самый актуальный (isCurrent=True или последний по id).
    Возвращает [{id, org_id, ...}, ...].
    """
    result = []
    async with _org_switch_lock:
        for org_id in org_ids:
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] get-contracts: не удалось переключить org_id={org_id}')
                continue
            contracts = await fin_get_worker_contracts(worker_id)
            if contracts:
                chosen = _pick_relevant_contract(contracts)
                if not chosen:
                    continue
                chosen['org_id'] = org_id
                result.append(chosen)
                logging.info(f'[fin-api] get-contracts org={org_id} worker={worker_id} id={chosen.get("id")}')
    return result


async def fin_get_worker_contracts_with_pdfs(worker_id: int, org_ids: list) -> list:
    """
    Собирает договоры и скачивает PDF — всё в одном проходе под локом,
    пока нужная организация активна.
    Возвращает [{org_id, id, pdf_bytes}, ...].
    """
    result = []
    async with _org_switch_lock:
        for org_id in org_ids:
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] get-contracts-pdf: не удалось переключить org_id={org_id}')
                continue
            contracts = await fin_get_worker_contracts(worker_id)
            if not contracts:
                logging.warning(f'[fin-api] get-contracts-pdf: org={org_id} worker={worker_id} договоров нет')
                continue
            chosen = _pick_relevant_contract(contracts)
            if not chosen:
                continue
            contract_id = chosen.get('id')
            if not contract_id:
                continue
            pdf = await fin_get_contract_pdf(contract_id)
            if pdf:
                result.append({'org_id': org_id, 'id': contract_id, 'pdf': pdf})
                logging.info(f'[fin-api] get-contracts-pdf org={org_id} worker={worker_id} id={contract_id} size={len(pdf)}b')
            else:
                logging.error(f'[fin-api] get-contracts-pdf org={org_id} id={contract_id} PDF не получен')
    return result


async def fin_ensure_contracts_for_all_orgs(
    worker_id: int,
    org_template_map: dict,
) -> list[str]:
    """
    Для каждого ИП проверяет наличие договора; если нет — создаёт и подписывает.
    org_template_map: {org_id: template_id}.
    Возвращает список org_id, для которых был создан новый договор.
    """
    created_org_ids: list[str] = []
    async with _org_switch_lock:
        for org_id, template_id in org_template_map.items():
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] ensure-contracts: не удалось переключить org_id={org_id}')
                continue
            existing = await fin_get_worker_contracts(worker_id)
            if existing:
                logging.info(f'[fin-api] ensure-contracts: договор уже есть org={org_id} worker={worker_id}')
                continue
            contract = await fin_create_worker_contract(worker_id, template_id)
            if not contract:
                logging.error(f'[fin-api] ensure-contracts: не удалось создать договор org={org_id} worker={worker_id}')
                continue
            contract_id = contract.get('id')
            if contract_id:
                signed = await fin_sign_contract_by_worker(contract_id)
                if signed:
                    created_org_ids.append(org_id)
                    logging.info(f'[fin-api] ensure-contracts: договор создан и подписан org={org_id} worker={worker_id} id={contract_id}')
                else:
                    logging.error(f'[fin-api] ensure-contracts: договор создан, но не подписан org={org_id} id={contract_id}')
    return created_org_ids


async def fin_create_missing_contracts(
    worker_id: int,
    org_template_map: dict,
) -> list:
    """
    Для каждого ИП проверяет наличие договора.
    Создаёт договора только там, где их нет (без подписания — подпись делает пользователь).
    Возвращает список только что созданных договоров.
    """
    contracts = []
    async with _org_switch_lock:
        for org_id, template_id in org_template_map.items():
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] create-missing: не удалось переключить org_id={org_id}')
                continue
            existing = await fin_get_worker_contracts(worker_id)
            if existing:
                logging.info(f'[fin-api] create-missing: договор уже есть org={org_id} worker={worker_id}')
                continue
            result = await fin_create_worker_contract(worker_id, template_id)
            if result:
                result['org_id'] = org_id
                contracts.append(result)
                logging.info(f'[fin-api] create-missing: договор создан org={org_id} worker={worker_id} id={result.get("id")}')
            else:
                logging.error(f'[fin-api] create-missing: не удалось создать org={org_id} worker={worker_id}')
    return contracts


async def fin_get_missing_contract_org_ids(
    worker_id: int,
    org_template_map: dict,
) -> list:
    """
    Проверяет наличие договора для каждого ИП.
    Возвращает список org_id, где договора нет.
    Ничего не создаёт и не подписывает.
    """
    missing = []
    async with _org_switch_lock:
        for org_id in org_template_map:
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] check-missing: не удалось переключить org_id={org_id}')
                continue
            existing = await fin_get_worker_contracts(worker_id)
            if not existing:
                missing.append(org_id)
    return missing


async def fin_create_contracts_for_all_orgs(
    worker_id: int,
    org_template_map: dict,
) -> list:
    """
    Для каждого ИП переключает организацию и создаёт договор.
    org_template_map: {org_id: template_id}, например {392: 486, 393: 487, 480: 577}.
    Возвращает список созданных договоров [{id, org_id, ...}, ...].
    """
    contracts = []
    async with _org_switch_lock:
        for org_id, template_id in org_template_map.items():
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] не удалось переключить org_id={org_id}')
                continue
            result = await fin_create_worker_contract(worker_id, template_id)
            if result:
                result['org_id'] = org_id
                contracts.append(result)
                logging.info(
                    f'[fin-api] договор создан org={org_id} worker={worker_id} id={result.get("id")}'
                )
            else:
                logging.error(f'[fin-api] не удалось создать договор org={org_id} worker={worker_id}')
    return contracts


async def fin_ensure_worker_contracts_all_orgs(
    worker_id: int,
    org_template_map: dict,
) -> list:
    """
    Гарантирует наличие релевантного договора по каждому ИП.
    Если по ИП договора нет — создаёт его.
    Возвращает список договоров [{id, org_id, ...}, ...].
    """
    contracts = []
    async with _org_switch_lock:
        for org_id, template_id in org_template_map.items():
            switched = await fin_change_organization(org_id)
            if not switched:
                logging.error(f'[fin-api] ensure-worker-contracts: не удалось переключить org_id={org_id}')
                continue
            existing = await fin_get_worker_contracts(worker_id)
            chosen = _pick_relevant_contract(existing)
            if not chosen:
                chosen = await fin_create_worker_contract(worker_id, template_id)
            if not chosen:
                logging.error(f'[fin-api] ensure-worker-contracts: не удалось получить договор org={org_id} worker={worker_id}')
                continue
            chosen['org_id'] = org_id
            contracts.append(chosen)
    return contracts


async def fin_get_unsigned_contracts_all_orgs(
    worker_id: int,
    org_template_map: dict,
) -> list:
    """
    Возвращает все договоры по ИП, которые ещё не подписаны.
    При отсутствии договора по ИП сначала создаёт его.
    """
    contracts = await fin_ensure_worker_contracts_all_orgs(worker_id, org_template_map)
    return [contract for contract in contracts if not _is_contract_signed(contract)]


async def fin_sign_contracts_all_orgs(worker_id: int, contract_ids: list[int]) -> bool:
    """
    Подписывает пакет договоров работника сразу по всем ИП.
    Возвращает True только если все договоры успешно подписаны.
    """
    if not contract_ids:
        return True
    contracts = await fin_get_worker_contracts_all_orgs(worker_id=worker_id, org_ids=list(orgs_id))
    contract_map = {contract.get('id'): contract for contract in contracts if contract.get('id')}
    success = True
    for contract_id in contract_ids:
        contract = contract_map.get(contract_id)
        org_id = contract.get('org_id') if contract else None
        signed = await fin_sign_contract_by_worker(contract_id=contract_id, org_id=org_id)
        if not signed:
            success = False
    return success
