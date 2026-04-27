from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def skip_middle_name_keyboard():
    """Клавиатура для пропуска отчества"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить (нет отчества)', callback_data='SkipMiddleName')]
        ]
    )


def skip_inn_keyboard():
    """Клавиатура для пропуска ИНН"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='SkipInn')]
        ]
    )


def skip_phone_keyboard():
    """Клавиатура для пропуска номера телефона"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='SkipPhone')]
        ]
    )


def skip_card_keyboard():
    """Клавиатура для пропуска номера карты"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='SkipCard')]
        ]
    )


def skip_telegram_id_keyboard():
    """Клавиатура для пропуска Telegram ID"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='SkipTelegramId')]
        ]
    )


def skip_birthday_keyboard():
    """Клавиатура для пропуска даты рождения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='SkipBirthday')]
        ]
    )


def skip_passport_keyboard():
    """Клавиатура для пропуска паспортных данных"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='⏭️ Пропустить паспорт', callback_data='SkipPassport')]
        ]
    )


def confirm_save_worker_keyboard():
    """Клавиатура для подтверждения сохранения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Сохранить', callback_data='ConfirmSaveWorker')],
            [InlineKeyboardButton(text='❌ Отменить', callback_data='CancelSaveWorker')]
        ]
    )


def back_to_workers_menu_keyboard():
    """Клавиатура для возврата в меню самозанятых"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='◀️ Назад в меню', callback_data='BackToAdmWorkersMenu')]
        ]
    )
