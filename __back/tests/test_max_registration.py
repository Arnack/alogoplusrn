"""
Unit tests for Max bot registration handlers.

Tests are fully isolated — no DB, no network.
All external dependencies are replaced with MagicMock / AsyncMock.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers: build fake event / context objects
# ---------------------------------------------------------------------------

def make_event(text: str = '', user_id: int = 12345, username: str = 'testuser'):
    """Build a minimal fake MessageCreated-like object."""
    event = MagicMock()
    event.from_user.user_id = user_id
    event.from_user.username = username
    event.message.body.text = text
    event.message.answer = AsyncMock()
    event.bot.send_message = AsyncMock()
    event.bot.edit_message = AsyncMock()
    return event


def make_context(data: dict = None, state=None):
    """Build a minimal fake MemoryContext-like object."""
    ctx = MagicMock()
    _data = dict(data or {})
    _state = [state]

    async def _get_data():
        return dict(_data)

    async def _update_data(**kwargs):
        _data.update(kwargs)

    async def _set_state(s):
        _state[0] = s

    async def _clear():
        _data.clear()
        _state[0] = None

    ctx.get_data = _get_data
    ctx.update_data = _update_data
    ctx.set_state = _set_state
    ctx.clear = _clear
    ctx._data = _data       # expose for assertions
    ctx._state = _state     # expose for assertions
    return ctx


def make_worker(id=1, tg_id=0, max_id=0, inn='', phone_number='', card=''):
    """Build a minimal fake User DB object."""
    w = MagicMock()
    w.id = id
    w.tg_id = tg_id
    w.max_id = max_id
    w.inn = inn
    w.phone_number = phone_number
    w.card = card
    return w


# ---------------------------------------------------------------------------
# Patch paths (relative to the module under test)
# ---------------------------------------------------------------------------

HANDLERS = 'max_worker_bot.handlers.registration_handlers'


# ===========================================================================
# reg_get_inn — handler for RegistrationStates.reg_inn
# ===========================================================================

class TestRegGetInn:
    """Tests for reg_get_inn — INN entry during new registration flow."""

    @pytest.mark.asyncio
    async def test_invalid_inn_too_short(self):
        """Non-12-digit input → error message, stay in state."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='123')
        ctx = make_context()

        with patch(f'{HANDLERS}.txt') as mock_txt:
            mock_txt.registration_inn_error.return_value = 'Ошибка ИНН'
            await reg_get_inn(event, ctx)

        event.message.answer.assert_called_once()
        assert ctx._state[0] is None  # state unchanged

    @pytest.mark.asyncio
    async def test_invalid_inn_not_digits(self):
        """Letters in INN → error message."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='12345678901a')
        ctx = make_context()

        with patch(f'{HANDLERS}.txt') as mock_txt:
            mock_txt.registration_inn_error.return_value = 'Ошибка ИНН'
            await reg_get_inn(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_inn_found_in_db_with_max_id_already_linked(self):
        """INN exists in DB and already has max_id → show error, clear."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='460502663875')
        ctx = make_context()
        worker = make_worker(id=1, max_id=99999, inn='460502663875')

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.get_worker_by_inn = AsyncMock(return_value=worker)
            mock_txt.reg_error_inn_exists.return_value = 'ИНН уже зарегистрирован'

            await reg_get_inn(event, ctx)

        event.message.answer.assert_called_once()
        # update_worker_max_id must NOT be called
        mock_db.update_worker_max_id.assert_not_called()
        # context cleared
        assert ctx._state[0] is None

    @pytest.mark.asyncio
    async def test_inn_found_in_db_without_max_id_links_account(self):
        """INN found in DB with max_id=0 → auto-link and show main menu."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='460502663875', user_id=42000)
        ctx = make_context()
        worker = make_worker(id=7, max_id=0, inn='460502663875')

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_inn = AsyncMock(return_value=worker)
            mock_db.update_worker_max_id = AsyncMock()
            mock_db.is_foreman = AsyncMock(return_value=False)
            mock_txt.rejoin_worker.return_value = 'Добро пожаловать!'
            mock_kb.user_main_menu.return_value = MagicMock()

            await reg_get_inn(event, ctx)

        # max_id must be updated to the current Max user
        mock_db.update_worker_max_id.assert_awaited_once_with(
            worker_id=7, max_id=42000
        )
        event.message.answer.assert_called_once()
        # context cleared
        assert ctx._state[0] is None

    @pytest.mark.asyncio
    async def test_inn_found_in_db_without_max_id_foreman_gets_foreman_menu(self):
        """INN auto-link for foreman → foreman menu shown."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='460502663875', user_id=42001)
        ctx = make_context()
        worker = make_worker(id=8, max_id=0, inn='460502663875')

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_inn = AsyncMock(return_value=worker)
            mock_db.update_worker_max_id = AsyncMock()
            mock_db.is_foreman = AsyncMock(return_value=True)
            mock_txt.rejoin_worker.return_value = 'Добро пожаловать!'
            mock_kb.foreman_main_menu.return_value = MagicMock()

            await reg_get_inn(event, ctx)

        mock_kb.foreman_main_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_inn_found_in_rr_api(self):
        """INN not in local DB but found in fin API → special error."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        event = make_event(text='460502663875')
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.fin_get_worker_by_inn') as mock_rr, \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.get_worker_by_inn = AsyncMock(return_value=None)
            mock_rr.return_value = {'id': 999}  # found in РР
            mock_txt.reg_error_inn_rr_exists.return_value = 'ИНН в базе РР'

            await reg_get_inn(event, ctx)

        event.message.answer.assert_called_once()
        assert ctx._state[0] is None

    @pytest.mark.asyncio
    async def test_valid_inn_new_user_proceeds_to_card(self):
        """Valid INN, not in any DB → save and ask for card."""
        from max_worker_bot.handlers.registration_handlers import reg_get_inn
        from max_worker_bot.states import RegistrationStates
        event = make_event(text='460502663875')
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.fin_get_worker_by_inn') as mock_rr, \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.get_worker_by_inn = AsyncMock(return_value=None)
            mock_rr.return_value = None
            mock_txt.request_card.return_value = 'Введите карту'

            await reg_get_inn(event, ctx)

        assert ctx._data.get('RegINN') == '460502663875'
        assert ctx._state[0] == RegistrationStates.reg_card


# ===========================================================================
# reg_get_card — handler for RegistrationStates.reg_card
# ===========================================================================

class TestRegGetCard:
    """Tests for reg_get_card — bank card entry."""

    @pytest.mark.asyncio
    async def test_non_digit_card(self):
        """Card with letters → error."""
        from max_worker_bot.handlers.registration_handlers import reg_get_card
        event = make_event(text='abcd-1234-5678-9012')
        ctx = make_context()

        with patch(f'{HANDLERS}.txt') as mock_txt:
            mock_txt.card_number_error.return_value = 'Только цифры'
            await reg_get_card(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_luhn(self):
        """Card fails Luhn check → error."""
        from max_worker_bot.handlers.registration_handlers import reg_get_card
        event = make_event(text='1234567890123456')  # bad Luhn
        ctx = make_context()

        with patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.luhn_check', return_value=False):
            mock_txt.luhn_check_error.return_value = 'Неверный номер карты'
            await reg_get_card(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_card_already_in_local_db(self):
        """Card already exists in local DB → error."""
        from max_worker_bot.handlers.registration_handlers import reg_get_card
        event = make_event(text='4111111111111111')
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.luhn_check', return_value=True), \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.card_unique = AsyncMock(return_value=True)
            mock_txt.card_not_unique_error.return_value = 'Карта занята'
            await reg_get_card(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_card_already_in_rr(self):
        """Card found in fin API → error."""
        from max_worker_bot.handlers.registration_handlers import reg_get_card
        event = make_event(text='4111111111111111')
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.luhn_check', return_value=True), \
             patch(f'{HANDLERS}.fin_get_worker_by_card') as mock_fin, \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.card_unique = AsyncMock(return_value=False)
            mock_fin.return_value = {'id': 1}
            mock_txt.card_not_unique_error.return_value = 'Карта занята'
            await reg_get_card(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_valid_card_proceeds_to_phone(self):
        """Valid, unique card → saved, next state is reg_phone."""
        from max_worker_bot.handlers.registration_handlers import reg_get_card
        from max_worker_bot.states import RegistrationStates
        event = make_event(text='4111111111111111')
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.luhn_check', return_value=True), \
             patch(f'{HANDLERS}.fin_get_worker_by_card') as mock_fin:
            mock_db.card_unique = AsyncMock(return_value=False)
            mock_fin.return_value = None

            await reg_get_card(event, ctx)

        assert ctx._data.get('RegCard') == '4111111111111111'
        assert ctx._state[0] == RegistrationStates.reg_phone


# ===========================================================================
# cmd_start — /start command
# ===========================================================================

class TestCmdStart:
    """Tests for cmd_start."""

    @pytest.mark.asyncio
    async def test_known_worker_sees_main_menu(self):
        """Existing Max user → main menu, no registration prompt."""
        from max_worker_bot.handlers.registration_handlers import cmd_start
        event = make_event(user_id=11111)
        ctx = make_context()
        worker = make_worker(id=5, max_id=11111)

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_max_id = AsyncMock(return_value=worker)
            mock_db.is_foreman = AsyncMock(return_value=False)
            mock_txt.rejoin_worker.return_value = 'С возвращением!'
            mock_kb.user_main_menu.return_value = MagicMock()

            await cmd_start(event, ctx)

        event.message.answer.assert_called_once()
        mock_kb.user_main_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_worker_sees_entry_choice(self):
        """New user → entry choice (Login/Register)."""
        from max_worker_bot.handlers.registration_handlers import cmd_start
        event = make_event(user_id=22222)
        ctx = make_context()

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_max_id = AsyncMock(return_value=None)
            mock_txt.cmd_start_user.return_value = 'Добро пожаловать!'
            mock_kb.entry_choice_max.return_value = MagicMock()

            await cmd_start(event, ctx)

        event.message.answer.assert_called_once()
        mock_kb.entry_choice_max.assert_called_once()

    @pytest.mark.asyncio
    async def test_cmd_start_clears_context(self):
        """/start always clears stale FSM context."""
        from max_worker_bot.handlers.registration_handlers import cmd_start
        event = make_event(user_id=33333)
        ctx = make_context(data={'RegINN': '123456789012'})

        with patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt'), \
             patch(f'{HANDLERS}.kb'):
            mock_db.get_worker_by_max_id = AsyncMock(return_value=None)
            await cmd_start(event, ctx)

        assert ctx._data == {}


# ===========================================================================
# get_phone_number — login flow phone input
# ===========================================================================

class TestGetPhoneNumber:
    """Tests for get_phone_number — login flow."""

    @pytest.mark.asyncio
    async def test_invalid_phone_format(self):
        """Garbage text → phone error."""
        from max_worker_bot.handlers.registration_handlers import get_phone_number
        event = make_event(text='not-a-phone')
        ctx = make_context()

        with patch(f'{HANDLERS}.normalize_phone_number', return_value=None), \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_txt.phone_number_error.return_value = 'Неверный телефон'
            await get_phone_number(event, ctx)

        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_known_tg_user_without_max_id_gets_linked(self):
        """Phone found in DB (Telegram user, max_id=0) → link and show menu."""
        from max_worker_bot.handlers.registration_handlers import get_phone_number
        event = make_event(text='+79001234567', user_id=55555)
        ctx = make_context(data={'city': 'Москва'})
        worker = make_worker(id=10, tg_id=7777777, max_id=0, phone_number='+79001234567')

        with patch(f'{HANDLERS}.normalize_phone_number', return_value='+79001234567'), \
             patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_phone_number = AsyncMock(return_value=worker)
            mock_db.update_worker_max_id = AsyncMock()
            mock_db.update_user_city = AsyncMock()
            mock_db.is_foreman = AsyncMock(return_value=False)
            mock_txt.rejoin_worker.return_value = 'Связано!'
            mock_kb.user_main_menu.return_value = MagicMock()

            await get_phone_number(event, ctx)

        mock_db.update_worker_max_id.assert_awaited_once_with(
            worker_id=10, max_id=55555
        )
        mock_db.update_user_city.assert_awaited_once_with(
            worker_id=10, city='Москва'
        )
        event.message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_known_max_user_gets_verification_code(self):
        """Phone found and already has max_id → send verification code to existing device."""
        from max_worker_bot.handlers.registration_handlers import get_phone_number
        from max_worker_bot.states import RegistrationStates
        event = make_event(text='+79001234567', user_id=66666)
        ctx = make_context()
        worker = make_worker(id=11, max_id=77777, phone_number='+79001234567')

        with patch(f'{HANDLERS}.normalize_phone_number', return_value='+79001234567'), \
             patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.create_code_hash', return_value={'hash': 'h', 'salt': 's'}), \
             patch(f'{HANDLERS}.schedule_delete_verification_code', new_callable=AsyncMock), \
             patch(f'{HANDLERS}.txt') as mock_txt:
            mock_db.get_worker_by_phone_number = AsyncMock(return_value=worker)
            mock_db.set_verification_code_max = AsyncMock(return_value=42)
            mock_txt.request_verification_code.return_value = 'Введите код'
            mock_txt.verification_code = lambda code: f'Код: {code}'

            await get_phone_number(event, ctx)

        mock_db.set_verification_code_max.assert_awaited_once()
        assert ctx._state[0] == RegistrationStates.verification_code

    @pytest.mark.asyncio
    async def test_unknown_phone_not_in_db_not_in_rr(self):
        """Phone not in local DB, not in fin API → prompt to register."""
        from max_worker_bot.handlers.registration_handlers import get_phone_number
        event = make_event(text='+79991112233', user_id=99999)
        ctx = make_context()

        with patch(f'{HANDLERS}.normalize_phone_number', return_value='+79991112233'), \
             patch(f'{HANDLERS}.db') as mock_db, \
             patch(f'{HANDLERS}.fin_get_worker_by_phone') as mock_fin, \
             patch(f'{HANDLERS}.txt') as mock_txt, \
             patch(f'{HANDLERS}.kb') as mock_kb:
            mock_db.get_worker_by_phone_number = AsyncMock(return_value=None)
            mock_fin.return_value = None
            mock_txt.reg_error_phone_exists = MagicMock()
            mock_kb.entry_choice_max.return_value = MagicMock()

            await get_phone_number(event, ctx)

        # Not found in DB or API → answer something (not found prompt or register suggestion)
        event.message.answer.assert_called()
