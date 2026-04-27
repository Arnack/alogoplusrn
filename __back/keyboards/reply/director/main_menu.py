from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def director_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧾 Модерация заявок"),
             KeyboardButton(text="📦 Заявки")],
            [KeyboardButton(text="👤 Координатор"),
             KeyboardButton(text="🔍 СМЗ")],
            [KeyboardButton(text="📣 Уведомления"),
             KeyboardButton(text="👤 Исполнители (НПД)")],
            [KeyboardButton(text="📄 Сформировать сверку")]
        ],
        resize_keyboard=True
    )
