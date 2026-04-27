from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date, timedelta

import database as db


def save_order():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveOrder')],
            [InlineKeyboardButton(text="🔄 Ввести другие данные", callback_data='AddOrder')],
            [InlineKeyboardButton(text="❌ Отменить добавление", callback_data='CancelAddOrder')]
        ]
    )


async def customer_date_list():
    keyboard = InlineKeyboardBuilder()

    today = date.today()
    dates = [today + timedelta(days=i) for i in range(8)]
    formatted_dates = [d.strftime('%d.%m.%Y') for d in dates]

    for d in formatted_dates:
        keyboard.add(InlineKeyboardButton(text=f'{d}',
                                          callback_data=f"Date:{d}"))

    keyboard.row(InlineKeyboardButton(text='Ввести другую', callback_data='InputDate'))

    return keyboard.adjust(2).as_markup()


async def customer_jobs_list(admin):
    keyboard = InlineKeyboardBuilder()
    all_jobs = await db.get_customer_admin_jobs(admin=admin)

    for job in all_jobs:
        keyboard.add(InlineKeyboardButton(text=f'{job}',
                                          callback_data=f"SetOrderJob:{job}"))

    return keyboard.adjust(1).as_markup()


async def customer_shifts(admin):
    customer = await db.get_customer_shifts(admin=admin)
    keyboard = InlineKeyboardBuilder()

    if customer.day_shift and customer.night_shift:
        keyboard.row(InlineKeyboardButton(text=customer.day_shift,
                                          callback_data=f'OrderSetDayShift:{customer.day_shift}'),
                     InlineKeyboardButton(text=customer.night_shift,
                                          callback_data=f'OrderSetNightShift:{customer.night_shift}'))
    elif customer.day_shift:
        keyboard.row(InlineKeyboardButton(text=customer.day_shift,
                                          callback_data=f'OrderSetDayShift:{customer.day_shift}'))
    elif customer.night_shift:
        keyboard.row(InlineKeyboardButton(text=customer.night_shift,
                                          callback_data=f'OrderSetNightShift:{customer.night_shift}'))

    return keyboard.as_markup()


async def customer_cities_list(admin):
    keyboard = InlineKeyboardBuilder()
    all_cities = await db.get_customer_cities_by_admin(admin=admin)

    for city in all_cities:
        keyboard.add(InlineKeyboardButton(text=f'{city}',
                                          callback_data=f"OrderCity:{city}"))

    return keyboard.adjust(1).as_markup()
