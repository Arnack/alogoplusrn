from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_settings():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Количество выходов"), KeyboardButton(text="💸 Размер бонуса")],
            [KeyboardButton(text='📪 Почта'), KeyboardButton(text='🛂 Наименование услуг')],
            [KeyboardButton(text="🗂️ Главное меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
