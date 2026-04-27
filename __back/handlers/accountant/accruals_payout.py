"""Флоу вывода из начислений с договорами и актами (п.12 ТЗ).

Сценарий:
1. Пользователь нажимает «Вывод»
2. Формируются 3 договора
3. Запрос уходит кассиру
4. Кассир выбирает ИП
5. Пользователю приходит акт
6. Пользователь формирует чек
7. Данные отправляются в РР
"""
import logging
from datetime import datetime
from decimal import Decimal
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from filters import Accountant
from utils.organizations import orgs_dict
from handlers.user.sign_act import send_act_to_worker, send_act_to_worker_max
from utils.payout_flow import create_contract_documents, ensure_act_pdf, get_worker_pin_context
import database as db
import texts as txt

router = Router()


class AccrualsPayoutStates(StatesGroup):
    """Состояния флоу вывода из начислений."""
    waiting_worker_selection = State()  # Выбор работника
    waiting_org_selection = State()  # Выбор ИП кассиром
    waiting_amount_confirmation = State()  # Подтверждение суммы


@router.callback_query(Accountant(), F.data.startswith('AccrualsPayoutSelect:'))
async def select_worker_for_payout(callback: CallbackQuery, state: FSMContext):
    """Кассир выбрал работника для выплаты из начислений."""
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])

    worker = await db.get_user_by_id(user_id=worker_id)
    sec = await db.get_user_real_data_by_id(user_id=worker_id)

    if not worker or not sec:
        await callback.message.edit_text('❌ Работник не найден.')
        await state.clear()
        return

    # Формируем 3 договора для работника (п.6 ТЗ)
    act_date = datetime.strftime(datetime.now(), "%d.%m.%Y")
    contracts = await create_contract_documents(user_id=worker_id, act_date=act_date)

    if not contracts:
        await callback.message.edit_text('❌ Не удалось создать договоры.')
        await state.clear()
        return

    fio = f"{sec.last_name} {sec.first_name}"
    if sec.middle_name:
        fio += f" {sec.middle_name}"

    try:
        balance = Decimal(worker.balance.replace(',', '.')) if worker.balance else Decimal('0')
    except Exception:
        balance = Decimal('0')

    await state.update_data(
        AccrualsPayoutWorkerId=worker_id,
        AccrualsPayoutWorkerName=fio,
        AccrualsPayoutWorkerTgId=worker.tg_id,
        AccrualsPayoutWorkerMaxId=worker.max_id,
        AccrualsPayoutBalance=str(balance),
        AccrualsPayoutContracts=[c.id for c in contracts],
    )

    # Показываем кассиру список ИП для выбора
    keyboard = []
    for org_id, org_name in orgs_dict.items():
        keyboard.append([InlineKeyboardButton(
            text=f'🏢 {org_name}',
            callback_data=f'AccrualsPayoutOrg:{org_id}',
        )])
    keyboard.append([InlineKeyboardButton(text='❌ Отмена', callback_data='AccrualsPayoutCancel')])

    await callback.message.edit_text(
        text=(
            f'✅ <b>{fio}</b>\n'
            f'Баланс: <b>{balance:,.2f} ₽</b>\n'
            f'Договоров создано: <b>{len(contracts)}</b>\n\n'
            f'Выберите ИП для выплаты:'
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML',
    )
    await state.set_state('AccrualsPayoutStates.waiting_org_selection')


@router.callback_query(Accountant(), F.data.startswith('AccrualsPayoutOrg:'))
async def select_org_for_payout(callback: CallbackQuery, state: FSMContext):
    """Кассир выбрал ИП для выплаты."""
    await callback.answer()
    org_id = int(callback.data.split(':')[1])
    data = await state.get_data()

    worker_id = data['AccrualsPayoutWorkerId']
    fio = data['AccrualsPayoutWorkerName']

    # Архивируем 2 договора из 3, оставляем только с выбранным ИП (п.7 ТЗ)
    archived = await db.archive_contracts_except_legal_entity(
        user_id=worker_id,
        legal_entity_id=org_id,
    )

    # Получаем активный договор
    active_contract = await db.get_active_contract(
        user_id=worker_id,
        legal_entity_id=org_id,
    )

    await state.update_data(
        AccrualsPayoutOrgId=org_id,
        AccrualsPayoutActiveContractId=active_contract.id if active_contract else None,
    )

    await callback.message.edit_text(
        text=(
            f'✅ Выбрано ИП: <b>{orgs_dict[org_id]}</b>\n'
            f'Договор: <b>{active_contract.number if active_contract else "N/A"}</b>\n\n'
            f'Введите сумму для выплаты:'
        ),
        parse_mode='HTML',
    )
    await state.set_state('AccrualsPayoutStates.waiting_amount_confirmation')


@router.message(Accountant(), F.text, StateFilter('AccrualsPayoutStates.waiting_amount_confirmation'))
async def receive_payout_amount(message: Message, state: FSMContext):
    """Кассир ввел сумму выплаты."""
    from utils import is_number, truncate_decimal

    raw = message.text.strip().replace(',', '.')
    amount = truncate_decimal(raw)

    if not is_number(amount):
        await message.answer('❌ Неверный формат. Введите число (например: 1500):')
        return

    data = await state.get_data()
    worker_id = data['AccrualsPayoutWorkerId']
    fio = data['AccrualsPayoutWorkerName']
    worker_tg_id = data.get('AccrualsPayoutWorkerTgId')
    worker_max_id = data.get('AccrualsPayoutWorkerMaxId')
    org_id = data['AccrualsPayoutOrgId']

    worker, security, birthday = await get_worker_pin_context(worker_id)

    # Фиксируем карту на момент выплаты (п.10 ТЗ)
    card_snapshot = worker.card.replace(' ', '')[:16] if worker.card else None

    # Создаём акт
    act_date = datetime.strftime(datetime.now(), "%d.%m.%Y")
    act = await db.create_worker_act(
        worker_id=worker_id,
        legal_entity_id=org_id,
        amount=amount,
        date=act_date,
        card_snapshot=card_snapshot,
    )
    await ensure_act_pdf(act.id)

    # Отправляем акт работнику
    if worker_tg_id:
        await send_act_to_worker(
            bot=message.bot,
            worker_tg_id=worker_tg_id,
            act_id=act.id,
            amount=amount,
            date=act_date,
            inn=worker.inn or '',
            passport_number=(security.passport_number if security else '') or '',
            birthday=birthday,
            card_snapshot=card_snapshot,
            worker_max_id=worker_max_id,
        )

    # Дублируем в Max если привязан
    if worker_max_id:
        await send_act_to_worker_max(
            worker_max_id=worker_max_id,
            act_id=act.id,
            amount=amount,
            date=act_date,
            inn=worker.inn or '',
            passport_number=(security.passport_number if security else '') or '',
            birthday=birthday,
            card_snapshot=card_snapshot,
            worker_tg_id=worker_tg_id,
        )

    await message.answer(
        text=(
            f'✅ Акт на сумму <b>{amount:,.2f} ₽</b> отправлен работнику.\n'
            f'После подписания акта и получения чека выплата будет отправлена в РР.'
        ),
        parse_mode='HTML',
    )

    await state.clear()


@router.callback_query(Accountant(), F.data == 'AccrualsPayoutCancel')
async def cancel_accruals_payout(callback: CallbackQuery, state: FSMContext):
    """Отмена выплаты из начислений."""
    await callback.answer()
    await callback.message.edit_text('❌ Выплата из начислений отменена.')
    await state.clear()
