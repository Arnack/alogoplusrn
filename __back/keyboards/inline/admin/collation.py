from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import Optional
import math

import database as db


class CollationCallbackData(
    CallbackData, prefix='Collation'
):
    customer_id: Optional[int] = None
    menu_page: int
    action: str


async def select_customer(
        menu_page: int
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    customers = await db.get_customers()

    total_pages = math.ceil(len(customers) / 5)
    items = menu_page * 5

    for i in range(items - 5, len(customers)):
        if i >= items or i > len(customers):
            break

        keyboard.row(
            InlineKeyboardButton(
                text=f'👤 {customers[i].organization}',
                callback_data=CollationCallbackData(
                    customer_id=customers[i].id,
                    action='SelectCustomer',
                    menu_page=menu_page
                ).pack()
            )
        )

    if 5 >= items >= len(customers):
        pass
    elif items == 5:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=CollationCallbackData(
                    action="ForwardCollationMenu",
                    menu_page=menu_page
                ).pack()
            )
        )
    elif items >= len(customers):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=CollationCallbackData(
                    action="BackCollationMenu",
                    menu_page=menu_page
                ).pack()),
            InlineKeyboardButton(
                text=f"{menu_page}/{total_pages}", callback_data="None"
            )
        )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=CollationCallbackData(
                    action="BackCollationMenu",
                    menu_page=menu_page
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=CollationCallbackData(
                    action="ForwardCollationMenu",
                    menu_page=menu_page
                ).pack()
            )
        )

    return keyboard.as_markup()
