from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def confirmation_send_help_message() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'SendHelpMessage'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelSendHelpMessage')],
        ]
    )