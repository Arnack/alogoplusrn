from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import Optional
from math import ceil

import database as db


class WalletPaymentCallbackData(
    CallbackData, prefix='WalletPayments'
):
    wp_id: Optional[int] = None
    amount: Optional[str] = None
    worker_id: Optional[int] = None
    menu_page: int
    action: str
    date: str


def wallet_payments_menu(
        wallet_payments: list[db.WalletPayment],
        menu_page: int,
        date: str,
        items_on_page: int = 5,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    total_pages = ceil(len(wallet_payments) / items_on_page)
    items = menu_page * items_on_page

    for index in range(items - items_on_page, len(wallet_payments)):
        if index >= items or index > len(wallet_payments):
            break

        keyboard.row(
            InlineKeyboardButton(
                text=f"{wallet_payments[index].worker.last_name} "
                     f"{wallet_payments[index].worker.first_name} "
                     f"{wallet_payments[index].worker.middle_name}| "
                     f"{wallet_payments[index].amount}",
                callback_data=WalletPaymentCallbackData(
                    wp_id=wallet_payments[index].id,
                    amount=wallet_payments[index].amount,
                    worker_id=wallet_payments[index].worker_id,
                    action='OpenWP',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )

    if items_on_page >= items >= len(wallet_payments):
        pass
    elif items == items_on_page:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=WalletPaymentCallbackData(
                    action='ShowWalletPayments',
                    menu_page=menu_page + 1,
                    date=date
                ).pack()
            )
        )
    elif items >= len(wallet_payments):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=WalletPaymentCallbackData(
                    action='ShowWalletPayments',
                    menu_page=menu_page - 1,
                    date=date
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            )
        )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=WalletPaymentCallbackData(
                    action='ShowWalletPayments',
                    menu_page=menu_page - 1,
                    date=date
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=WalletPaymentCallbackData(
                    action='ShowWalletPayments',
                    menu_page=menu_page + 1,
                    date=date
                ).pack()
            )
        )

    return keyboard.as_markup()