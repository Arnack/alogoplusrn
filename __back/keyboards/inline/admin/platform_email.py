from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def platform_email_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Редактировать', callback_data='EditPlatformEmails')],
            [InlineKeyboardButton(text='Назад', callback_data='AdminMainMenu')]
        ]
    )


def confirm_platform_emails() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Сохранить', callback_data='SavePlatformEmails'),
             InlineKeyboardButton(text='❌ Отменить', callback_data='PlatformEmailMenu')]
        ]
    )
