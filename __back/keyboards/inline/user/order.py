from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

import database as db


def respond_to_an_order(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Взять заявку', callback_data=f'RespondToAnOrder:{order_id}')]
        ]
    )


def accept_respond(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'ConfirmRespond:{order_id}'),
             InlineKeyboardButton(text='❌ Отказаться', callback_data=f'CancelRespond:{order_id}')]
        ]
    )


def accept_respond_in_search(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'ConfirmRespond:{order_id}'),
             InlineKeyboardButton(text='❌ Отказаться', callback_data=f'BackToSearchOrders')]
        ]
    )


def confirmation_respond_for_friend(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'ConfirmRespond:{order_id}'),
             InlineKeyboardButton(text='❌ Отказаться', callback_data=f'CancelRespondOrderForFriend')]
        ]
    )


async def show_order_for_search(page, orders, order_id):
    count = len(orders)
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='Взять заявку', callback_data=f'RespondToAnOrderSearch:{order_id}'))

    if count == 1:
        pass
    elif page == 1:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='SearchOrderForward'))
    elif page == count:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='SearchOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'))
    else:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='SearchOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='SearchOrderForward'))

    keyboard.row(InlineKeyboardButton(text=f"Назад", callback_data='BackToCustomerSearchOrders'))

    return keyboard.as_markup()


async def customer_search_orders(
        customers: List[int],
        items: int,
        page: int
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i in range(items - 5, len(customers)):
        if i >= items or i > len(customers):
            break
        else:
            customer = await db.get_customer(
                customer_id=customers[i]
            )
            keyboard.row(
                InlineKeyboardButton(
                    text=f"🚚 {customer.organization}",
                    callback_data=f"CustomerSearchOrders:{customer.id}"
                )
            )

    pages = len(customers) // 5 if len(customers) % 5 == 0 else (len(customers)//5) + 1
    if 5 >= items >= len(customers):
        pass
    elif items == 5:
        keyboard.row(
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
            InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardCustomerSearchOrders")
        )
    elif items >= len(customers):
        keyboard.row(
            InlineKeyboardButton(text="Назад ◀️", callback_data="BackCustomerSearchOrders"),
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Назад ◀️", callback_data="BackCustomerSearchOrders"),
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
            InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardCustomerSearchOrders")
        )

    return keyboard.as_markup()


def support():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Написать в поддержку', url='https://t.me/helpmealgoritm')]
        ]
    )
