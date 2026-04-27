from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
import logging

from filters import Admin, Director
from aiogram.filters import or_f
from utils.pdf import create_archive_pdf
from utils import parse_date_from_str_to_str
import database as db


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'SelfEmployedArchive')
async def request_archive_start(callback: CallbackQuery, state: FSMContext):
    """Запросить начальную дату для архива"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        text="📅 Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:",
        parse_mode='HTML'
    )
    await state.set_state('ArchiveDebtorsStartDate')


@router.message(or_f(Admin(), Director()), F.text, StateFilter('ArchiveDebtorsStartDate'))
async def get_archive_start(message: Message, state: FSMContext):
    """Получить начальную дату и запросить конечную"""
    # Парсинг даты
    date_str = parse_date_from_str_to_str(message.text)
    if not date_str:
        await message.answer(text="❌ Неверный формат даты.\n\n💡 Примеры: <code>1.1</code>, <code>31.12</code>, <code>01.01.2026</code>", parse_mode='HTML')
        return

    await state.update_data(ArchiveStartDate=date_str)
    await message.answer(text="📅 Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:", parse_mode='HTML')
    await state.set_state('ArchiveDebtorsEndDate')


@router.message(or_f(Admin(), Director()), F.text, StateFilter('ArchiveDebtorsEndDate'))
async def get_archive_end_and_generate(message: Message, state: FSMContext):
    """Получить конечную дату и сгенерировать PDF"""
    # Парсинг даты
    end_date_str = parse_date_from_str_to_str(message.text)
    if not end_date_str:
        await message.answer(text="❌ Неверный формат даты.\n\n💡 Примеры: <code>1.1</code>, <code>31.12</code>, <code>01.01.2026</code>", parse_mode='HTML')
        return

    data = await state.get_data()
    start_date_str = data['ArchiveStartDate']
    await state.clear()

    msg = await message.answer(text="⏳ Формирую PDF архива удержаний...")

    try:
        # Получить данные за период
        cycles = await db.get_cycles_for_archive_report(
            start_date_str=start_date_str,
            end_date_str=end_date_str
        )

        if not cycles:
            back_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="SelfEmployedMenu")]
                ]
            )
            await msg.edit_text(
                text="ℹ️ Нет данных за указанный период.",
                reply_markup=back_keyboard
            )
            return

        # Генерация PDF
        pdf_bytes = await create_archive_pdf(cycles=cycles)
        pdf_name = f"Архив_удержаний_{start_date_str.replace('.', '_')}-{end_date_str.replace('.', '_')}.pdf"

        # Отправка PDF
        await message.answer_document(
            document=BufferedInputFile(file=pdf_bytes, filename=pdf_name),
            caption=f"📁 Архив удержаний за период {start_date_str} — {end_date_str}"
        )
        await msg.delete()

    except Exception as e:
        logging.exception(f'Ошибка генерации архива удержаний: {e}')
        await msg.edit_text(text="❌ Ошибка при создании PDF. Попробуйте позже.")
