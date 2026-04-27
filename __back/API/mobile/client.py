import logging
import aiohttp

from config_reader import config

MOBILE_BASE_URL = 'https://mobile.handswork.pro/api'


def get_mobile_headers() -> dict:
    token = config.mobile_api_token
    if not token:
        raise RuntimeError('mobile_api_token не настроен в .env')
    return {
        'Authorization': token.get_secret_value(),
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }


async def mobile_get(path: str) -> tuple[int, dict | None]:
    url = f'{MOBILE_BASE_URL}{path}'
    headers = get_mobile_headers()
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            try:
                body = await response.json()
            except Exception:
                body = await response.text()
            if response.status != 200:
                logging.error(f'[Mobile GET] {path} -> {response.status}: {body}')
            return response.status, body


async def mobile_post(path: str, json: dict = None) -> tuple[int, dict | None]:
    url = f'{MOBILE_BASE_URL}{path}'
    headers = get_mobile_headers()
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, json=json) as response:
            try:
                body = await response.json()
            except Exception:
                body = await response.text()
            if response.status not in (200, 201):
                logging.error(f'[Mobile POST] {path} -> {response.status}: {body}')
            return response.status, body
