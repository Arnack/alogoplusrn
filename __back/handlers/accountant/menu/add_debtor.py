from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime, timedelta
import logging

from filters import Accountant
from utils import parse_date_from_str_to_str
from utils.scheduler import schedule_expire_no_show_buttons
import database as db


router = Router()


@router.message(Accountant(), F.text == '➕ Добавить должника')
async def request_worker_lastname(message: Message, state: FSMContext):
    """Запросить фамилию работника для поиска"""
    await state.clear()
    await message.answer(
        text="🔍 <b>Поиск работника</b>\n\n"
             "Введите фамилию исполнителя:",
        parse_mode='HTML'
    )
    await state.set_state('ManualDebtorSearchLastName')


@router.message(Accountant(), F.text, StateFilter('ManualDebtorSearchLastName'))
async def search_worker_by_lastname(message: Message, state: FSMContext):
    """Найти работников по фамилии"""
    lastname = message.text.strip()

    # Поиск работников по фамилии
    workers = await db.search_workers_by_lastname(lastname=lastname)

    if not workers:
        await message.answer(
            text=f"❌ Работники с фамилией <b>{lastname}</b> не найдены.\n\n"
                 "Попробуйте еще раз:",
            parse_mode='HTML'
        )
        return

    if len(workers) > 20:
        await message.answer(
            text=f"📊 Найдено работников: <b>{len(workers)}</b>\n\n"
                 "Слишком много результатов. Уточните фамилию:",
            parse_mode='HTML'
        )
        return

    # Создать инлайн клавиатуру с найденными работниками
    keyboard = []
    for worker in workers:
        security_data = worker.security
        full_name = f"{security_data.last_name} {security_data.first_name}"
        if security_data.middle_name:
            full_name += f" {security_data.middle_name}"

        keyboard.append([
            InlineKeyboardButton(
                text=full_name,
                callback_data=f"ManualDebtorSelectWorker:{worker.id}"
            )
        ])

    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="ManualDebtorCancel")])

    await message.answer(
        text=f"🔍 Найдено работников: <b>{len(workers)}</b>\n\n"
             "Выберите исполнителя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


@router.callback_query(Accountant(), F.data.startswith('ManualDebtorSelectWorker:'))
async def select_worker_and_request_date(callback: CallbackQuery, state: FSMContext):
    """Работник выбран, запросить дату невыхода"""
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])

    security_data = await db.get_user_real_data_by_id(user_id=worker_id)
    if not security_data:
        await callback.message.edit_text(text="❌ Работник не найден.")
        await state.clear()
        return

    full_name = f"{security_data.last_name} {security_data.first_name}"
    if security_data.middle_name:
        full_name += f" {security_data.middle_name}"

    await state.update_data(ManualDebtorWorkerId=worker_id, ManualDebtorWorkerName=full_name)

    await callback.message.edit_text(
        text=f"✅ Выбран: <b>{full_name}</b>\n\n"
             "📅 Введите дату невыхода:\n\n"
             "💡 Примеры: <code>21.2</code>, <code>21.02</code>, <code>21.02.26</code>",
        parse_mode='HTML'
    )
    await state.set_state('ManualDebtorEnterDate')


@router.message(Accountant(), F.text, StateFilter('ManualDebtorEnterDate'))
async def receive_date_and_request_amount(message: Message, state: FSMContext):
    """Получить дату и запросить подтверждение суммы"""
    # Парсинг даты
    date_str = parse_date_from_str_to_str(message.text)
    if not date_str:
        await message.answer(
            text="❌ Неверный формат даты.\n\n"
                 "💡 Примеры: <code>21.2</code>, <code>21.02</code>, <code>21.02.26</code>",
            parse_mode='HTML'
        )
        return

    data = await state.get_data()
    worker_name = data['ManualDebtorWorkerName']

    await state.update_data(ManualDebtorDate=date_str)

    # Клавиатура с подтверждением суммы
    keyboard = [
        [InlineKeyboardButton(text="✅ Подтвердить 3 000 ₽", callback_data="ManualDebtorConfirmAmount:3000")],
        [InlineKeyboardButton(text="✏️ Изменить сумму", callback_data="ManualDebtorChangeAmount")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ManualDebtorCancel")]
    ]

    await message.answer(
        text=f"📋 <b>Подтверждение данных</b>\n\n"
             f"Самозанятый: <b>{worker_name}</b>\n"
             f"Дата невыхода: <b>{date_str}</b>\n"
             f"Договорная комиссия: <b>3 000 ₽</b>\n\n"
             f"Подтвердите или измените сумму:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


@router.callback_query(Accountant(), F.data.startswith('ManualDebtorConfirmAmount:'))
async def confirm_and_create_event(callback: CallbackQuery, state: FSMContext):
    """Подтвердить сумму и создать событие"""
    await callback.answer()
    amount = int(callback.data.split(':')[1])

    data = await state.get_data()
    worker_id = data['ManualDebtorWorkerId']
    worker_name = data['ManualDebtorWorkerName']
    date_str = data['ManualDebtorDate']

    try:
        # Получить или создать цикл должника
        cycle = await db.get_or_create_debtor_cycle(worker_id=worker_id)

        # Создать событие невыхода
        event = await db.create_no_show_event(
            cycle_id=cycle.id,
            order_archive_id=None,  # Ручное добавление, без привязки к архиву
            no_show_date=date_str,
            assigned_amount=amount
        )

        # Получить всех кассиров
        accountants = await db.get_all_accountants()

        # Текст карточки
        card_text = (
            f"⚠️ <b>{worker_name}</b>\n"
            f"взял заказ и не оказал услуги.\n\n"
            f"💼 В соответствии с п. 8.10 Договора, Исполнитель обязан возместить организационные расходы в размере {amount:,} ₽.\n\n"
            f"📅 Дата заказа: <b>{date_str}</b>\n"
            f"🆔 ID события: <code>{event.id}</code>\n"
            f"✍️ Добавлено вручную\n\n"
            f"Подтвердите сумму или измените её при необходимости."
        )

        # Клавиатура для кассиров
        keyboard = [
            [InlineKeyboardButton(text=f"✅ Подтвердить {amount:,} ₽", callback_data=f"NoShowConfirm:{event.id}")],
            [InlineKeyboardButton(text="✏️ Изменить сумму", callback_data=f"NoShowChangeAmount:{event.id}")]
        ]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Разослать карточки всем кассирам
        sent_count = 0
        for accountant in accountants:
            try:
                msg = await callback.bot.send_message(
                    chat_id=accountant.tg_id,
                    text=card_text,
                    reply_markup=markup,
                    parse_mode='HTML'
                )

                # Сохранить message_id
                await db.add_cashier_message(
                    event_id=event.id,
                    cashier_tg_id=accountant.tg_id,
                    message_id=msg.message_id
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Ошибка отправки карточки кассиру {accountant.tg_id}: {e}")

        # Запланировать истечение кнопок через 24 часа
        await schedule_expire_no_show_buttons(event_id=event.id)

        await callback.message.edit_text(
            text=f"✅ <b>Должник добавлен</b>\n\n"
                 f"Самозанятый: <b>{worker_name}</b>\n"
                 f"Дата: <b>{date_str}</b>\n"
                 f"Сумма: <b>{amount:,} ₽</b>\n\n"
                 f"Карточки разосланы кассирам: {sent_count}",
            parse_mode='HTML'
        )

        await state.clear()

    except Exception as e:
        logging.exception(f"Ошибка при создании события невыхода: {e}")
        await callback.message.edit_text(
            text="❌ Произошла ошибка при добавлении должника. Попробуйте позже."
        )
        await state.clear()


@router.callback_query(Accountant(), F.data == 'ManualDebtorChangeAmount')
async def request_custom_amount(callback: CallbackQuery, state: FSMContext):
    """Запросить ввод пользовательской суммы"""
    await callback.answer()
    await callback.message.edit_text(
        text="✏️ Введите сумму договорной комиссии:\n\n"
             "💡 Допустимый диапазон: от 1 до 3 000 ₽"
    )
    await state.set_state('ManualDebtorEnterCustomAmount')


@router.message(Accountant(), F.text, StateFilter('ManualDebtorEnterCustomAmount'))
async def receive_custom_amount(message: Message, state: FSMContext):
    """Получить пользовательскую сумму"""
    try:
        amount = int(message.text.strip())
        assert 1 <= amount <= 3000
    except (ValueError, AssertionError):
        await message.answer(
            text="❌ Неверная сумма. Введите целое число от 1 до 3 000 ₽."
        )
        return

    data = await state.get_data()
    worker_name = data['ManualDebtorWorkerName']
    date_str = data['ManualDebtorDate']

    # Клавиатура с подтверждением новой суммы
    keyboard = [
        [InlineKeyboardButton(text=f"✅ Подтвердить {amount:,} ₽", callback_data=f"ManualDebtorConfirmAmount:{amount}")],
        [InlineKeyboardButton(text="✏️ Изменить сумму", callback_data="ManualDebtorChangeAmount")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="ManualDebtorCancel")]
    ]

    await message.answer(
        text=f"📋 <b>Подтверждение данных</b>\n\n"
             f"Самозанятый: <b>{worker_name}</b>\n"
             f"Дата невыхода: <b>{date_str}</b>\n"
             f"Договорная комиссия: <b>{amount:,} ₽</b>\n\n"
             f"Подтвердите данные:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='HTML'
    )


@router.callback_query(Accountant(), F.data == 'ManualDebtorCancel')
async def cancel_add_debtor(callback: CallbackQuery, state: FSMContext):
    """Отменить добавление должника"""
    await callback.answer()
    await callback.message.edit_text(text="❌ Добавление должника отменено.")
    await state.clear()
