from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def proceed():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Далее')]
        ],
        resize_keyboard=True
    )
