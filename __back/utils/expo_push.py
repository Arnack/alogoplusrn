from __future__ import annotations

import logging

import httpx

import database as db

logger = logging.getLogger(__name__)

_EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'


async def send_push(user_id: int, title: str, body: str) -> None:
    tokens = await db.get_device_tokens(user_id)
    if not tokens:
        return

    messages = [
        {'to': token, 'title': title, 'body': body, 'sound': 'default'}
        for token in tokens
    ]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _EXPO_PUSH_URL,
                json=messages,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
            )
            resp.raise_for_status()
            data = resp.json().get('data', [])
    except Exception as exc:
        logger.warning('expo push error for user %s: %s', user_id, exc)
        return

    # Remove stale tokens
    stale = [
        tokens[i]
        for i, item in enumerate(data)
        if isinstance(item, dict) and item.get('details', {}).get('error') == 'DeviceNotRegistered'
    ]
    for token in stale:
        try:
            await db.delete_device_token(token)
        except Exception:
            pass
