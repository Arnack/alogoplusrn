"""Проверка подписи Telegram Web App initData (https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl


class TelegramWebAppDataError(ValueError):
    pass


def parse_and_validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict[str, Any]:
    if not init_data or not bot_token:
        raise TelegramWebAppDataError('empty init_data or bot_token')

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_received = parsed.pop('hash', None)
    if not hash_received:
        raise TelegramWebAppDataError('hash missing')

    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(parsed.items()))

    secret_key = hmac.new(
        b'WebAppData',
        bot_token.encode(),
        hashlib.sha256,
    ).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, hash_received):
        raise TelegramWebAppDataError('invalid hash')

    auth_date_raw = parsed.get('auth_date')
    if auth_date_raw:
        auth_date = int(auth_date_raw)
        if time.time() - auth_date > max_age_seconds:
            raise TelegramWebAppDataError('init_data expired')

    user_raw = parsed.get('user')
    if not user_raw:
        raise TelegramWebAppDataError('user missing')
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError as e:
        raise TelegramWebAppDataError('user json invalid') from e

    return user
