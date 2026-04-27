import pytest
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


_MODULE_PATH = Path(__file__).resolve().parents[1] / 'utils' / 'max_delivery.py'
_SPEC = importlib.util.spec_from_file_location('test_max_delivery_module', _MODULE_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MODULE)

find_dialog_chat_id = _MODULE.find_dialog_chat_id
send_max_message = _MODULE.send_max_message
remember_dialog = _MODULE.remember_dialog


class FakeMaxError(Exception):
    def __init__(self, code: str):
        self.raw = {'code': code}
        super().__init__(code)


@pytest.mark.asyncio
async def test_find_dialog_chat_id_returns_matching_dialog(tmp_path):
    _MODULE._DIALOG_CHAT_CACHE.clear()
    _MODULE._CACHE_PATH = tmp_path / 'max_dialog_cache.json'
    bot = MagicMock()
    target_user_id = 41632388

    dialog_user = MagicMock()
    dialog_user.user_id = target_user_id

    chat = MagicMock()
    chat.chat_id = 236002616
    chat.dialog_with_user = dialog_user

    chats_page = MagicMock()
    chats_page.chats = [chat]
    chats_page.marker = None
    bot.get_chats = AsyncMock(return_value=chats_page)

    result = await find_dialog_chat_id(bot, target_user_id)

    assert result == 236002616


@pytest.mark.asyncio
async def test_send_max_message_falls_back_to_chat_id(tmp_path):
    _MODULE._DIALOG_CHAT_CACHE.clear()
    _MODULE._CACHE_PATH = tmp_path / 'max_dialog_cache.json'
    bot = MagicMock()
    target_user_id = 41632389
    target_chat_id = 236002616

    dialog_user = MagicMock()
    dialog_user.user_id = target_user_id

    chat = MagicMock()
    chat.chat_id = target_chat_id
    chat.dialog_with_user = dialog_user

    empty_page = MagicMock()
    empty_page.chats = []
    empty_page.marker = None

    chats_page = MagicMock()
    chats_page.chats = [chat]
    chats_page.marker = None

    bot.get_chats = AsyncMock(side_effect=[empty_page, chats_page])
    bot.send_message = AsyncMock(side_effect=[
        FakeMaxError('chat.denied'),
        {'ok': True},
    ])

    result = await send_max_message(
        bot,
        user_id=target_user_id,
        text='test',
    )

    assert result == {'ok': True}
    assert bot.send_message.await_args_list[0].kwargs['user_id'] == target_user_id
    assert bot.send_message.await_args_list[1].kwargs['chat_id'] == target_chat_id


@pytest.mark.asyncio
async def test_send_max_message_uses_cached_chat_id_first(tmp_path):
    _MODULE._DIALOG_CHAT_CACHE.clear()
    _MODULE._CACHE_PATH = tmp_path / 'max_dialog_cache.json'
    bot = MagicMock()
    target_user_id = 41632391
    target_chat_id = 236002617

    remember_dialog(target_user_id, target_chat_id)
    bot.send_message = AsyncMock(return_value={'ok': True})

    result = await send_max_message(
        bot,
        user_id=target_user_id,
        text='test',
    )

    assert result == {'ok': True}
    assert bot.send_message.await_args_list[0].kwargs['chat_id'] == target_chat_id


@pytest.mark.asyncio
async def test_send_max_message_raises_when_dialog_not_found(tmp_path):
    _MODULE._DIALOG_CHAT_CACHE.clear()
    _MODULE._CACHE_PATH = tmp_path / 'max_dialog_cache.json'
    bot = MagicMock()
    target_user_id = 41632390

    chats_page = MagicMock()
    chats_page.chats = []
    chats_page.marker = None

    bot.get_chats = AsyncMock(return_value=chats_page)
    bot.send_message = AsyncMock(side_effect=FakeMaxError('chat.denied'))

    with pytest.raises(FakeMaxError):
        await send_max_message(
            bot,
            user_id=target_user_id,
            text='test',
        )
