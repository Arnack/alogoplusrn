"""Серверное состояние сценария «Заявка для друга» (web-панель)."""
from __future__ import annotations

import secrets
import threading
from typing import Any

import database as db
import API
from utils import (
    check_code,
    create_code_hash,
    normalize_phone_number,
    schedule_delete_code_for_order,
    send_sms_with_api,
)
from utils.worker_validators import validate_inn
import texts as txt


_lock = threading.Lock()
# user_id (подписант) -> поля сессии
_sessions: dict[int, dict[str, Any]] = {}
# после успешного кода: подписант -> (friend_worker_id, city)
_verified_friend: dict[int, tuple[int, str]] = {}


def _sess_get(user_id: int) -> dict[str, Any] | None:
    with _lock:
        return _sessions.get(user_id)


def _sess_put(user_id: int, data: dict[str, Any]) -> None:
    with _lock:
        _sessions[user_id] = data


def _sess_clear(user_id: int) -> None:
    with _lock:
        _sessions.pop(user_id, None)


def clear_friend_session(user_id: int) -> None:
    _sess_clear(user_id)


def clear_friend_verified(user_id: int) -> None:
    with _lock:
        _verified_friend.pop(user_id, None)


def set_friend_verified(user_id: int, friend_id: int, city: str) -> None:
    with _lock:
        _verified_friend[user_id] = (friend_id, city)


def get_friend_verified(user_id: int) -> tuple[int, str] | None:
    with _lock:
        return _verified_friend.get(user_id)


async def _send_sms_step(log_tg_id: int, phone: str, first: str, middle: str, last: str) -> int:
    code = str(secrets.randbelow(900000) + 100000)
    hashed = create_code_hash(code=code)
    code_id = await db.set_code_for_order(code_hash=hashed['hash'], salt=hashed['salt'])
    await schedule_delete_code_for_order(code_id=code_id)
    await send_sms_with_api(
        phone_number=phone,
        message_text=txt.code_text_for_message(code=code),
        tg_id=log_tg_id,
    )
    return code_id


async def lookup_phone(signer_id: int, raw_phone: str) -> dict[str, Any]:
    phone = normalize_phone_number(raw_phone)
    if not phone:
        return {'ok': False, 'message': 'Введите корректный номер телефона', 'step': 'idle'}

    _sess_clear(signer_id)
    clear_friend_verified(signer_id)

    friend = await db.get_worker_by_phone_number(phone_number=phone)
    if friend:
        real = await db.get_user_real_data_by_id(user_id=friend.id)
        if not await db.check_daily_code_attempts(phone_number=real.phone_number):
            return {'ok': False, 'message': 'Лимит SMS на сегодня исчерпан. Попробуйте завтра.', 'step': 'idle'}
        cities = await db.get_cities_name()
        label = f'{real.last_name} {real.first_name} {real.middle_name}'.strip()
        _sess_put(
            signer_id,
            {
                'step': 'need_city',
                'choose_city_action': 'RegWorker',
                'friend_id': friend.id,
                'phone_number': real.phone_number,
                'first_name': real.first_name,
                'middle_name': real.middle_name,
                'last_name': real.last_name,
                'code_attempts': 0,
                'friend_label': label,
            },
        )
        return {
            'ok': True,
            'step': 'need_city',
            'message': 'Выберите город друга для поиска заявок.',
            'cities': cities,
            'friend_label': label,
        }

    worker = await API.get_worker_by_phone_number_or_inn(value=phone.lstrip('+'))

    if not worker:
        return {'ok': False, 'message': 'Исполнитель не найден в базе и в сервисе «Рабочие руки».', 'step': 'idle'}

    cities = await db.get_cities_name()
    label = f"{worker.get('lastName', '')} {worker.get('firstName', '')}".strip()
    _sess_put(
        signer_id,
        {
            'step': 'need_city',
            'choose_city_action': 'NewWorker',
            'phone_number': f"+7{worker.get('phone', '')}",
            'first_name': worker.get('firstName', ''),
            'middle_name': worker.get('patronymic', '') or '',
            'last_name': worker.get('lastName', ''),
            'inn': worker.get('inn', ''),
            'api_worker_id': worker['id'],
            'worker_card': worker.get('bankcardNumber', '') or '',
            'code_attempts': 0,
            'friend_label': label,
        },
    )
    return {
        'ok': True,
        'step': 'need_city',
        'message': 'Выберите город друга. После выбора друг будет добавлен в базу и получит SMS-код.',
        'cities': cities,
        'friend_label': label,
    }


async def lookup_inn(signer_id: int, inn_raw: str) -> dict[str, Any]:
    inn = inn_raw.strip()
    if not inn.isdigit() or not validate_inn(inn):
        return {'ok': False, 'message': 'Введите корректный ИНН (12 цифр).', 'step': 'idle'}

    _sess_clear(signer_id)
    clear_friend_verified(signer_id)

    friend = await db.get_worker_by_inn(inn=inn)
    if friend:
        real = await db.get_user_real_data_by_id(user_id=friend.id)
        if not await db.check_daily_code_attempts(phone_number=real.phone_number):
            return {'ok': False, 'message': 'Лимит SMS на сегодня исчерпан. Попробуйте завтра.', 'step': 'idle'}
        cities = await db.get_cities_name()
        label = f'{real.last_name} {real.first_name} {real.middle_name}'.strip()
        _sess_put(
            signer_id,
            {
                'step': 'need_city',
                'choose_city_action': 'RegWorker',
                'friend_id': friend.id,
                'phone_number': real.phone_number,
                'first_name': real.first_name,
                'middle_name': real.middle_name,
                'last_name': real.last_name,
                'code_attempts': 0,
                'friend_label': label,
            },
        )
        return {
            'ok': True,
            'step': 'need_city',
            'message': 'Выберите город друга для поиска заявок.',
            'cities': cities,
            'friend_label': label,
        }

    worker = await API.get_worker_by_phone_number_or_inn(value=inn)
    if not worker:
        return {'ok': False, 'message': 'Исполнитель с таким ИНН не найден.', 'step': 'idle'}

    cities = await db.get_cities_name()
    label = f"{worker.get('lastName', '')} {worker.get('firstName', '')}".strip()
    _sess_put(
        signer_id,
        {
            'step': 'need_city',
            'choose_city_action': 'NewWorker',
            'phone_number': f"+7{worker.get('phone', '')}",
            'first_name': worker.get('firstName', ''),
            'middle_name': worker.get('patronymic', '') or '',
            'last_name': worker.get('lastName', ''),
            'inn': worker.get('inn', ''),
            'api_worker_id': worker['id'],
            'worker_card': worker.get('bankcardNumber', '') or '',
            'code_attempts': 0,
            'friend_label': label,
        },
    )
    return {
        'ok': True,
        'step': 'need_city',
        'message': 'Выберите город друга.',
        'cities': cities,
        'friend_label': label,
    }


async def set_city_and_send_code(signer_id: int, city: str, log_tg_id: int) -> dict[str, Any]:
    s = _sess_get(signer_id)
    if not s or s.get('step') != 'need_city':
        return {'ok': False, 'message': 'Сначала найдите друга по телефону или ИНН.', 'step': 'idle'}

    action = s['choose_city_action']
    if action == 'NewWorker':
        friend_id = await db.set_user(
            api_worker_id=s['api_worker_id'],
            card=s['worker_card'],
            tg_id=0,
            username=None,
            phone_number=s['phone_number'],
            city=city,
            first_name=s['first_name'],
            middle_name=s['middle_name'],
            last_name=s['last_name'],
            inn=s['inn'],
            real_phone_number=s['phone_number'],
            real_first_name=s['first_name'],
            real_last_name=s['last_name'],
            real_middle_name=s['middle_name'],
        )
        if not friend_id:
            return {'ok': False, 'message': 'Не удалось создать профиль друга.', 'step': 'need_city'}
        if not await db.check_daily_code_attempts(phone_number=s['phone_number']):
            return {'ok': False, 'message': 'Лимит SMS на сегодня исчерпан.', 'step': 'need_city'}
        code_id = await _send_sms_step(
            log_tg_id,
            s['phone_number'],
            s['first_name'],
            s['middle_name'],
            s['last_name'],
        )
        s.update(
            {
                'step': 'need_code',
                'friend_id': friend_id,
                'friend_city': city,
                'code_for_order_id': code_id,
                'code_attempts': 1,
            },
        )
        _sess_put(signer_id, s)
        return {'ok': True, 'step': 'need_code', 'message': 'Код отправлен в SMS. Введите его ниже.'}

    # RegWorker — лимит SMS уже проверен при поиске друга
    code_id = await _send_sms_step(
        log_tg_id,
        s['phone_number'],
        s['first_name'],
        s['middle_name'],
        s['last_name'],
    )
    s.update(
        {
            'step': 'need_code',
            'friend_city': city,
            'code_for_order_id': code_id,
            'code_attempts': 1,
        },
    )
    _sess_put(signer_id, s)
    return {'ok': True, 'step': 'need_code', 'message': 'Код отправлен в SMS. Введите его ниже.'}


async def verify_code(signer_id: int, raw_code: str) -> dict[str, Any]:
    s = _sess_get(signer_id)
    if not s or s.get('step') != 'need_code':
        return {'ok': False, 'message': 'Нет активного запроса кода.', 'step': 'idle'}

    if not raw_code.isdigit():
        return {'ok': False, 'message': 'Код должен содержать только цифры.', 'step': 'need_code'}

    code_data = await db.get_code_for_order(code_id=s['code_for_order_id'])
    if not code_data:
        _sess_clear(signer_id)
        return {'ok': False, 'message': 'Код устарел. Запросите новый, начав поиск заново.', 'step': 'idle'}

    ok = check_code(salt=code_data.salt, hashed_code=code_data.code_hash, entered_code=raw_code)
    if ok:
        await db.delete_code_for_order(code_id=code_data.id)
        friend_id = s['friend_id']
        friend_city = s['friend_city']
        set_friend_verified(signer_id, friend_id, friend_city)
        _sess_clear(signer_id)
        return {
            'ok': True,
            'step': 'verified',
            'message': 'Друг подтверждён. В разделе «Поиск заявок» включите режим «За друга» и выберите заявку.',
            'friend_id': friend_id,
            'friend_city': friend_city,
        }

    attempts = int(s.get('code_attempts', 1))
    if attempts >= 3:
        await db.delete_code_for_order(code_id=code_data.id)
        _sess_clear(signer_id)
        return {'ok': False, 'message': 'Слишком много неверных попыток. Начните сценарий заново.', 'step': 'idle'}

    s['code_attempts'] = attempts + 1
    _sess_put(signer_id, s)
    return {'ok': False, 'message': 'Неверный код. Попробуйте ещё раз.', 'step': 'need_code'}


async def friend_progress(user_id: int) -> dict[str, Any]:
    vf = get_friend_verified(user_id)
    if vf:
        _fid, city = vf
        return {
            'step': 'verified',
            'message': f'Режим «за друга» активен (город: {city}).',
            'cities': [],
            'friend_label': None,
        }
    s = _sess_get(user_id)
    if not s:
        return {'step': 'idle', 'message': '', 'cities': [], 'friend_label': None}
    cities: list[str] = []
    if s.get('step') == 'need_city':
        cities = await db.get_cities_name()
    return {
        'step': s.get('step', 'idle'),
        'message': '',
        'cities': cities,
        'friend_label': s.get('friend_label'),
    }
