import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import or_f

from filters import Admin, Director
import database as db
from utils.pdf.closure_report_pdf import generate_closure_report_pdf


router = Router()


class ClosureReportState(StatesGroup):
    waiting_for_period = State()


@router.callback_query(or_f(Admin(), Director()), F.data == 'ClosureReport')
async def ask_period(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ClosureReportState.waiting_for_period)
    await callback.message.answer(
        "Введите месяц и год (пример: 4, 04, 4.25, 04.25, 4.2025)"
    )
    await callback.answer()


@router.message(or_f(Admin(), Director()), ClosureReportState.waiting_for_period)
async def process_period(message: Message, state: FSMContext):
    text = message.text.strip()
    parsed = _parse_period(text)

    if parsed is None:
        await message.answer("❌ Неверный формат. Попробуйте: 4, 04, 4.25, 04.25 или 4.2025")
        await state.clear()
        return

    month, year = parsed
    await state.clear()

    wait_msg = await message.answer(f"⏳ Формирую отчет за {month:02d}.{year}...")

    raw_orders = await db.get_archive_orders_for_month(month, year)

    if not raw_orders:
        await wait_msg.edit_text(f"📭 Нет архивных данных за {month:02d}.{year}")
        return

    pdf_bytes = generate_closure_report_pdf(raw_orders, month, year)
    year_short = year % 100
    filename = f"Закрываемость_{month}_{year_short}.pdf"

    await message.answer_document(
        BufferedInputFile(pdf_bytes, filename=filename),
        caption=f"📊 Закрываемость за {month:02d}.{year}"
    )
    await wait_msg.delete()


def _parse_period(text: str):
    """
    Парсит ввод периода.

    Поддерживаемые форматы:
        4, 04          → апрель текущего года
        4.25, 04.25    → апрель 2025
        4.2025, 04.2025 → апрель 2025

    Returns:
        (month, year) или None при ошибке
    """
    text = text.replace(',', '.').replace('/', '.').replace('-', '.').strip()

    # Убираем лишние пробелы вокруг точки
    text = re.sub(r'\s*\.\s*', '.', text)

    parts = text.split('.')

    if len(parts) == 1:
        # Только месяц
        try:
            month = int(parts[0])
        except ValueError:
            return None
        if month < 1 or month > 12:
            return None
        return month, datetime.now().year

    elif len(parts) == 2:
        # Месяц.Год
        try:
            month = int(parts[0])
            year_part = int(parts[1])
        except ValueError:
            return None

        if month < 1 or month > 12:
            return None

        if year_part < 100:
            year = 2000 + year_part
        else:
            year = year_part

        if year < 2020 or year > 2100:
            return None

        return month, year

    return None
