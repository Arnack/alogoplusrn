from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_menu():
    keyboard = [
        [KeyboardButton(text="👤 Обо мне"), KeyboardButton(text="🔍 Поиск заявок")],
        [KeyboardButton(text='🆘 СВЯЗЬ С РУКОВОДСТВОМ'), KeyboardButton(text="📝 Управление заявкой")],
        [KeyboardButton(text='💼 Заявка для друга')],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def foreman_menu():
    keyboard = [
        [KeyboardButton(text="👤 Обо мне"), KeyboardButton(text="🔍 Поиск заявок")],
        [KeyboardButton(text='🆘 СВЯЗЬ С РУКОВОДСТВОМ'), KeyboardButton(text="📝 Управление заявкой")],
        [KeyboardButton(text='📣 Оповещение на объекте'), KeyboardButton(text='💼 Заявка для друга')],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def supervisor_menu():
    keyboard = [
        [KeyboardButton(text="👤 Обо мне"), KeyboardButton(text="🔍 Поиск заявок")],
        [KeyboardButton(text='🆘 СВЯЗЬ С РУКОВОДСТВОМ'), KeyboardButton(text="📝 Управление заявкой")],
        [KeyboardButton(text='👤 Координатор'), KeyboardButton(text='💼 Заявка для друга')],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
