from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎭 Роли"), KeyboardButton(text="🏢 Получатели услуг")],
            [KeyboardButton(text="👤 Исполнители (НПД)"), KeyboardButton(text="📦 Заявки")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text='📊 Математика')],
            [KeyboardButton(text='📄 Сформировать сверку')],
        ],
        resize_keyboard=True
    )
