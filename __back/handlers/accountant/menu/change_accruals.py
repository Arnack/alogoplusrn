from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal, InvalidOperation
import logging

from filters import Accountant
import database as db


router = Router()


@router.message(Accountant(), F.text == '✏️ Изменение начислений')
async def request_lastname_for_accruals(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='🔍 <b>Изменение начислений</b>\n\nВведите фамилию исполнителя:',
        parse_mode='HTML',
    )
    await state.set_state('ChangeAccrualsSearchLastName')


@router.message(Accountant(), F.text, StateFilter('ChangeAccrualsSearchLastName'))
async def search_worker_for_accruals(message: Message, state: FSMContext):
    lastname = message.text.strip()
    workers = await db.search_workers_by_lastname(lastname=lastname)

    if not workers:
        await message.answer(
            text=f'❌ Работники с фамилией <b>{lastname}</b> не найдены.\n\nПопробуйте ещё раз:',
            parse_mode='HTML',
        )
        return

    if len(workers) > 20:
        await message.answer(
            text=f'📊 Найдено: <b>{len(workers)}</b>. Слишком много — уточните фамилию:',
            parse_mode='HTML',
        )
        return

    keyboard = []
    for w in workers:
        sec = w.security
        fio = f"{sec.last_name} {sec.first_name}"
        if sec.middle_name:
            fio += f" {sec.middle_name}"
        try:
            balance = Decimal(w.balance.replace(',', '.')) if w.balance else Decimal('0')
        except Exception:
            balance = Decimal('0')
        keyboard.append([InlineKeyboardButton(
            text=f"{fio} — {balance:,.2f} ₽",
            callback_data=f"ChangeAccrualsSelect:{w.id}",
        )])
    keyboard.append([InlineKeyboardButton(text='❌ Отмена', callback_data='ChangeAccrualsCancel')])

    await message.answer(
        text=f'🔍 Найдено: <b>{len(workers)}</b>. Выберите исполнителя:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML',
    )


@router.callback_query(Accountant(), F.data.startswith('ChangeAccrualsSelect:'))
async def select_worker_for_accruals(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])

    sec = await db.get_user_real_data_by_id(user_id=worker_id)
    user = await db.get_user_by_id(user_id=worker_id)
    if not sec or not user:
        await callback.message.edit_text('❌ Работник не найден.')
        await state.clear()
        return

    fio = f"{sec.last_name} {sec.first_name}"
    if sec.middle_name:
        fio += f" {sec.middle_name}"

    try:
        balance = Decimal(user.balance.replace(',', '.')) if user.balance else Decimal('0')
    except Exception:
        balance = Decimal('0')

    await state.update_data(
        ChangeAccrualsWorkerId=worker_id,
        ChangeAccrualsWorkerName=fio,
        ChangeAccrualsWorkerTgId=user.tg_id,
    )

    await callback.message.edit_text(
        text=(
            f'✅ <b>{fio}</b>\n'
            f'Текущий баланс: <b>{balance:,.2f} ₽</b>\n\n'
            f'Введите новый баланс (число, например: 1500 или -500):'
        ),
        parse_mode='HTML',
    )
    await state.set_state('ChangeAccrualsEnterAmount')


@router.message(Accountant(), F.text, StateFilter('ChangeAccrualsEnterAmount'))
async def receive_new_accrual_amount(message: Message, state: FSMContext):
    raw = message.text.strip().replace(',', '.')
    try:
        new_balance = Decimal(raw)
    except InvalidOperation:
        await message.answer('❌ Неверный формат. Введите число (например: 1500 или -500):')
        return

    data = await state.get_data()
    worker_name = data['ChangeAccrualsWorkerName']

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f'✅ Подтвердить: {new_balance:,.2f} ₽',
            callback_data='ChangeAccrualsConfirm',
        )],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='ChangeAccrualsCancel')],
    ])

    await message.answer(
        text=(
            f'📋 <b>Подтверждение изменения</b>\n\n'
            f'Исполнитель: <b>{worker_name}</b>\n'
            f'Новый баланс: <b>{new_balance:,.2f} ₽</b>\n\n'
            f'Подтвердите изменение:'
        ),
        reply_markup=keyboard,
        parse_mode='HTML',
    )
    await state.update_data(ChangeAccrualsNewBalance=str(new_balance))


@router.callback_query(Accountant(), F.data == 'ChangeAccrualsConfirm')
async def confirm_accrual_change(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    fio = data.get('ChangeAccrualsWorkerName', '?')
    worker_id = data.get('ChangeAccrualsWorkerId')
    new_balance_str = data.get('ChangeAccrualsNewBalance', '0')

    if not worker_id:
        await callback.message.edit_text('❌ Данные работника не найдены.')
        await state.clear()
        return

    success = await db.update_worker_balance(worker_id=worker_id, new_balance=new_balance_str)

    if success:
        logging.info(f'[Баланс] Кассир {callback.from_user.id} изменил баланс {fio} → {new_balance_str}')
        await callback.message.edit_text(
            text=f'✅ Баланс <b>{fio}</b> обновлён: <b>{Decimal(new_balance_str):,.2f} ₽</b>',
            parse_mode='HTML',
        )
    else:
        await callback.message.edit_text('❌ Ошибка при обновлении баланса.')

    await state.clear()


@router.callback_query(Accountant(), F.data == 'ChangeAccrualsCancel')
async def cancel_accruals_change(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text('❌ Изменение начислений отменено.')
    await state.clear()
