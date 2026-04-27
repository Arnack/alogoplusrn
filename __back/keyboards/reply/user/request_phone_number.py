from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def request_phone_number():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True
    )
