from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
import logging

from filters import Accountant
import database as db


router = Router()


@router.callback_query(Accountant(), F.data.startswith('NoShowConfirm:'))
async def confirm_no_show_amount(callback: CallbackQuery):
    """Кассир подтверждает стандартную сумму 3000 ₽"""
    await callback.answer()
    event_id = int(callback.data.split(':')[1])
    event = await db.get_no_show_event(event_id=event_id)

    if not event:
        await callback.answer("Событие не найдено.", show_alert=True)
        return

    if event.cashier_reviewed:
        await callback.answer("Уже проверено.", show_alert=True)
        return

    if event.buttons_expire_at < datetime.now():
        await callback.answer("Время действия кнопок истекло.", show_alert=True)
        return

    # Отметить как проверенное
    await db.mark_event_reviewed(
        event_id=event_id,
        cashier_tg_id=callback.from_user.id,
        new_amount=event.assigned_amount
    )

    # Получить данные для обновленного текста
    worker_data = await db.get_user_real_data_by_id(user_id=event.cycle.worker_id)
    full_name = f"{worker_data.last_name} {worker_data.first_name} {worker_data.middle_name}"
    accountant = await db.get_accountant_by_tg_id(tg_id=callback.from_user.id)

    reviewed_text = (
        f"✅ <b>Договорная комиссия подтверждена</b>\n\n"
        f"Самозанятый: <b>{full_name}</b>\n"
        f"Дата заявки: <b>{event.no_show_date}</b>\n"
        f"Подтверждённая сумма: <b>{event.assigned_amount:,} ₽</b>\n\n"
        f"Проверено кассиром: {accountant.full_name if accountant else str(callback.from_user.id)}"
    )

    # Обновить ВСЕ сообщения с этой карточкой (убрать кнопки)
    cashier_messages = await db.get_cashier_messages_for_event(event_id=event_id)
    for msg in cashier_messages:
        try:
            await callback.bot.edit_message_text(
                chat_id=msg.cashier_tg_id,
                message_id=msg.message_id,
                text=reviewed_text,
                reply_markup=None,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f'Ошибка редактирования сообщения кассиру {msg.cashier_tg_id}: {e}')


@router.callback_query(Accountant(), F.data.startswith('NoShowChangeAmount:'))
async def request_new_amount(callback: CallbackQuery, state: FSMContext):
    """Кассир хочет изменить сумму"""
    await callback.answer()
    event_id = int(callback.data.split(':')[1])
    event = await db.get_no_show_event(event_id=event_id)

    if not event:
        await callback.answer("Событие не найдено.", show_alert=True)
        return

    if event.cashier_reviewed:
        await callback.answer("Уже проверено или недоступно.", show_alert=True)
        return

    if event.buttons_expire_at < datetime.now():
        await callback.answer("Время действия кнопок истекло.", show_alert=True)
        return

    await state.update_data(NoShowEventId=event_id)
    await state.set_state('NoShowNewAmount')
    await callback.message.answer(
        text="Введите новую сумму договорной комиссии (от 1 до 3000 ₽):"
    )


@router.message(Accountant(), F.text, StateFilter('NoShowNewAmount'))
async def receive_new_amount(message: Message, state: FSMContext):
    """Получить и сохранить новую сумму"""
    try:
        new_amount = int(message.text.strip())
        assert 1 <= new_amount <= 3000
    except (ValueError, AssertionError):
        await message.answer(text="❌ Неверная сумма. Введите целое число от 1 до 3000.")
        return

    data = await state.get_data()
    event_id = data['NoShowEventId']
    event = await db.get_no_show_event(event_id=event_id)

    if not event:
        await message.answer(text="❌ Событие не найдено.")
        await state.clear()
        return

    # Отметить как проверенное с новой суммой
    await db.mark_event_reviewed(
        event_id=event_id,
        cashier_tg_id=message.from_user.id,
        new_amount=new_amount
    )

    # Получить данные для обновленного текста
    worker_data = await db.get_user_real_data_by_id(user_id=event.cycle.worker_id)
    full_name = f"{worker_data.last_name} {worker_data.first_name} {worker_data.middle_name}"
    accountant = await db.get_accountant_by_tg_id(tg_id=message.from_user.id)

    reviewed_text = (
        f"✅ <b>Договорная комиссия изменена</b>\n\n"
        f"Самозанятый: <b>{full_name}</b>\n"
        f"Дата заявки: <b>{event.no_show_date}</b>\n"
        f"Новая сумма: <b>{new_amount:,} ₽</b>\n\n"
        f"Изменено кассиром: {accountant.full_name if accountant else str(message.from_user.id)}"
    )

    # Обновить ВСЕ сообщения с этой карточкой (убрать кнопки)
    cashier_messages = await db.get_cashier_messages_for_event(event_id=event_id)
    for msg in cashier_messages:
        try:
            await message.bot.edit_message_text(
                chat_id=msg.cashier_tg_id,
                message_id=msg.message_id,
                text=reviewed_text,
                reply_markup=None,
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f'Ошибка редактирования карточки неявки: {e}')

    await message.answer(text="✅ Сумма договорной комиссии обновлена.")
    await state.clear()
