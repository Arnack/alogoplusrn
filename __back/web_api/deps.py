from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

import database as db
from config_reader import config
from database.models import User

from web_api.security.jwt_util import decode_access_token

_bearer = HTTPBearer(auto_error=True)


async def get_current_worker(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> User:
    secret = config.web_jwt_secret
    if not secret:
        raise HTTPException(500, 'WEB_JWT_SECRET не задан')
    try:
        payload = decode_access_token(creds.credentials, secret.get_secret_value())
    except Exception:
        raise HTTPException(401, 'Недействительный токен') from None

    if payload.get('typ') != 'web_worker':
        raise HTTPException(401, 'Неверный тип токена')

    try:
        user_id = int(payload['sub'])
    except (KeyError, ValueError):
        raise HTTPException(401, 'Неверный токен')

    # Проверяем, не вытеснена ли сессия новым входом с другого устройства
    redis = getattr(request.app.state, 'redis', None)
    if redis:
        try:
            stored_iat = await redis.get(f'web_session:{user_id}')
            if stored_iat is not None and int(stored_iat) != payload.get('iat'):
                raise HTTPException(401, detail='SESSION_REPLACED')
        except HTTPException:
            raise
        except Exception:
            pass  # Redis недоступен — пропускаем проверку

    user = await db.get_user_by_id(user_id=user_id)
    if not user:
        raise HTTPException(401, 'Пользователь не найден')

    if user.tg_id and await db.has_block(worker_tg_id=user.tg_id):
        raise HTTPException(403, 'Доступ ограничен')

    if user.block:
        raise HTTPException(403, 'Доступ ограничен')

    return user


async def get_current_foreman(
    user: Annotated[User, Depends(get_current_worker)],
) -> User:
    if not user.tg_id or user.tg_id not in await db.get_foremen_tg_id():
        raise HTTPException(403, 'Раздел доступен только представителям бригады')
    return user


async def get_current_supervisor(
    user: Annotated[User, Depends(get_current_worker)],
) -> User:
    if not user.tg_id or user.tg_id not in await db.get_supervisors_tg_id():
        raise HTTPException(403, 'Раздел доступен только координаторам')
    return user
