from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

import database as db


def order_for_friend_confirmation() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Продолжить', callback_data='ContinueOrderForFriend'),
             InlineKeyboardButton(text='Отменить', callback_data='CancelOrderForFriend')]
        ]
    )


def methods_search_friend() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Номер телефона', callback_data='SearchWorkerByPhone'),
             InlineKeyboardButton(text='ИНН', callback_data='SearchWorkerByInn')]
        ]
    )


async def cities_for_order_for_friend() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        keyboard.add(
            InlineKeyboardButton(text=city, callback_data=f'CityForFriend:{city}')
        )

    return keyboard.adjust(2).as_markup()
