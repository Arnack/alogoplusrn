from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from filters import Admin, Director
from aiogram.filters import or_f
from utils.pdf import create_unfulfilled_pdf
import database as db


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'SelfEmployedUnfulfilled')
async def generate_unfulfilled_report(callback: CallbackQuery):
    """Сгенерировать отчёт по неисполненным заказам (активным должникам)"""
    await callback.answer()

    msg = await callback.message.edit_text(text="⏳ Формирую PDF отчёта...")

    try:
        # Получить всех активных должников
        cycles = await db.get_workers_with_active_cycles()

        if not cycles:
            back_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ В меню", callback_data="SelfEmployedMenu")]
                ]
            )
            await callback.message.edit_text(
                text="ℹ️ Нет активных должников.",
                reply_markup=back_keyboard
            )
            return

        # Генерация PDF
        pdf_bytes = await create_unfulfilled_pdf(cycles=cycles)
        pdf_name = "Неисполненные_заявки.pdf"

        # Отправка PDF
        await callback.message.answer_document(
            document=BufferedInputFile(file=pdf_bytes, filename=pdf_name),
            caption=f"📊 Отчёт по неисполненным заявкам\nАктивных должников: {len(cycles)}"
        )

        # Удалить сообщение "Формирую..."
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=msg.message_id
            )
        except:
            pass

    except Exception as e:
        logging.exception(f'Ошибка генерации отчёта по неисполненным заявкам: {e}')
        await callback.message.edit_text(text="❌ Ошибка при создании PDF. Попробуйте позже.")
