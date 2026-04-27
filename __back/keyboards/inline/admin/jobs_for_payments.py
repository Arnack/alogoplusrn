from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def jobs_fp_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить услуги', callback_data='JobsFpAdd')],
            [InlineKeyboardButton(text='📋 Список услуг', callback_data='JobsFpList')],
        ]
    )
