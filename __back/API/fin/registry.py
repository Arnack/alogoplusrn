"""
Реестры выплат через старый (желтый) кабинет: fin-api.handswork.pro
"""
import asyncio
import logging
import aiohttp

from API.fin.client import FIN_BASE_URL, _get_headers
from Schemas import WorkerPaymentSchema
from utils.xlsx.payments import create_payment_xlsx


async def create_payment(
        payment_id: int,
        workers: list[WorkerPaymentSchema],
        org_id: int,
        is_wallet_payment: bool = False,
        name: str = None,
) -> tuple[int | None, str | None]:
    url = f'{FIN_BASE_URL}/registry/upload-registry'
    file_bytes = create_payment_xlsx(workers=workers)
    if is_wallet_payment:
        filename = f'wallet_payment_{payment_id}.xlsx'
    elif name:
        filename = f'{name}.xlsx'
    else:
        filename = f'order_payment_{payment_id}.xlsx'
    form = aiohttp.FormData()
    form.add_field(
        'file',
        file_bytes,
        filename=filename,
    )
    form.add_field('needs_sign_documents', 'true')
    form.add_field('current_organization_id', str(org_id))

    headers = _get_headers()
    headers.pop('Content-Type', None)  # aiohttp sets multipart Content-Type automatically

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=headers, data=form) as response:
                if response.status == 200:
                    json = await response.json()
                    if json.get('errorsReport'):
                        logging.error(f'[FIN registry] create_payment errorsReport: {json["errorsReport"]}')
                    return json.get('id'), json.get('status', {}).get('codename')
                logging.error(f'[FIN registry] create_payment -> {response.status}: {await response.text()}')
                return None, None
    except Exception as e:
        logging.error(f'[FIN registry] create_payment: {e}')
        return None, None


async def get_registry_updated_date(registry_id: int) -> str | None:
    url = f'{FIN_BASE_URL}/registry/{registry_id}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=_get_headers()) as response:
                if response.status == 200:
                    return (await response.json()).get('updatedDate')
                logging.error(f'[FIN registry] get_registry_updated_date {registry_id} -> {response.status}')
                return None
    except Exception as e:
        logging.error(f'[FIN registry] get_registry_updated_date {registry_id}: {e}')
        return None


async def send_registry_for_payment(registry_id: int, updated_date: str) -> bool:
    url = f'{FIN_BASE_URL}/registry/{registry_id}'
    data = {'status': {'id': 3, 'codename': 'inPayment'}, 'updated_date': updated_date}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url=url, headers=_get_headers(), json=data) as response:
                if response.status == 200:
                    json = await response.json()
                    return json.get('status', {}).get('codename') == 'inPayment'
                logging.error(f'[FIN registry] send_registry_for_payment {registry_id} -> {response.status}: {await response.text()}')
                return False
    except Exception as e:
        logging.error(f'[FIN registry] send_registry_for_payment {registry_id}: {e}')
        return False


async def get_registry_transactions(registry_id: int) -> list[dict] | None:
    url = f'{FIN_BASE_URL}/registry/{registry_id}/get-transactions'
    try:
        for attempt in range(2):
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, headers=_get_headers()) as response:
                    if response.status == 200:
                        return (await response.json()).get('results')
                    body = await response.text()
                    if response.status == 400:
                        logging.warning(f'[FIN registry] get_registry_transactions {registry_id} -> 400: {body[:200]}')
                        return None
                    if response.status >= 500 and attempt == 0:
                        logging.warning(f'[FIN registry] get_registry_transactions {registry_id} -> {response.status}, retrying')
                        await asyncio.sleep(1)
                        continue
                    logging.error(f'[FIN registry] get_registry_transactions {registry_id} -> {response.status}: {body[:200]}')
                    return None
    except Exception as e:
        logging.error(f'[FIN registry] get_registry_transactions {registry_id}: {e}')
        return None


async def get_registry_status(registry_id: int) -> str | None:
    url = f'{FIN_BASE_URL}/registry/{registry_id}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=_get_headers()) as response:
                if response.status == 200:
                    return (await response.json()).get('status', {}).get('codename')
                logging.error(f'[FIN registry] get_registry_status {registry_id} -> {response.status}')
                return None
    except Exception as e:
        logging.error(f'[FIN registry] get_registry_status {registry_id}: {e}')
        return None
