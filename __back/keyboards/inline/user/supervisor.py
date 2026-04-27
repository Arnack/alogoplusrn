from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from datetime import datetime
from math import ceil

from utils import get_rating
import database as db


class ShowOrderCallbackData(
    CallbackData, prefix='ShowOrder'
):
    order_id: Optional[int] = None
    customer_id: int
    menu_page: int
    action: str


class AddWorkerCallbackData(
    ShowOrderCallbackData, prefix='AddWorker'
):
    worker_id: int


def cities_for_supervisor(
        cities: List[str]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for city_name in cities:
        keyboard.add(
            InlineKeyboardButton(
                text=city_name, callback_data=f'ReqSupervisorCity:{city_name}'
            )
        )

    return keyboard.adjust(2).as_markup()


def choose_customer(
        customers: List[db.Customer]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for customer in customers:
        keyboard.add(
            InlineKeyboardButton(
                text=customer.organization, callback_data=f'ReqSupervisorCust:{customer.id}'
            )
        )

    return keyboard.adjust(2).as_markup()


async def supervisor_orders_info(
        orders: List[db.Order],
        customer_id: int,
        menu_page: int,
        items_on_page: int = 5
):
    keyboard = InlineKeyboardBuilder()

    total_pages = ceil(len(orders) / items_on_page)
    items = menu_page * items_on_page

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    for index in range(items - items_on_page, len(sorted_orders)):
        if index >= items or index > len(sorted_orders):
            break

        workers_count = await db.get_order_workers_count_by_order_id(
            order_id=sorted_orders[index].id
        )
        applications_count = await db.get_applications_count_by_order_id(
            order_id=sorted_orders[index].id
        )

        keyboard.row(
            InlineKeyboardButton(
                text=f"{sorted_orders[index].date[:5:]} {'Д' if sorted_orders[index].day_shift else 'Н'} | "
                     f"{workers_count} из {sorted_orders[index].workers} | "
                     f"{applications_count}",
                callback_data=ShowOrderCallbackData(
                    action='SupervisorOrder',
                    order_id=sorted_orders[index].id,
                    customer_id=customer_id,
                    menu_page=menu_page
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
                text="▶️ Вперед", callback_data=ShowOrderCallbackData(
                    action='ForwardSupervisorOrder',
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            )
        )
    elif items >= len(sorted_orders):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=ShowOrderCallbackData(
                    action='BackSupervisorOrder',
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            )
        )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=ShowOrderCallbackData(
                    action='BackSupervisorOrder',
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=ShowOrderCallbackData(
                    action='ForwardSupervisorOrder',
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            )
        )

    return keyboard.as_markup()


def supervisor_order_menu(
        customer_id: int,
        order_id: int,
        menu_page: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Отклики',
                callback_data=ShowOrderCallbackData(
                    action='SuperApplications',
                    order_id=order_id,
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            ),
             InlineKeyboardButton(
                 text='Исполнители',
                 callback_data=ShowOrderCallbackData(
                    action='SuperWorkers',
                    order_id=order_id,
                    customer_id=customer_id,
                    menu_page=menu_page
                 ).pack()
             )],
            [InlineKeyboardButton(
                text='➕ Добавить исполнителя',
                callback_data=ShowOrderCallbackData(
                    action='SuperAddWorker',
                    order_id=order_id,
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=ShowOrderCallbackData(
                    action='BackToSupervisorOrders',
                    customer_id=customer_id,
                    menu_page=menu_page
                ).pack()
            )],
        ]
    )


async def supervisor_applications(
        applications: List[db.OrderApplication],
        order_id: int,
        customer_id: int,
        menu_page: int
):
    keyboard = InlineKeyboardBuilder()

    for application in applications:
        user = await db.get_user_real_data_by_id(
            user_id=application.worker_id
        )
        rating = await get_rating(
            user_id=application.worker_id
        )

        order_from_friend = '🔵 ' if application.order_from_friend else ''

        keyboard.row(
            InlineKeyboardButton(
                text=f'{order_from_friend}{user.last_name} {user.first_name} {user.middle_name} | {rating}',
                callback_data=f'None'
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text='Назад',
            callback_data=ShowOrderCallbackData(
                action='SupervisorOrder',
                order_id=order_id,
                customer_id=customer_id,
                menu_page=menu_page
            ).pack()
        )
    )

    return keyboard.as_markup()


async def supervisor_order_workers(
        order_id: int,
        customer_id: int,
        menu_page: int
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    workers = await db.get_order_workers_id_by_order_id(
        order_id=order_id
    )

    for worker_id in workers:
        order_worker = await db.get_order_worker(
            worker_id=worker_id,
            order_id=order_id
        )
        worker = await db.get_user_real_data_by_id(
            user_id=worker_id
        )
        rating = await get_rating(user_id=worker_id)
        order_from_friend = '🔵 ' if order_worker.order_from_friend else ''

        keyboard.row(
            InlineKeyboardButton(
                text=f'{order_from_friend}{worker.last_name} {worker.first_name} {worker.middle_name} | {rating}',
                callback_data=f'None'
            )
        )

    keyboard.row(
        InlineKeyboardButton(
            text='Назад',
            callback_data=ShowOrderCallbackData(
                action='SupervisorOrder',
                order_id=order_id,
                customer_id=customer_id,
                menu_page=menu_page
            ).pack()
        )
    )

    return keyboard.as_markup()


def supervisor_confirmation_add_order_worker(
        worker_id: int,
        order_id: int,
        customer_id: int,
        menu_page: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Да',
                callback_data=AddWorkerCallbackData(
                    action='ConfirmAddWorker',
                    order_id=order_id,
                    customer_id=customer_id,
                    worker_id=worker_id,
                    menu_page=menu_page
                ).pack()
            ),
             InlineKeyboardButton(
                 text='Нет',
                 callback_data=ShowOrderCallbackData(
                     action='SupervisorOrder',
                     order_id=order_id,
                     customer_id=customer_id,
                     menu_page=menu_page
                 ).pack()
             )]
        ]
    )
