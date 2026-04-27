from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from filters import Manager, AdminOrManager
from keyboards.inline.admin.workers.add_worker_keyboards import (
    skip_middle_name_keyboard,
    skip_inn_keyboard,
    skip_phone_keyboard,
    skip_card_keyboard,
    skip_telegram_id_keyboard,
    skip_birthday_keyboard,
    skip_passport_keyboard,
    confirm_save_worker_keyboard,
    back_to_workers_menu_keyboard
)
from texts import add_worker as txt
from utils.worker_validators import validate_inn, normalize_phone_number, validate_card_number, validate_telegram_id
from database.requests.admin.workers.add_worker_manually import add_worker_manually
from API.fin.workers import fin_get_worker_by_inn, fin_get_worker_by_card, fin_get_worker_by_phone
import logging
import re

# ==================== ВРЕМЕННЫЙ ФЛАГ ====================
# Установите False чтобы вернуть отправку в РР API при добавлении СМЗ
BYPASS_RR_API = False
# =========================================================

router = Router()


def _is_valid_date(value: str) -> bool:
    """Проверяет формат ДД.ММ.ГГГГ"""
    return bool(re.match(r'^\d{2}\.\d{2}\.\d{4}$', value.strip()))


# Шаг 1: Начало добавления самозанятого - запрос фамилии
@router.callback_query(AdminOrManager(), F.data == 'AddWorker')
async def start_add_worker(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await state.set_state('AddWorkerLastName')

    await callback.message.edit_text(
        text=txt.request_last_name(),
        reply_markup=back_to_workers_menu_keyboard()
    )


# Обработчик reply-кнопки для менеджеров
@router.message(Manager(), F.text == '🚶 СМЗ')
async def start_add_worker_manager(
        message: Message,
        state: FSMContext
):
    await state.clear()
    await state.set_state('AddWorkerLastName')

    await message.answer(
        text=txt.request_last_name(),
        reply_markup=back_to_workers_menu_keyboard()
    )


# Шаг 2: Получение фамилии и запрос имени
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerLastName'))
async def get_last_name(
        message: Message,
        state: FSMContext
):
    last_name = message.text.strip()

    if not last_name:
        await message.answer(
            text='❗Фамилия не может быть пустой. Попробуйте еще раз:',
            reply_markup=back_to_workers_menu_keyboard()
        )
        return

    await state.update_data(last_name=last_name)
    await state.set_state('AddWorkerFirstName')

    await message.answer(
        text=txt.request_first_name(),
        reply_markup=back_to_workers_menu_keyboard()
    )


# Шаг 3: Получение имени и запрос отчества
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerFirstName'))
async def get_first_name(
        message: Message,
        state: FSMContext
):
    first_name = message.text.strip()

    if not first_name:
        await message.answer(
            text='❗Имя не может быть пустым. Попробуйте еще раз:',
            reply_markup=back_to_workers_menu_keyboard()
        )
        return

    await state.update_data(first_name=first_name)
    await state.set_state('AddWorkerMiddleName')

    await message.answer(
        text=txt.request_middle_name(),
        reply_markup=skip_middle_name_keyboard()
    )


# Шаг 4: Получение отчества или пропуск
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerMiddleName'))
async def get_middle_name(
        message: Message,
        state: FSMContext
):
    middle_name = message.text.strip()
    await state.update_data(middle_name=middle_name)
    await state.set_state('AddWorkerInn')

    await message.answer(
        text=txt.request_inn(),
        reply_markup=skip_inn_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipMiddleName')
async def skip_middle_name(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(middle_name='')
    await state.set_state('AddWorkerInn')

    await callback.message.edit_text(
        text=txt.request_inn(),
        reply_markup=skip_inn_keyboard()
    )


# Шаг 5: Получение ИНН или пропуск (с проверкой в РР и локальной БД)
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerInn'))
async def get_inn(
        message: Message,
        state: FSMContext
):
    inn = message.text.strip()

    if inn and not validate_inn(inn):
        await message.answer(
            text=txt.inn_validation_error(),
            reply_markup=skip_inn_keyboard()
        )
        return

    digits = ''.join(filter(str.isdigit, inn)) if inn else ''

    if digits and not BYPASS_RR_API:
        # Проверяем в глобальной базе РР
        rr_worker = await fin_get_worker_by_inn(digits)
        if rr_worker:
            await message.answer(
                text=txt.inn_already_registered_rr(),
                reply_markup=skip_inn_keyboard()
            )
            return

    await state.update_data(inn=digits)
    await state.set_state('AddWorkerPhone')

    await message.answer(
        text=txt.request_phone_number(),
        reply_markup=skip_phone_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipInn')
async def skip_inn(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(inn='')
    await state.set_state('AddWorkerPhone')

    await callback.message.edit_text(
        text=txt.request_phone_number(),
        reply_markup=skip_phone_keyboard()
    )


# Шаг 6: Получение номера телефона или пропуск (с проверкой на дубликат в РР)
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerPhone'))
async def get_phone_number(
        message: Message,
        state: FSMContext
):
    phone = message.text.strip()
    normalized_phone = normalize_phone_number(phone) if phone else ''

    if normalized_phone and not BYPASS_RR_API:
        # Нормализуем до 10 цифр для поиска в РР
        phone_10 = normalized_phone.lstrip('+')
        if phone_10.startswith('7') and len(phone_10) == 11:
            phone_10 = phone_10[1:]
        rr_worker = await fin_get_worker_by_phone(phone_10)
        if rr_worker:
            await message.answer(
                text=txt.phone_already_registered(),
                reply_markup=skip_phone_keyboard()
            )
            return

    if normalized_phone and len(normalized_phone) == 12 and normalized_phone[2] == '7':
        await message.answer(
            text=f'⚠️ <b>Внимание!</b>\n\n'
                 f'Вы ввели номер: <code>+{normalized_phone}</code>\n\n'
                 f'Российские номера после префикса +7 обычно начинаются с 9, 3, 4, 5 или 8, но не с 7.\n'
                 f'Убедитесь, что номер введён правильно.\n\n'
                 f'Данные будут сохранены как есть.',
            parse_mode='HTML'
        )

    await state.update_data(phone_number=normalized_phone)
    await state.set_state('AddWorkerCard')

    await message.answer(
        text=txt.request_card_number(),
        reply_markup=skip_card_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipPhone')
async def skip_phone(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(phone_number='')
    await state.set_state('AddWorkerCard')

    await callback.message.edit_text(
        text=txt.request_card_number(),
        reply_markup=skip_card_keyboard()
    )


# Шаг 7: Получение номера карты или пропуск (с проверкой на дубликат в РР)
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerCard'))
async def get_card_number(
        message: Message,
        state: FSMContext
):
    card_number = message.text.strip()

    if card_number and not validate_card_number(card_number):
        await message.answer(
            text=txt.card_number_validation_error(),
            reply_markup=skip_card_keyboard()
        )
        return

    digits = ''.join(filter(str.isdigit, card_number)) if card_number else ''

    if digits and not BYPASS_RR_API:
        rr_worker = await fin_get_worker_by_card(digits)
        if rr_worker:
            await message.answer(
                text=txt.card_already_used(),
                reply_markup=skip_card_keyboard()
            )
            return

    await state.update_data(card_number=digits)
    await state.set_state('AddWorkerBirthday')

    await message.answer(
        text=txt.request_birthday(),
        reply_markup=skip_birthday_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipCard')
async def skip_card(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(card_number='')
    await state.set_state('AddWorkerBirthday')

    await callback.message.edit_text(
        text=txt.request_birthday(),
        reply_markup=skip_birthday_keyboard()
    )


# Шаг 8: Получение даты рождения или пропуск
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerBirthday'))
async def get_birthday(
        message: Message,
        state: FSMContext
):
    birthday = message.text.strip()

    if not _is_valid_date(birthday):
        await message.answer(
            text=txt.birthday_validation_error(),
            reply_markup=skip_birthday_keyboard()
        )
        return

    await state.update_data(birthday=birthday)
    await state.set_state('AddWorkerPassportSeries')

    await message.answer(
        text=txt.request_passport_series(),
        reply_markup=skip_passport_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipBirthday')
async def skip_birthday(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(birthday='')
    await state.set_state('AddWorkerPassportSeries')

    await callback.message.edit_text(
        text=txt.request_passport_series(),
        reply_markup=skip_passport_keyboard()
    )


# Шаг 9: Серия паспорта
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerPassportSeries'))
async def get_passport_series(
        message: Message,
        state: FSMContext
):
    series = ''.join(filter(str.isdigit, message.text.strip()))

    if len(series) != 4:
        await message.answer(
            text=txt.passport_series_validation_error(),
            reply_markup=skip_passport_keyboard()
        )
        return

    await state.update_data(passport_series=series)
    await state.set_state('AddWorkerPassportNumber')

    await message.answer(
        text=txt.request_passport_number(),
        reply_markup=back_to_workers_menu_keyboard()
    )


@router.callback_query(AdminOrManager(), F.data == 'SkipPassport')
async def skip_passport(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(passport_series='', passport_number='', passport_date='')
    await state.set_state('AddWorkerTelegramId')

    await callback.message.edit_text(
        text=txt.request_telegram_id(),
        reply_markup=skip_telegram_id_keyboard()
    )


# Шаг 10: Номер паспорта
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerPassportNumber'))
async def get_passport_number(
        message: Message,
        state: FSMContext
):
    number = ''.join(filter(str.isdigit, message.text.strip()))

    if len(number) != 6:
        await message.answer(
            text=txt.passport_number_validation_error(),
            reply_markup=back_to_workers_menu_keyboard()
        )
        return

    await state.update_data(passport_number=number)
    await state.set_state('AddWorkerPassportDate')

    await message.answer(
        text=txt.request_passport_date(),
        reply_markup=back_to_workers_menu_keyboard()
    )


# Шаг 11: Дата выдачи паспорта
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerPassportDate'))
async def get_passport_date(
        message: Message,
        state: FSMContext
):
    date = message.text.strip()

    if not _is_valid_date(date):
        await message.answer(
            text=txt.passport_date_validation_error(),
            reply_markup=back_to_workers_menu_keyboard()
        )
        return

    await state.update_data(passport_date=date)
    await state.set_state('AddWorkerTelegramId')

    await message.answer(
        text=txt.request_telegram_id(),
        reply_markup=skip_telegram_id_keyboard()
    )


# Дополнительный шаг: Получение Telegram ID или пропуск
@router.message(AdminOrManager(), F.text, StateFilter('AddWorkerTelegramId'))
async def get_telegram_id(
        message: Message,
        state: FSMContext
):
    telegram_id = message.text.strip()

    if telegram_id and not validate_telegram_id(telegram_id):
        await message.answer(
            text=txt.telegram_id_validation_error(),
            reply_markup=skip_telegram_id_keyboard()
        )
        return

    await state.update_data(telegram_id=telegram_id if telegram_id else '')
    await show_confirmation(message, state)


@router.callback_query(AdminOrManager(), F.data == 'SkipTelegramId')
async def skip_telegram_id(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(telegram_id='')
    await show_confirmation(callback.message, state)


# Функция для показа подтверждения
async def show_confirmation(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()

    confirmation_text = txt.confirm_worker_data(
        last_name=data.get('last_name', ''),
        first_name=data.get('first_name', ''),
        middle_name=data.get('middle_name', ''),
        inn=data.get('inn', ''),
        phone_number=data.get('phone_number', ''),
        card_number=data.get('card_number', ''),
        telegram_id=data.get('telegram_id', ''),
        birthday=data.get('birthday', ''),
        passport_series=data.get('passport_series', ''),
        passport_number=data.get('passport_number', ''),
        passport_date=data.get('passport_date', ''),
    )

    await state.set_state('AddWorkerConfirmation')

    await message.answer(
        text=confirmation_text,
        reply_markup=confirm_save_worker_keyboard()
    )


# Подтверждение и сохранение
@router.callback_query(AdminOrManager(), F.data == 'ConfirmSaveWorker')
async def confirm_save_worker(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()

    last_name = data.get('last_name', '')
    first_name = data.get('first_name', '')
    middle_name = data.get('middle_name', '') or None
    inn = data.get('inn', '') or None
    phone_number = data.get('phone_number', '') or None
    card_number = data.get('card_number', '') or None
    telegram_id = data.get('telegram_id', '')
    telegram_id_int = int(telegram_id) if telegram_id and telegram_id.isdigit() else None
    birthday = data.get('birthday', '') or None
    passport_series = data.get('passport_series', '') or None
    passport_number = data.get('passport_number', '') or None
    passport_date = data.get('passport_date', '') or None

    # Сохраняем самозанятого в базу
    worker_id = await add_worker_manually(
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        inn=inn,
        phone_number=phone_number,
        telegram_id=telegram_id_int,
        card_number=card_number,
    )

    if worker_id is None:
        await callback.message.edit_text(
            text=txt.worker_save_error(),
            reply_markup=back_to_workers_menu_keyboard()
        )
        await state.clear()
        return

    sent_to_api = False

    if not BYPASS_RR_API:
        phone_digits = phone_number if phone_number else ''
        should_send_to_api = inn and phone_digits and len(phone_digits) == 12 and phone_digits.startswith('+7')

        if should_send_to_api:
            try:
                from API.fin.workers import fin_create_worker as _fin_create_worker
                phone_10 = phone_digits.lstrip('+')
                if phone_10.startswith('7') and len(phone_10) == 11:
                    phone_10 = phone_10[1:]

                api_worker_id = await _fin_create_worker(
                    phone_number=phone_10,
                    inn=inn,
                    card_number=card_number,
                    first_name=first_name,
                    last_name=last_name,
                    patronymic=middle_name,
                    birthday=birthday,
                    passport_series=passport_series,
                    passport_number=passport_number,
                    passport_issue_date=passport_date,
                )

                if api_worker_id is not None:
                    sent_to_api = True
                    logging.info(f'Worker {worker_id} sent to RR API with id={api_worker_id}')
                else:
                    logging.warning(f'Worker {worker_id} failed to send to RR API')
            except Exception as e:
                logging.exception(f'Error sending worker {worker_id} to RR API: {e}')
    else:
        logging.info(f'BYPASS_RR_API: skipped API registration for worker {worker_id}')

    await callback.message.edit_text(
        text=txt.worker_saved_successfully(sent_to_api=sent_to_api),
        reply_markup=back_to_workers_menu_keyboard()
    )

    await state.clear()


# Отмена добавления
@router.callback_query(AdminOrManager(), F.data == 'CancelSaveWorker')
async def cancel_save_worker(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.clear()

    await callback.message.edit_text(
        text=txt.worker_save_cancelled(),
        reply_markup=back_to_workers_menu_keyboard()
    )
