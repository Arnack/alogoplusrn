from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging

from filters import Admin, Director
from aiogram.filters import or_f
import database as db


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'SelfEmployedAnnul')
async def open_annul_menu(callback: CallbackQuery, state: FSMContext):
    """Открыть меню аннулирования"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        text="Введите фамилию самозанятого для поиска:",
        parse_mode='HTML'
    )
    await state.set_state('AnnulRequestLastName')


@router.message(or_f(Admin(), Director()), F.text, StateFilter('AnnulRequestLastName'))
async def get_last_name_for_annul(message: Message, state: FSMContext):
    """Получить фамилию и показать список исполнителей"""
    await state.set_state(None)

    workers = await db.get_workers_by_last_name_with_active_cycle(last_name=message.text)

    if not workers:
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="SelfEmployedMenu")]
            ]
        )
        await message.answer(
            text="❌ Исполнители с активными циклами не найдены.",
            reply_markup=back_keyboard
        )
        return

    # Создать клавиатуру со списком исполнителей
    keyboard = InlineKeyboardBuilder()
    for worker in workers:
        full_name = f"{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}"
        keyboard.add(InlineKeyboardButton(
            text=f"👤 {full_name}",
            callback_data=f"AnnulSelectWorker:{worker.id}"
        ))
    keyboard.add(InlineKeyboardButton(text="◀️ Назад", callback_data="SelfEmployedMenu"))
    keyboard.adjust(1)

    await message.answer(
        text=f"Найдено исполнителей с активными циклами: {len(workers)}",
        reply_markup=keyboard.as_markup()
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AnnulSelectWorker:'))
async def select_worker_for_annul(callback: CallbackQuery, state: FSMContext):
    """Выбрать исполнителя и показать информацию о цикле"""
    await callback.answer()

    worker_id = int(callback.data.split(':')[1])
    worker = await db.get_user_by_id(user_id=worker_id)
    worker_data = await db.get_user_real_data_by_id(user_id=worker_id)
    full_name = f"{worker_data.last_name} {worker_data.first_name} {worker_data.middle_name}"

    # Получить активный цикл и события
    active_cycle = await db.get_active_cycle_for_worker(worker_id=worker_id)

    if not active_cycle:
        await callback.message.edit_text(
            text="❌ Активный цикл не найден.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="SelfEmployedMenu")]]
            )
        )
        return

    # Получить события невыхода
    events = await db.get_no_show_events_for_worker_active_cycle(worker_id=worker_id)
    dates_str = '\n'.join([f"• {event.no_show_date} — {event.assigned_amount:,} ₽" for event in events])
    max_amount = max([e.assigned_amount for e in events], default=0)

    confirm_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, аннулировать", callback_data=f"AnnulConfirm:{active_cycle.id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="SelfEmployedMenu")
            ]
        ]
    )

    await callback.message.edit_text(
        text=(
            f"<b>Аннулирование договорной комиссии</b>\n\n"
            f"Самозанятый: <b>{full_name}</b>\n"
            f"ИНН: <code>{worker.inn}</code>\n\n"
            f"<b>Даты невыходов:</b>\n{dates_str}\n\n"
            f"Максимальная назначенная сумма: <b>{max_amount:,} ₽</b>\n\n"
            f"❓ Подтвердите аннулирование."
        ),
        reply_markup=confirm_keyboard,
        parse_mode='HTML'
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AnnulConfirm:'))
async def confirm_annul(callback: CallbackQuery, state: FSMContext):
    """Подтвердить аннулирование"""
    await callback.answer()

    cycle_id = int(callback.data.split(':')[1])

    try:
        await db.annul_cycle(cycle_id=cycle_id, admin_tg_id=callback.from_user.id)

        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В меню", callback_data="SelfEmployedMenu")]
            ]
        )

        await callback.message.edit_text(
            text="✅ <b>Договорная комиссия успешно аннулирована</b>",
            reply_markup=back_keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f'Ошибка аннулирования цикла {cycle_id}: {e}')
        await callback.message.edit_text(
            text="❌ Ошибка при аннулировании. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="SelfEmployedMenu")]]
            )
        )

    await state.clear()
