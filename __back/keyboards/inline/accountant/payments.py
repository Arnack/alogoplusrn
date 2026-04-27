from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from datetime import datetime
from typing import Optional
from math import ceil

import database as db
from utils.organizations import orgs_dict


class ShowPaymentOrderCallbackData(
    CallbackData, prefix='PaymentOrders'
):
    order_id: Optional[int] = None
    menu_page: int
    action: str
    date: str


class ReceiptQueueCallbackData(
    CallbackData, prefix='ReceiptQueue'
):
    wp_id: Optional[int] = None
    menu_page: int
    action: str
    date: str


async def orders_for_payments(
        archive_orders: list[db.OrderArchive],
        menu_page: int,
        date: str,
        items_on_page: int = 5,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    total_pages = ceil(len(archive_orders) / items_on_page)
    items = menu_page * items_on_page

    pre_sorted_orders = sorted(
        archive_orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    sorted_orders = sorted(
        pre_sorted_orders,
        key=lambda order: order.customer_id
    )

    for index in range(items - items_on_page, len(sorted_orders)):
        if index >= items or index > len(sorted_orders):
            break

        organization = await db.get_customer_organization(
            customer_id=sorted_orders[index].customer_id
        )
        keyboard.row(
            InlineKeyboardButton(
                text=f"{organization} | "
                     f"{sorted_orders[index].date[:5]} | "
                     f"{'Д' if sorted_orders[index].day_shift else 'Н'}",
                callback_data=ShowPaymentOrderCallbackData(
                    order_id=sorted_orders[index].order_id,
                    action='OpenPayment',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )

    if items_on_page >= items >= len(sorted_orders):
        pass
    elif items == items_on_page:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=ShowPaymentOrderCallbackData(
                    action='ForwardPayment',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )
    elif items >= len(sorted_orders):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=ShowPaymentOrderCallbackData(
                    action='BackPayment',
                    menu_page=menu_page,
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
                text="Назад ◀️", callback_data=ShowPaymentOrderCallbackData(
                    action='BackPayment',
                    menu_page=menu_page,
                    date=date
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=ShowPaymentOrderCallbackData(
                    action='ForwardPayment',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )

    return keyboard.as_markup()


def confirmation_payment_order(
        order_id: int,
        total_amount: str,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='✅ Оставить суммы', callback_data=f'PaymentNotChangeAmounts:{order_id}:{total_amount}'
             ),
             InlineKeyboardButton(
                 text='✏️ Изменить суммы', callback_data=f'PaymentChangeAmounts:{order_id}'
             ),]
        ]
    )


def choose_org_for_payment(
        order_id: int,
        orgs: list[dict]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for org in orgs:
        keyboard.row(
            InlineKeyboardButton(
                text=f"{orgs_dict[org['id']]} — {org['balance']}₽",
                callback_data=f"ConfirmationCreatePayment:{order_id}:{org['id']}"
            )
        )

    return keyboard.as_markup()


def choose_ip_for_wallet_payment(
        wp_id: int,
        orgs: list[dict]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for org in orgs:
        keyboard.row(
            InlineKeyboardButton(
                text=f"{orgs_dict[org['id']]} — {org['balance']}₽",
                callback_data=f"ConfirmationCreateWP:{wp_id}:{org['id']}"
            )
        )

    return keyboard.as_markup()

def confirmation_create_payment(
        order_id: int,
        org_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmCreatePayment:{order_id}:{org_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelCreatePayment:{order_id}'),]
        ]
    )


def confirmation_create_wallet_payment(
        wp_id: int,
        org_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmCreateWP:{wp_id}:{org_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelCreateWP:{wp_id}'),]
        ]
    )


def receipts_queue_menu(
        items: list[dict],
        menu_page: int,
        date: str,
        items_on_page: int = 5,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    total_pages = max(1, ceil(len(items) / items_on_page)) if items else 1
    start = (menu_page - 1) * items_on_page
    end = start + items_on_page

    for item in items[start:end]:
        keyboard.row(
            InlineKeyboardButton(
                text=f"{item['status_emoji']} {item['date']} | {item['full_name']} | {item['amount']}",
                callback_data=ReceiptQueueCallbackData(
                    wp_id=item['wp_id'],
                    action='OpenReceipt',
                    menu_page=menu_page,
                    date=date,
                ).pack(),
            )
        )

    nav_buttons = []
    if menu_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text='Назад ◀️',
                callback_data=ReceiptQueueCallbackData(action='ShowReceipts', menu_page=menu_page - 1, date=date).pack(),
            )
        )
    nav_buttons.append(InlineKeyboardButton(text=f'{menu_page}/{total_pages}', callback_data='None'))
    if end < len(items):
        nav_buttons.append(
            InlineKeyboardButton(
                text='▶️ Вперед',
                callback_data=ReceiptQueueCallbackData(action='ShowReceipts', menu_page=menu_page + 1, date=date).pack(),
            )
        )
    if nav_buttons:
        keyboard.row(*nav_buttons)
    return keyboard.as_markup()


def receipt_item_actions(wp_id: int, *, can_pay: bool, has_receipt: bool) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    if can_pay:
        keyboard.row(
            InlineKeyboardButton(text='Оплатить', callback_data=f'ReceiptPay:{wp_id}')
        )
    keyboard.row(
        InlineKeyboardButton(text='Добавить чек', callback_data=f'ReceiptAdd:{wp_id}')
    )
    if has_receipt:
        keyboard.row(
            InlineKeyboardButton(text='Новый чек', callback_data=f'ReceiptNew:{wp_id}')
        )
    return keyboard.as_markup()
