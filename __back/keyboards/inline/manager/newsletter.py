from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

import database as db


def accept_newsletter():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data='Newsletter'),
             InlineKeyboardButton(text='Нет', callback_data='NewsletterCancel')]
        ]
    )


async def cities_for_newsletter():
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city, callback_data=f'NewsletterCity:{city}'))

    return keyboard.adjust(2).as_markup()

