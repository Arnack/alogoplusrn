from __future__ import annotations

import logging
import re
import time
from typing import Optional

from aiogram import Bot
from fastapi import APIRouter, Body, Header, HTTPException, Request

import database as db
from API.fin.workers import fin_get_worker_by_phone
from config_reader import config
from utils.phone import normalize_phone_number
from web_api.rate_limit import assert_under_limit
from web_api.schemas import (
    AuthBootstrapResponse,
    CheckUserBody,
    CheckUserResponse,
    LoginPhoneBody,
    TelegramWebAppAuthBody,
    TokenResponse,
)
from web_api.security.jwt_util import create_access_token, decode_access_token
from web_api.security.telegram_webapp import TelegramWebAppDataError, parse_and_validate_init_data

router = APIRouter()
logger = logging.getLogger(__name__)


def _inn_last4_matches(inn: str, last4: str) -> bool:
    digits = re.sub(r'\D', '', inn or '')
    return len(digits) >= 4 and digits[-4:] == last4


def _issue_token(user_id: int) -> TokenResponse:
    secret = config.web_jwt_secret
    if not secret:
        raise HTTPException(500, 'WEB_JWT_SECRET не задан в .env')
    minutes = config.web_jwt_expire_minutes
    token = create_access_token(
        user_id=user_id,
        secret=secret.get_secret_value(),
        expire_minutes=minutes,
    )
    return TokenResponse(
        access_token=token,
        expires_in=minutes * 60,
    )


async def _register_session(request: Request, user_id: int, token_response: TokenResponse) -> None:
    """Сохраняет iat новой сессии в Redis и обновляет last_web_ip."""
    ip = request.client.host if request.client else 'unknown'

    # Обновляем last_web_ip в БД
    try:
        await db.update_user_last_web_ip(user_id=user_id, ip=ip)
    except Exception as exc:
        logger.warning('[session] Не удалось обновить last_web_ip user=%s: %s', user_id, exc)

    # Записываем iat новой сессии в Redis (старая сессия автоматически инвалидируется)
    redis = getattr(request.app.state, 'redis', None)
    if redis:
        try:
            secret = config.web_jwt_secret
            payload = decode_access_token(
                token_response.access_token,
                secret.get_secret_value(),
            )
            iat = payload.get('iat', int(time.time()))
            old_iat = await redis.get(f'web_session:{user_id}')
            ttl = config.web_jwt_expire_minutes * 60
            await redis.set(f'web_session:{user_id}', str(iat), ex=ttl)
            if old_iat and int(old_iat) != iat:
                logger.info(
                    '[session] Смена сессии user=%s ip=%s old_iat=%s new_iat=%s',
                    user_id, ip, old_iat, iat,
                )
        except Exception as exc:
            logger.warning('[session] Ошибка записи сессии в Redis user=%s: %s', user_id, exc)


async def _authenticate_by_init_data(
    *,
    init_data: str,
    request: Request,
) -> TokenResponse:
    bot_token = config.bot_token
    if not bot_token:
        raise HTTPException(500, 'BOT_TOKEN не задан')

    redis = getattr(request.app.state, 'redis', None)
    ip = request.client.host if request.client else 'unknown'
    await assert_under_limit(
        redis,
        f'web:tginit:{ip}',
        80,
        3600,
    )

    try:
        tg_user = parse_and_validate_init_data(
            init_data,
            bot_token.get_secret_value(),
            max_age_seconds=config.web_telegram_init_data_max_age_seconds,
        )
    except TelegramWebAppDataError as e:
        raise HTTPException(401, str(e)) from e

    tg_id = int(tg_user['id'])
    user = await db.get_user(tg_id=tg_id)
    if not user:
        raise HTTPException(404, 'Пользователь не зарегистрирован в системе')

    if user.tg_id and await db.has_block(worker_tg_id=user.tg_id):
        raise HTTPException(403, 'Доступ ограничен')

    token = _issue_token(user.id)
    await _register_session(request, user.id, token)
    return token


@router.post('/telegram-webapp', response_model=TokenResponse)
async def auth_telegram_webapp(
    body: TelegramWebAppAuthBody,
    request: Request,
):
    return await _authenticate_by_init_data(init_data=body.init_data, request=request)


@router.post('/bootstrap', response_model=AuthBootstrapResponse)
async def auth_bootstrap(
    request: Request,
    body: Optional[TelegramWebAppAuthBody] = Body(default=None),
    x_telegram_init_data: Optional[str] = Header(default=None),
):
    """
    Универсальный старт авторизации:
    - если пришел initData (body.init_data / body.initData / заголовок X-Telegram-Init-Data),
      пробуем авто-логин по Telegram;
    - если initData нет, фронт должен показать телефон+ИНН.
    """
    init_data = (body.init_data if body else None) or x_telegram_init_data
    if not init_data:
        return AuthBootstrapResponse(
            authenticated=False,
            requires_phone_auth=True,
            reason='init_data_missing',
        )

    token = await _authenticate_by_init_data(init_data=init_data, request=request)
    return AuthBootstrapResponse(
        authenticated=True,
        requires_phone_auth=False,
        access_token=token.access_token,
        token_type=token.token_type,
        expires_in=token.expires_in,
    )


@router.post('/check-user', response_model=CheckUserResponse)
async def check_user(body: CheckUserBody, request: Request):
    redis = getattr(request.app.state, 'redis', None)
    phone = normalize_phone_number(body.phone)
    if not phone:
        return CheckUserResponse(exists=False)

    await assert_under_limit(
        redis,
        f'web:chk:{phone}',
        60,
        3600,
    )

    user = await db.get_worker_by_phone_number(phone)
    if not user:
        return CheckUserResponse(exists=False)
    return CheckUserResponse(exists=True)


@router.post('/login-phone', response_model=TokenResponse)
async def login_phone(body: LoginPhoneBody, request: Request):
    redis = getattr(request.app.state, 'redis', None)
    phone = normalize_phone_number(body.phone)
    if not phone:
        raise HTTPException(400, 'Некорректный номер телефона')

    max_att = config.web_auth_max_attempts_per_hour
    await assert_under_limit(
        redis,
        f'web:phlogin:{phone}',
        max_att,
        3600,
    )

    user = await db.get_worker_by_phone_number(phone)

    if not user:
        # Не найден в локальной БД — проверяем у партнёра (Рабочие Руки)
        phone_10 = phone.lstrip('+')[1:]  # +79... → 9... (10 цифр)
        rr_worker = await fin_get_worker_by_phone(phone_10)
        if not rr_worker:
            raise HTTPException(
                401,
                detail={'code': 'WORKER_NOT_FOUND', 'message': 'Пользователь не найден. Пройдите регистрацию.'},
            )
        rr_inn = str(rr_worker.get('inn') or '')
        if not _inn_last4_matches(rr_inn, body.inn_last4):
            raise HTTPException(401, 'Неверный телефон или ИНН')

        # Создаём пользователя в нашей БД на основе данных партнёра
        first_name = rr_worker.get('firstName') or ''
        last_name = rr_worker.get('lastName') or ''
        middle_name = rr_worker.get('patronymic') or ''
        card = rr_worker.get('bankcardNumber') or ''
        api_worker_id = rr_worker.get('id')

        new_user_id = await db.set_user(
            api_worker_id=api_worker_id,
            card=card,
            tg_id=0,
            phone_number=phone,
            city=body.city.strip(),
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            inn=rr_inn,
            real_phone_number=phone,
            real_first_name=first_name,
            real_last_name=last_name,
            real_middle_name=middle_name,
        )
        if not new_user_id:
            # Параллельная регистрация — повторно ищем
            user = await db.get_worker_by_phone_number(phone)
            if not user:
                raise HTTPException(500, 'Ошибка создания профиля')
        else:
            user = await db.get_user_by_id(new_user_id)

    else:
        if not _inn_last4_matches(user.inn, body.inn_last4):
            raise HTTPException(401, 'Неверный телефон или ИНН')

        if user.tg_id and await db.has_block(worker_tg_id=user.tg_id):
            raise HTTPException(403, 'Доступ ограничен')

        if user.block:
            raise HTTPException(403, 'Доступ ограничен')

    # Город при входе не проверяем — сохраняем выбранный пользователем
    await db.update_user_city(user.id, body.city.strip())

    token = _issue_token(user.id)
    await _register_session(request, user.id, token)
    return token


@router.post('/logout', response_model=dict)
async def logout():
    return {'ok': True, 'message': 'Удалите токен на клиенте'}
