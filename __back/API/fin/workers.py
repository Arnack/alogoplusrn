import logging
import aiohttp

from config_reader import config

FIN_API_BASE = 'https://fin-api.handswork.pro/api/v1'


def _get_fin_headers() -> dict:
    token = config.main_rr_token
    if not token:
        raise RuntimeError('main_rr_token не настроен в .env')
    return {'authorization': f'Token {token.get_secret_value()}'}


def _to_iso_date(value: str) -> str | None:
    """Конвертирует ДД.ММ.ГГГГ → ГГГГ-ММ-ДД для fin API."""
    try:
        d, m, y = value.strip().split('.')
        return f'{y}-{m}-{d}'
    except Exception:
        return None


async def fin_create_worker(
    phone_number: str,
    inn: str,
    card_number: str = None,
    first_name: str = None,
    last_name: str = None,
    patronymic: str = None,
    birthday: str = None,
    passport_series: str = None,
    passport_number: str = None,
    passport_issue_date: str = None,
) -> int | None:
    """
    Создать нового работника в fin-api.handswork.pro.
    phone_number — 10 цифр без кода страны (например: 9036390303).
    Даты — в формате ДД.ММ.ГГГГ.
    Возвращает id работника или None при ошибке.
    """
    url = f'{FIN_API_BASE}/workers'
    payload = {
        'phone_number': phone_number,
        'inn': inn,
        'first_name': first_name or 'Иван',
        'last_name': last_name or 'Иванов',
        'patronymic': patronymic or 'Иванович',
    }
    if card_number:
        payload['bankcard_number'] = card_number
    if birthday:
        payload['birthday'] = birthday  # fin API ожидает ДД.ММ.ГГГГ

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=_get_fin_headers(), json=payload) as response:
                data = await response.json()
                data_str = str(data).lower()
                if response.status in (200, 201):
                    worker_id = data.get('id')
                    if not worker_id:
                        logging.error(f'[fin-api] POST /workers 200/201 но нет id: {data}')
                elif response.status in (400, 422):
                    if 'инн уже существует' in data_str or ('inn' in data_str and 'уже' in data_str):
                        logging.warning(f'[fin-api] POST /workers: ИНН {inn} уже существует — ищем по ИНН')
                        existing = await fin_get_worker_by_inn(inn)
                        worker_id = existing['id'] if existing else None
                    elif 'phone' in data_str or 'телефон' in data_str:
                        logging.warning(f'[fin-api] POST /workers: телефон {phone_number} уже существует — ищем по телефону')
                        existing = await fin_get_worker_by_phone(phone_number)
                        worker_id = existing['id'] if existing else None
                    else:
                        logging.error(f'[fin-api] POST /workers {response.status}: {data}')
                        return None
                else:
                    logging.error(f'[fin-api] POST /workers → {response.status}: {data}')
                    return None

            if not worker_id:
                logging.error(f'[fin-api] fin_create_worker: worker_id=None после всех проверок, phone={phone_number} inn={inn}')
                return None

            # Патчим паспортные данные отдельным запросом (требует updatedDate из GET)
            has_passport = passport_series or passport_number or passport_issue_date
            if has_passport:
                async with session.get(
                    f'{FIN_API_BASE}/workers/{worker_id}', headers=_get_fin_headers()
                ) as gr:
                    worker_data = await gr.json()
                    updated_date = worker_data.get('updatedDate')

                passport_patch = {'updatedDate': updated_date, 'passportData': {}}
                if passport_series:
                    passport_patch['passportData']['series'] = passport_series
                if passport_number:
                    passport_patch['passportData']['number'] = passport_number
                if passport_issue_date:
                    passport_patch['passportData']['whenIssued'] = passport_issue_date

                async with session.patch(
                    f'{FIN_API_BASE}/workers/{worker_id}',
                    headers=_get_fin_headers(),
                    json=passport_patch,
                ) as pr:
                    if pr.status != 200:
                        text = await pr.text()
                        logging.warning(f'[fin-api] PATCH passport worker={worker_id} → {pr.status}: {text[:200]}')

            return worker_id
    except Exception as e:
        logging.exception(f'[fin-api] fin_create_worker({phone_number}): {e}')
        return None


async def fin_patch_worker_profile(
    worker_id: int,
    first_name: str = None,
    last_name: str = None,
    patronymic: str = None,
    birthday: str = None,
    passport_series: str = None,
    passport_number: str = None,
    passport_issue_date: str = None,
) -> bool:
    """PATCH имя, дату рождения и паспорт работника в fin API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as gr:
                if gr.status != 200:
                    logging.error(f'[fin-api] GET worker={worker_id} → {gr.status}')
                    return False
                worker_data = await gr.json()
                updated_date = worker_data.get('updatedDate')

            payload = {'updatedDate': updated_date}
            if first_name:
                payload['firstName'] = first_name
            if last_name:
                payload['lastName'] = last_name
            if patronymic:
                payload['patronymic'] = patronymic
            if birthday:
                payload['birthday'] = birthday
            passport = {}
            if passport_series:
                passport['series'] = passport_series
            if passport_number:
                passport['number'] = passport_number
            if passport_issue_date:
                passport['whenIssued'] = passport_issue_date
            if passport:
                payload['passportData'] = passport

            async with session.patch(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
                json=payload,
            ) as pr:
                if pr.status == 200:
                    return True
                text = await pr.text()
                logging.error(f'[fin-api] PATCH profile worker={worker_id} → {pr.status}: {text[:200]}')
                return False
    except Exception as e:
        logging.exception(f'[fin-api] fin_patch_worker_profile({worker_id}): {e}')
        return False


async def fin_update_worker_phone(worker_id: int, phone_number: str) -> bool:
    """Обновляет номер телефона работника через PATCH /workers/{id} (требует updatedDate).
    phone_number — 10 цифр без кода страны."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as gr:
                if gr.status != 200:
                    logging.error(f'[fin-api] GET worker={worker_id} → {gr.status}')
                    return False
                worker_data = await gr.json()
                updated_date = worker_data.get('updatedDate')

            async with session.patch(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
                json={'updatedDate': updated_date, 'phoneNumber': phone_number},
            ) as pr:
                if pr.status == 200:
                    return True
                text = await pr.text()
                logging.error(f'[fin-api] PATCH phone worker={worker_id} → {pr.status}: {text[:200]}')
                return False
    except Exception as e:
        logging.exception(f'[fin-api] fin_update_worker_phone({worker_id}): {e}')
        return False


async def fin_update_worker_bank_card(worker_id: int, bank_card: str) -> bool:
    """Обновляет номер карты работника через PATCH /workers/{id} (требует updatedDate)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as gr:
                if gr.status != 200:
                    logging.error(f'[fin-api] GET worker={worker_id} → {gr.status}')
                    return False
                worker_data = await gr.json()
                updated_date = worker_data.get('updatedDate')

            async with session.patch(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
                json={'updatedDate': updated_date, 'bankcardNumber': bank_card},
            ) as pr:
                if pr.status == 200:
                    return True
                text = await pr.text()
                logging.error(f'[fin-api] PATCH card worker={worker_id} → {pr.status}: {text[:200]}')
                return False
    except Exception as e:
        logging.exception(f'[fin-api] fin_update_worker_bank_card({worker_id}): {e}')
        return False


async def fin_get_worker_by_card(card: str) -> dict | None:
    """Ищет работника в fin API по номеру карты."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers',
                headers=_get_fin_headers(),
                params={'search': f'bankcard_number:{card}'},
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get('results') or []
                    return results[0] if results else None
                return None
    except Exception as e:
        logging.exception(f'[fin-api] fin_get_worker_by_card({card}): {e}')
        return None


async def fin_get_worker_full_name(worker_id: int) -> dict | None:
    """Возвращает ФИО работника из fin API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        return {
            'first_name': data.get('firstName') or '',
            'last_name': data.get('lastName') or '',
            'middle_name': data.get('patronymic') or '',
        }
    except Exception as e:
        logging.exception(f'[fin-api] fin_get_worker_full_name({worker_id}): {e}')
        return None


async def fin_get_worker(worker_id: int) -> dict | None:
    """Возвращает полный профиль работника из fin API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as r:
                if r.status != 200:
                    logging.error(f'[fin-api] GET /workers/{worker_id} -> {r.status}')
                    return None
                return await r.json()
    except Exception as e:
        logging.exception(f'[fin-api] fin_get_worker({worker_id}): {e}')
        return None


async def fin_get_worker_by_id(worker_id: int) -> dict | None:
    """Совместимость со старым именем функции."""
    return await fin_get_worker(worker_id)


async def fin_get_worker_by_inn(inn: str) -> dict | None:
    # Пробуем оба варианта: с ведущим нулём и без (fin API может хранить ИНН как число)
    for search_inn in dict.fromkeys([inn, inn.lstrip('0')]):
        if not search_inn:
            continue
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{FIN_API_BASE}/workers',
                    headers=_get_fin_headers(),
                    params={'search': f'inn:{search_inn}'},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results') or []
                        if results:
                            return results[0]
        except Exception as e:
            logging.exception(f'[fin-api] fin_get_worker_by_inn({search_inn}): {e}')
    return None


async def fin_get_worker_by_phone(phone: str) -> dict | None:
    """
    Найти работника в fin-api.handswork.pro по номеру телефона.
    phone — 10 цифр без кода страны (например: 9036390303).
    Возвращает dict с полями: id, firstName, lastName, patronymic,
    phone, inn, bankcardNumber, fnsStatus, ...
    """
    url = f'{FIN_API_BASE}/workers'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=url,
                headers=_get_fin_headers(),
                params={'search': f'phone_number:{phone}'},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results') or []
                    return results[0] if results else None
                logging.error(f'[fin-api] GET /workers?search=phone_number:{phone} → {response.status}')
                return None
    except Exception as e:
        logging.exception(f'[fin-api] get_worker_by_phone({phone}): {e}')
        return None


async def fin_check_fns_status(worker_id: int) -> tuple[bool, bool]:
    """
    Проверяет SMZ-статус работника через fin API.
    Запускает проверку через mass-action, затем читает статус.
    Возвращает (is_registered, is_smz).
      is_registered = платформа подключена / запрос отправлен
      is_smz        = зарегистрирован как самозанятый
    """
    try:
        async with aiohttp.ClientSession() as session:
            await session.patch(
                f'{FIN_API_BASE}/workers/mass-action',
                headers=_get_fin_headers(),
                json={
                    'ids': [worker_id],
                    'action': 'check_self_employment_and_send_connection_request',
                    'current_organization_id': None,
                },
            )
            async with session.get(
                f'{FIN_API_BASE}/workers/{worker_id}',
                headers=_get_fin_headers(),
            ) as r:
                if r.status != 200:
                    return False, False
                data = await r.json()

        fns_status = data.get('fnsStatus') or {}
        codename = (fns_status.get('codename') or '').lower()
        fns_check = data.get('fnsCheck') or False
        is_connected = data.get('isConnectedToPlatform') or False
        fns_sent = data.get('fnsSentConnectionRequest') or False

        # codename из fin API: 'taxPayer' → lower → 'taxpayer' = самозанятый, 'individual' = физлицо
        is_smz = fns_check or 'taxpayer' in codename or 'smz' in codename or 'самозан' in codename
        is_registered = is_connected or fns_sent or bool(codename)

        logging.info(
            f'[fin-api] fns_check worker={worker_id}: '
            f'fnsCheck={fns_check} fnsStatus={fns_status} '
            f'isConnected={is_connected} fnsSent={fns_sent}'
        )
        return is_registered, is_smz
    except Exception as e:
        logging.exception(f'[fin-api] fin_check_fns_status({worker_id}): {e}')
        return False, False
