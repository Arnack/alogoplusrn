from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from datetime import datetime
from math import ceil

import database as db


class ShowArchiveOrderCallbackData(
    CallbackData, prefix='ArchiveOrders'
):
    archive_id: Optional[int] = None
    menu_page: int
    action: str
    date: str


async def archive_orders_menu(
        archive_orders: List[db.OrderArchive],
        menu_page: int,
        date: str,
        items_on_page: int = 8
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
        archive_workers = await db.get_archive_order_workers(
            archive_id=sorted_orders[index].id
        )
        keyboard.row(
            InlineKeyboardButton(
                text=f"{organization} | "
                     f"{sorted_orders[index].date[:5]} {'Д' if sorted_orders[index].day_shift else 'Н'} | "
                     f"{len(archive_workers)} из {sorted_orders[index].workers_count}",
                callback_data=ShowArchiveOrderCallbackData(
                    archive_id=sorted_orders[index].id,
                    action='OpenArchiveOrder',
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
                text="▶️ Вперед", callback_data=ShowArchiveOrderCallbackData(
                    action='ForwardArchive',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )
    elif items >= len(sorted_orders):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=ShowArchiveOrderCallbackData(
                    action='BackArchive',
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
                text="Назад ◀️", callback_data=ShowArchiveOrderCallbackData(
                    action='BackArchive',
                    menu_page=menu_page,
                    date=date
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=ShowArchiveOrderCallbackData(
                    action='ForwardArchive',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )
        )

    return keyboard.as_markup()


def update_archive_order_workers_count(
        archive_id: int,
        menu_page: int,
        date: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Изменить лимит откликов по заявке',
                callback_data=ShowArchiveOrderCallbackData(
                    archive_id=archive_id,
                    action='UpdArchWorkersCount',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=ShowArchiveOrderCallbackData(
                    action='BackToArchiveMenu',
                    menu_page=menu_page,
                    date=date
                ).pack()
            )]
        ]
    )


def confirmation_update_archive_order_workers_count(
        archive_id: int,
        menu_page: int,
        date: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                 text='Да',
                 callback_data=f'ConfirmUpdateArchiveOrderWorkersCount:{archive_id}'
            ),
             InlineKeyboardButton(
                 text='Нет',
                 callback_data=ShowArchiveOrderCallbackData(
                     archive_id=archive_id,
                     action='OpenArchiveOrder',
                     menu_page=menu_page,
                     date=date
                 ).pack()
            )]
        ]
    )
