from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def go_to_rr_warning():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Перейти на РР', callback_data='GoToRR')]
        ]
    )
