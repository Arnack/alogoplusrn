from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from filters import Admin, Director
from aiogram.filters import or_f


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'SelfEmployedMenu')
async def open_self_employed_menu(callback: CallbackQuery, state: FSMContext):
    """Открыть меню управления договорными комиссиями"""
    await callback.answer()
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Аннулирование", callback_data="SelfEmployedAnnul")],
            [InlineKeyboardButton(text="📁 Архив удержаний", callback_data="SelfEmployedArchive")],
            [InlineKeyboardButton(text="📊 Неисполненные заявки", callback_data="SelfEmployedUnfulfilled")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="BackToAdmWorkersMenu")]
        ]
    )

    await callback.message.edit_text(
        text="<b>💰 Управление договорными комиссиями</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )
