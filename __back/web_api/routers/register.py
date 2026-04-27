from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import time
import uuid

from fastapi import APIRouter, HTTPException, Request

import database as db
from API.fin.workers import (
    fin_check_fns_status,
    fin_create_worker,
    fin_get_worker_by_card,
    fin_get_worker_by_inn,
    fin_get_worker_by_phone,
)
from config_reader import config
from utils.phone import normalize_phone_number
from utils.sms_sender import send_sms_with_api
from web_api.schemas import (
    RegSendSmsBody,
    RegSendSmsResponse,
    RegStatusBody,
    RegSubmitBody,
    RegSubmitResponse,
    RegValidateBody,
    RegValidateResponse,
    RegVerifySmsBody,
    RegVerifySmsResponse,
    TokenResponse,
)
from web_api.security.jwt_util import create_access_token, decode_access_token

router = APIRouter()
logger = logging.getLogger(__name__)

_SMS_CODE_TTL = 900       # 15 минут
_VERIFIED_TTL = 3600      # 60 минут — время на заполнение формы после SMS
_REG_DATA_TTL = 7200      # 2 часа — время ожидания FNS статуса


# ── helpers ──────────────────────────────────────────────────

def _hash_code(code: str) -> tuple[str, str]:
    """Возвращает (salt, hash) для SMS-кода."""
    salt = os.urandom(16).hex()
    h = hashlib.pbkdf2_hmac('sha256', code.encode(), salt.encode(), 100_000)
    return salt, h.hex()


def _verify_code_hash(code: str, salt: str, stored_hash: str) -> bool:
    h = hashlib.pbkdf2_hmac('sha256', code.encode(), salt.encode(), 100_000)
    return h.hex() == stored_hash


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
    return TokenResponse(access_token=token, expires_in=minutes * 60)


async def _register_session(request: Request, user_id: int, token_response: TokenResponse) -> None:
    ip = request.client.host if request.client else 'unknown'
    try:
        await db.update_user_last_web_ip(user_id=user_id, ip=ip)
    except Exception as exc:
        logger.warning('[reg-session] update_last_web_ip user=%s: %s', user_id, exc)

    redis = getattr(request.app.state, 'redis', None)
    if redis:
        try:
            secret = config.web_jwt_secret
            payload = decode_access_token(token_response.access_token, secret.get_secret_value())
            iat = payload.get('iat', int(time.time()))
            ttl = config.web_jwt_expire_minutes * 60
            await redis.set(f'web_session:{user_id}', str(iat), ex=ttl)
        except Exception as exc:
            logger.warning('[reg-session] redis write user=%s: %s', user_id, exc)


# ── endpoints ─────────────────────────────────────────────────

@router.post('/validate', response_model=RegValidateResponse)
async def validate_fields(body: RegValidateBody):
    """Проверяет уникальность ИНН, телефона и номера карты."""
    resp = RegValidateResponse()

    if body.inn:
        # Проверяем в локальной БД
        existing = await db.get_worker_by_inn(body.inn)
        if existing:
            resp.inn_ok = False
            resp.inn_error = 'С таким ИНН уже есть исполнитель на платформе. Используйте функцию входа.'
        else:
            # Проверяем у партнёра (глобальная база РР)
            rr = await fin_get_worker_by_inn(body.inn)
            if rr:
                resp.inn_ok = False
                resp.inn_error = 'Ваш ИНН уже есть в базе «Рабочие Руки». Для регистрации обратитесь в поддержку: https://t.me/helpmealgoritm'

    if body.phone:
        phone = normalize_phone_number(body.phone)
        if phone:
            existing = await db.get_worker_by_phone_number(phone)
            if existing:
                resp.phone_ok = False
                resp.phone_error = 'Такой номер телефона уже зарегистрирован. Введите другой номер.'

    if body.card:
        card = body.card.replace(' ', '')
        existing = await db.card_unique(card)
        if existing:
            resp.card_ok = False
            resp.card_error = 'Такой номер карты уже используется другим исполнителем. Введите другой номер карты.'
        else:
            rr = await fin_get_worker_by_card(card)
            if rr:
                resp.card_ok = False
                resp.card_error = 'Такой номер карты уже используется другим исполнителем. Введите другой номер карты.'

    return resp


@router.post('/send-sms', response_model=RegSendSmsResponse)
async def send_sms(body: RegSendSmsBody, request: Request):
    """Отправляет SMS с кодом подтверждения на указанный телефон."""
    phone = normalize_phone_number(body.phone)
    if not phone:
        raise HTTPException(400, 'Некорректный номер телефона')

    # SMS не отправляем, если телефон уже зарегистрирован в локальной БД
    existing = await db.get_worker_by_phone_number(phone)
    if existing:
        raise HTTPException(
            409,
            detail={'code': 'PHONE_EXISTS', 'message': 'Такой номер телефона уже зарегистрирован. Введите другой номер.'},
        )

    # Также проверяем в fin API — не тратим SMS зря
    phone_10 = phone.lstrip('+')[1:]
    rr_by_phone = await fin_get_worker_by_phone(phone_10)
    if rr_by_phone:
        raise HTTPException(
            409,
            detail={'code': 'PHONE_EXISTS', 'message': 'Такой номер телефона уже зарегистрирован. Введите другой номер.'},
        )

    # Рейт-лимит через БД — та же логика что в Telegram-боте
    can_send = await db.check_daily_code_attempts(phone_number=phone)
    if not can_send:
        raise HTTPException(429, 'Слишком много попыток. Попробуйте позже.')

    code = str(random.randint(100000, 999999))
    salt, code_hash = _hash_code(code)
    code_id = str(uuid.uuid4())

    redis = getattr(request.app.state, 'redis', None)
    if redis:
        payload = json.dumps({'phone': phone, 'code_hash': code_hash, 'salt': salt})
        await redis.set(f'web_reg_code:{code_id}', payload, ex=_SMS_CODE_TTL)
    else:
        logger.warning('[register] Redis недоступен, SMS-код не будет сохранён')

    # Отправляем SMS через IQSMS
    try:
        phone_for_sms = phone.lstrip('+')  # iqsms ожидает без +
        await send_sms_with_api(
            phone_number=phone_for_sms,
            message_text=f'Код подтверждения AlgoritmPlus: {code}',
            tg_id=0,
        )
    except Exception as exc:
        logger.error('[register] Ошибка отправки SMS на %s: %s', phone, exc)
        raise HTTPException(500, 'Не удалось отправить SMS. Попробуйте позже.')

    return RegSendSmsResponse(code_id=code_id)


@router.post('/verify-sms', response_model=RegVerifySmsResponse)
async def verify_sms(body: RegVerifySmsBody, request: Request):
    """Проверяет SMS-код и помечает телефон как подтверждённый."""
    redis = getattr(request.app.state, 'redis', None)
    if not redis:
        raise HTTPException(500, 'Сервис временно недоступен')

    raw = await redis.get(f'web_reg_code:{body.code_id}')
    if not raw:
        raise HTTPException(400, 'Код устарел или не существует. Запросите новый.')

    data = json.loads(raw)
    if not _verify_code_hash(body.code.strip(), data['salt'], data['code_hash']):
        raise HTTPException(400, 'Неверный код. Попробуйте ещё раз.')

    phone = data['phone']
    await redis.delete(f'web_reg_code:{body.code_id}')
    # Помечаем телефон как верифицированный
    await redis.set(f'web_reg_verified:{phone}', '1', ex=_VERIFIED_TTL)

    return RegVerifySmsResponse(ok=True, phone=phone)


@router.post('/submit', response_model=RegSubmitResponse)
async def submit_registration(body: RegSubmitBody, request: Request):
    """
    Создаёт работника у партнёра (fin API).
    Если FNS-статус уже подтверждён → создаёт пользователя в нашей БД и возвращает токен.
    Если нет → возвращает api_worker_id для дальнейшей проверки.
    """
    redis = getattr(request.app.state, 'redis', None)

    phone = normalize_phone_number(body.phone)
    if not phone:
        raise HTTPException(400, 'Некорректный номер телефона')

    # Проверяем, что SMS был подтверждён
    if redis:
        verified = await redis.get(f'web_reg_verified:{phone}')
        if not verified:
            raise HTTPException(400, 'Телефон не подтверждён. Пройдите SMS-верификацию заново.')

    # Финальная проверка уникальности
    if await db.get_worker_by_phone_number(phone):
        raise HTTPException(
            409,
            detail={'code': 'PHONE_EXISTS', 'message': 'Такой номер телефона уже зарегистрирован. Используйте вход.'},
        )
    if await db.get_worker_by_inn(body.inn):
        raise HTTPException(
            409,
            detail={'code': 'INN_EXISTS', 'message': 'С таким ИНН уже есть исполнитель на платформе. Используйте функцию входа.'},
        )
    rr_inn_check = await fin_get_worker_by_inn(body.inn)
    if rr_inn_check:
        raise HTTPException(
            409,
            detail={'code': 'INN_RR_EXISTS', 'message': 'Ваш ИНН уже есть в базе «Рабочие Руки». Для регистрации обратитесь в поддержку: https://t.me/helpmealgoritm'},
        )
    card = body.card.replace(' ', '')
    if await db.card_unique(card):
        raise HTTPException(
            409,
            detail={'code': 'CARD_EXISTS', 'message': 'Такой номер карты уже используется другим исполнителем. Введите другой номер карты.'},
        )

    # Номер телефона для fin API: 10 цифр без кода страны
    phone_10 = phone.lstrip('+')[1:]  # +79... → 9...

    # Создаём работника в fin API
    api_worker_id = await fin_create_worker(
        phone_number=phone_10,
        inn=body.inn,
        card_number=card,
        first_name=body.first_name,
        last_name=body.last_name,
        patronymic=body.middle_name or None,
        birthday=body.birth_date,
        passport_series=body.passport_series,
        passport_number=body.passport_number,
        passport_issue_date=body.passport_date,
    )

    if not api_worker_id:
        raise HTTPException(500, 'Не удалось создать профиль у партнёра. Попробуйте позже.')

    # Сохраняем данные формы в Redis для использования при активации
    if redis:
        reg_data = {
            'phone': phone,
            'city': body.city,
            'last_name': body.last_name,
            'first_name': body.first_name,
            'middle_name': body.middle_name,
            'birth_date': body.birth_date,
            'inn': body.inn,
            'card': card,
            'passport_series': body.passport_series,
            'passport_number': body.passport_number,
            'passport_date': body.passport_date,
        }
        await redis.set(
            f'web_reg_data:{api_worker_id}',
            json.dumps(reg_data),
            ex=_REG_DATA_TTL,
        )

    # Инициируем запрос на проверку СМЗ-статуса в РР, но НЕ выдаём токен немедленно.
    # Подтверждение от ФНС через РР асинхронное — доступ только после явного
    # получения ответа через /check-status.
    await fin_check_fns_status(api_worker_id)

    return RegSubmitResponse(status='pending', api_worker_id=api_worker_id)


@router.post('/check-status', response_model=RegSubmitResponse)
async def check_status(body: RegStatusBody, request: Request):
    """
    Повторная проверка FNS-статуса (кнопка «Проверить ещё раз»).
    Если подтверждён → создаёт пользователя в БД и возвращает токен.
    """
    redis = getattr(request.app.state, 'redis', None)

    phone = normalize_phone_number(body.phone)
    if not phone:
        raise HTTPException(400, 'Некорректный номер телефона')

    # Проверяем, не зарегистрировался ли уже (параллельный запрос)
    existing = await db.get_worker_by_phone_number(phone)
    if existing:
        token = _issue_token(existing.id)
        await _register_session(request, existing.id, token)
        return RegSubmitResponse(
            status='done',
            api_worker_id=body.api_worker_id,
            access_token=token.access_token,
            expires_in=token.expires_in,
        )

    _, is_smz = await fin_check_fns_status(body.api_worker_id)

    if not is_smz:
        return RegSubmitResponse(status='pending', api_worker_id=body.api_worker_id)

    # Создаём пользователя в БД
    card = body.card.replace(' ', '')
    user_id = await _create_local_user(body.api_worker_id, phone, body, card, request)
    if not user_id:
        raise HTTPException(500, 'Ошибка создания профиля в системе')

    token = _issue_token(user_id)
    await _register_session(request, user_id, token)
    return RegSubmitResponse(
        status='done',
        api_worker_id=body.api_worker_id,
        access_token=token.access_token,
        expires_in=token.expires_in,
    )


async def _create_local_user(
    api_worker_id: int,
    phone: str,
    body,  # RegSubmitBody | RegStatusBody
    card: str,
    request: Request,
) -> int | None:
    """Создаёт запись пользователя в локальной БД."""
    return await db.set_user(
        api_worker_id=api_worker_id,
        card=card,
        tg_id=0,
        phone_number=phone,
        city=body.city,
        first_name=body.first_name,
        last_name=body.last_name,
        middle_name=body.middle_name or '',
        inn=body.inn,
        real_phone_number=phone,
        real_first_name=body.first_name,
        real_last_name=body.last_name,
        real_middle_name=body.middle_name or '',
        passport_series=body.passport_series,
        passport_number=body.passport_number,
        passport_issue_date=body.passport_date,
    )
