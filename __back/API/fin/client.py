"""
Клиент для старого (желтого) кабинета handswork.pro.
Base URL: https://fin-api.handswork.pro/api/v1/
Auth:     Token {main_rr_token}
"""
import aiohttp
import logging

from config_reader import config

FIN_BASE_URL = 'https://fin-api.handswork.pro/api/v1'


def _get_headers() -> dict:
    token = config.main_rr_token
    if not token:
        raise RuntimeError('main_rr_token не настроен в .env')
    return {
        'Authorization': f'Token {token.get_secret_value()}',
        'Content-Type': 'application/json',
    }


async def fin_get(path: str, params: dict = None) -> dict | None:
    url = f'{FIN_BASE_URL}{path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=_get_headers(), params=params) as response:
                if response.status == 200:
                    return await response.json()
                logging.error(f'[FIN GET] {path} -> {response.status}: {await response.text()}')
                return None
    except Exception as e:
        logging.error(f'[FIN GET] {path}: {e}')
        return None


async def fin_post(path: str, json: dict = None, data=None) -> tuple[int, dict | None]:
    url = f'{FIN_BASE_URL}{path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=_get_headers(), json=json, data=data) as response:
                try:
                    body = await response.json()
                except Exception:
                    body = await response.text()
                return response.status, body
    except Exception as e:
        logging.error(f'[FIN POST] {path}: {e}')
        return 0, None


async def fin_get_bytes(path: str) -> bytes | None:
    """GET запрос, возвращает bytes (для скачивания PDF)."""
    url = f'{FIN_BASE_URL}{path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=_get_headers()) as response:
                if response.status == 200:
                    return await response.read()
                logging.error(f'[FIN GET bytes] {path} -> {response.status}: {await response.text()}')
                return None
    except Exception as e:
        logging.error(f'[FIN GET bytes] {path}: {e}')
        return None


async def fin_post_bytes(path: str, json: dict = None) -> bytes | None:
    """POST запрос, возвращает bytes (для скачивания PDF)."""
    url = f'{FIN_BASE_URL}{path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, headers=_get_headers(), json=json) as response:
                if response.status == 200:
                    return await response.read()
                logging.error(f'[FIN POST bytes] {path} -> {response.status}: {await response.text()}')
                return None
    except Exception as e:
        logging.error(f'[FIN POST bytes] {path}: {e}')
        return None


async def fin_patch(path: str, json: dict = None) -> tuple[int, dict | None]:
    url = f'{FIN_BASE_URL}{path}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url=url, headers=_get_headers(), json=json) as response:
                try:
                    body = await response.json()
                except Exception:
                    body = await response.text()
                return response.status, body
    except Exception as e:
        logging.error(f'[FIN PATCH] {path}: {e}')
        return 0, None
