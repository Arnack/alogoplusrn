import logging
from typing import Optional
import aiohttp

from config_reader import config

BASE_URL = 'https://zvonok.com/manager/cabapi_external/api/v1/phones'

# Маппинг целочисленных dial_status от zvonok.com в строки
# Источник: https://github.com/ZvonokComGroup/zvonok-example-python
_DIAL_INT_TO_STR = {
    0:  'wait',
    1:  'failed',
    2:  'hangup',
    3:  'ring_timeout',
    4:  'busy',
    5:  'answered',
    6:  'robot',
    7:  'robot',
    8:  'novalid_button_dial',
    9:  'unknown',
    10: 'wed',
    11: 'stoplist_white',
    12: 'stoplist_black',
    13: 'insufficient_duration',
    14: 'itself_exc',
    15: 'removed',
    19: 'no_button',
}

# Статусы dial_status, означающие недоступность телефона → статус 'blue'
UNAVAILABLE_DIAL_STATUSES = {
    'failed', 'stoplist', 'stoplist_black', 'stoplist_white',
    'invalid', 'unknown', 'ring_timeout', 'insufficient_duration',
    'itself_exc', 'removed',
}


async def make_call(phone: str, campaign_id: str) -> Optional[str]:
    """
    Инициировать звонок через zvonok.com.
    Возвращает call_id (zvonok_call_id) или None при ошибке.
    """
    url = f'{BASE_URL}/call/'
    params = {
        'public_key': config.zvonok_api_key.get_secret_value(),
        'phone': phone,
        'campaign_id': campaign_id,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                # API возвращает call_id прямо в корне ответа (без обёртки status/data)
                if resp.status == 200 and 'call_id' in data:
                    call_id = str(data['call_id'])
                    logging.info(f'[zvonok] Звонок создан: phone={phone}, call_id={call_id}')
                    return call_id
                else:
                    logging.error(f'[zvonok] Ошибка создания звонка: {resp.status} | {data}')
                    return None
    except Exception as e:
        logging.exception(f'[zvonok] Исключение при создании звонка на {phone}: {e}')
        return None


async def get_call_status(call_id: str) -> Optional[dict]:
    """
    Получить статус звонка по call_id.
    Возвращает нормализованный dict с полями call_status, dial_status, button или None при ошибке.

    Нормализация:
      - API возвращает список [{...}] — берём первый элемент
      - button_num (int/null) → button (str '1'/'2' или None)
      - dial_status (int) → строка из _DIAL_INT_TO_STR
    """
    url = f'{BASE_URL}/call_by_id/'
    params = {
        'public_key': config.zvonok_api_key.get_secret_value(),
        'call_id': call_id,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                logging.info(f'[zvonok] Статус звонка {call_id}: {data}')
                if resp.status != 200:
                    logging.error(f'[zvonok] Ошибка получения статуса {call_id}: {resp.status} | {data}')
                    return None

                # API возвращает список или dict
                if isinstance(data, list):
                    item = data[0] if data else None
                elif isinstance(data, dict):
                    item = data
                else:
                    item = None

                if not item:
                    return None

                # Нормализуем button_num (int) → button (str)
                button_num = item.get('button_num')
                button = str(button_num) if button_num is not None else None

                # Нормализуем dial_status (int) → строка
                dial_raw = item.get('dial_status')
                if isinstance(dial_raw, int):
                    dial_status = _DIAL_INT_TO_STR.get(dial_raw, 'unknown')
                else:
                    dial_status = dial_raw  # уже строка (старый формат)

                return {
                    'call_status': item.get('call_status'),
                    'dial_status': dial_status,
                    'button': button,
                    'recognize_word': item.get('recognize_word'),
                    'user_choice': item.get('user_choice'),
                }
    except Exception as e:
        logging.exception(f'[zvonok] Исключение при опросе статуса {call_id}: {e}')
        return None


async def get_call_status_by_phone(
    campaign_id: str,
    phone: str,
    call_id: Optional[str] = None
) -> Optional[dict]:
    """
    Получить статус звонка по телефону/кампании (calls_by_phone).
    Если указан call_id — вернем только совпадающий звонок.
    """
    url = f'{BASE_URL}/calls_by_phone/'
    params = {
        'public_key': config.zvonok_api_key.get_secret_value(),
        'campaign_id': campaign_id,
        'phone': phone,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                logging.info(f'[zvonok] Статус по телефону {phone}: {data}')
                if resp.status != 200:
                    logging.error(f'[zvonok] Ошибка получения статуса по телефону {phone}: {resp.status} | {data}')
                    return None

                if not isinstance(data, list) or not data:
                    return None

                item = None
                if call_id:
                    for row in data:
                        if str(row.get('call_id')) == str(call_id):
                            item = row
                            break
                if not item:
                    item = data[0]

                button_num = item.get('button_num')
                button = str(button_num) if button_num is not None else None

                dial_raw = item.get('dial_status')
                if isinstance(dial_raw, int):
                    dial_status = _DIAL_INT_TO_STR.get(dial_raw, 'unknown')
                else:
                    dial_status = dial_raw

                return {
                    'call_status': item.get('call_status') or item.get('status'),
                    'dial_status': dial_status,
                    'button': button,
                    'recognize_word': item.get('recognize_word'),
                    'user_choice': item.get('user_choice'),
                }
    except Exception as e:
        logging.exception(f'[zvonok] Исключение при опросе по телефону {phone}: {e}')
        return None


def map_zvonok_status(
    call_status: Optional[str],
    dial_status: Optional[str],
    button: Optional[str],
    recognize_word: Optional[str] = None,
    user_choice: Optional[str] = None
) -> str:
    """
    Маппинг статусов zvonok.com на внутренние:
    green  🟢 — подтвердил (кнопка 1 или голос "да"/"УСПЕХ")
    red    🔴 — отказался (кнопка 2 или голос "нет")
    blue   🔵 — телефон недоступен
    yellow 🟡 — не взял трубку (все попытки исчерпаны)
    pending    — звонок ещё не завершён
    """
    if button == '1':
        return 'green'
    if button == '2':
        return 'red'
    
    # Приоритет на user_choice (результат обработки IVR), fallback на recognize_word
    # Проверяем вхождение подстроки для гибкости (может быть "Нет", "нет", "НЕТ" и т.д.)
    choice_raw = user_choice or recognize_word or ''
    choice = choice_raw.strip().lower()
    
    # Проверяем вхождение ключевых слов (не точное совпадение)
    if 'нет' in choice or 'no' in choice:
        return 'red'
    if 'да' in choice or 'yes' in choice or 'успех' in choice:
        return 'green'
    
    if call_status in ('attempts_exc', 'compl_finished', 'compl_nofinished', 'novalid_button'):
        # Все попытки сделаны, кнопка не нажата
        return 'yellow'
    if dial_status in UNAVAILABLE_DIAL_STATUSES:
        return 'blue'
    return 'pending'
