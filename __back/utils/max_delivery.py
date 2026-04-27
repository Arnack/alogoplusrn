import logging
import json
from pathlib import Path
from typing import Any


_DIALOG_CHAT_CACHE: dict[int, int] = {}
_CACHE_PATH = Path(__file__).resolve().parents[1] / 'data' / 'max_dialog_cache.json'


def _load_persistent_cache() -> dict[int, int]:
    if not _CACHE_PATH.exists():
        return {}
    try:
        raw = json.loads(_CACHE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result: dict[int, int] = {}
    for key, value in raw.items():
        try:
            result[int(key)] = int(value)
        except Exception:
            continue
    return result


def _save_persistent_cache(cache: dict[int, int]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps({str(k): v for k, v in cache.items()}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def remember_dialog(max_user_id: int | None, chat_id: int | None) -> None:
    if not max_user_id or not chat_id:
        return
    _DIALOG_CHAT_CACHE[max_user_id] = chat_id
    try:
        persistent = _load_persistent_cache()
        persistent[max_user_id] = chat_id
        _save_persistent_cache(persistent)
    except Exception as exc:
        logging.warning('[max] failed to persist dialog cache for user_id=%s: %s', max_user_id, exc)
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        loop.create_task(_persist_dialog(max_user_id, chat_id))
    except Exception:
        pass


def remember_dialog_from_event(event: Any) -> None:
    try:
        message = getattr(event, 'message', None)
        recipient = getattr(message, 'recipient', None)
        chat_id = getattr(recipient, 'chat_id', None)
        from_user = getattr(event, 'from_user', None)
        user_id = getattr(from_user, 'user_id', None)
        if user_id is None:
            callback = getattr(event, 'callback', None)
            callback_user = getattr(callback, 'user', None)
            user_id = getattr(callback_user, 'user_id', None)
        remember_dialog(user_id, chat_id)
    except Exception:
        return


def _extract_error_code(exc: Exception) -> str:
    raw = getattr(exc, 'raw', None)
    if isinstance(raw, dict):
        code = raw.get('code')
        if code:
            return str(code).lower()
    return str(exc).lower()


def is_dialog_unavailable_error(exc: Exception) -> bool:
    error_text = _extract_error_code(exc)
    return (
        'chat.denied' in error_text
        or 'dialog.suspended' in error_text
        or '403' in error_text
    )


async def find_dialog_chat_id(bot: Any, user_id: int) -> int | None:
    cached = _DIALOG_CHAT_CACHE.get(user_id)
    if cached:
        return cached
    persistent = _load_persistent_cache()
    cached = persistent.get(user_id)
    if cached:
        _DIALOG_CHAT_CACHE[user_id] = cached
        return cached

    marker = None
    for _ in range(20):
        chats = await bot.get_chats(count=100, marker=marker)
        for chat in chats.chats:
            dialog_user = getattr(chat, 'dialog_with_user', None)
            dialog_user_id = getattr(dialog_user, 'user_id', None)
            if dialog_user_id == user_id and getattr(chat, 'chat_id', None):
                remember_dialog(user_id, chat.chat_id)
                return chat.chat_id

        marker = getattr(chats, 'marker', None)
        if not marker:
            break

    return None


async def send_max_message(
    bot: Any,
    *,
    user_id: int,
    chat_id: int | None = None,
    text: str,
    attachments: list[Any] | None = None,
    parse_mode: Any = None,
) -> Any:
    cached_chat_id = chat_id or await find_dialog_chat_id(bot, user_id)
    if cached_chat_id:
        try:
            return await bot.send_message(
                chat_id=cached_chat_id,
                text=text,
                attachments=attachments,
                parse_mode=parse_mode,
            )
        except Exception as exc:
            if not is_dialog_unavailable_error(exc):
                raise

    try:
        return await bot.send_message(
            user_id=user_id,
            text=text,
            attachments=attachments,
            parse_mode=parse_mode,
        )
    except Exception as exc:
        if not is_dialog_unavailable_error(exc):
            raise

        chat_id = await find_dialog_chat_id(bot, user_id)
        if not chat_id:
            raise

        logging.info(
            '[max] send_message fallback to chat_id=%s for user_id=%s',
            chat_id,
            user_id,
        )
        return await bot.send_message(
            chat_id=chat_id,
            text=text,
            attachments=attachments,
            parse_mode=parse_mode,
        )


async def _persist_dialog(max_user_id: int, chat_id: int) -> None:
    try:
        import database as db
        worker = await db.get_worker_by_max_id(max_id=max_user_id)
        if worker:
            current_chat_id = getattr(worker, 'max_chat_id', 0) or 0
            if current_chat_id != chat_id:
                await db.update_worker_max_id(
                    worker_id=worker.id,
                    max_id=max_user_id,
                    max_chat_id=chat_id,
                )
    except Exception as exc:
        logging.warning('[max] failed to persist dialog in db for user_id=%s: %s', max_user_id, exc)
