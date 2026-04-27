from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def manager_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧾 Модерация заявок")],
            [KeyboardButton(text="✍️ Уведомление"),
             KeyboardButton(text="🗂️ Архив")],
            [KeyboardButton(text="📞 Прозвоны"),
             KeyboardButton(text="📋 Архив прозвонов")],
            [KeyboardButton(text="🔍 СМЗ"),
            KeyboardButton(text="🚶 СМЗ")]
        ],
        resize_keyboard=True
    )
