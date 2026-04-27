from __future__ import annotations

import time
from typing import Any

import jwt


def create_access_token(
    *,
    user_id: int,
    secret: str,
    expire_minutes: int,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'iat': now,
        'exp': now + expire_minutes * 60,
        'typ': 'web_worker',
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def decode_access_token(token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=['HS256'])
