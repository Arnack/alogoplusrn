from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


def accountant_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Выплаты'),
             KeyboardButton(text='Запросы из начислений')],
            [KeyboardButton(text='Чеки')],
            [KeyboardButton(text="➕ Добавить должника")],
            [KeyboardButton(text="📊 Баланс начислений"),
             KeyboardButton(text="✏️ Изменение начислений")],
        ],
        resize_keyboard=True
    )
