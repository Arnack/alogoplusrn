from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def skip():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Пропустить')]
        ],
        resize_keyboard=True
    )
