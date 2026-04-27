from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def help_skip():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")],
        ],
        resize_keyboard=True
    )