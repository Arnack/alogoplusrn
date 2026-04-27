from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def order_management():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📝 Ваши заявки', callback_data='AllCustomerOrders')],
            [InlineKeyboardButton(text='➕ Новая заявка', callback_data='AddOrder')]
        ]
    )
