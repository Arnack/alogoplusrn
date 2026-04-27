from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def customer_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Управление заявками"),
             KeyboardButton(text='Самосверка')]
        ],
        resize_keyboard=True
    )
