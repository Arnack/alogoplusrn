from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from utils import get_rating
import database as db


def admin_orders_menu() -> InlineKeyboardMarkup:
    """Главное меню управления заявками"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🌆 Выбрать город', callback_data='AdminOrdersSelectCity')],
        ]
    )


async def cities_for_orders():
    """Клавиатура с городами для выбора"""
    cities = await db.get_cities_name()
    keyboard = InlineKeyboardBuilder()
    
    for city in cities:
        keyboard.row(
            InlineKeyboardButton(
                text=city,
                callback_data=f'AdminOrderCity:{city}'
            )
        )
    
    keyboard.row(InlineKeyboardButton(text='◀️ Назад', callback_data='AdminOrdersMenu'))
    return keyboard.as_markup()


async def customers_list_for_orders(city: str):
    """Список заказчиков города"""
    customers = await db.get_customers_by_city(city=city)
    keyboard = InlineKeyboardBuilder()
    
    for customer in customers:
        keyboard.row(
            InlineKeyboardButton(
                text=f"🚚 {customer.organization}",
                callback_data=f'AdminOrderCustomer:{customer.id}:{city}'
            )
        )
    
    return keyboard.as_markup()


def back_to_order_management_menu():
    """Кнопка назад к меню управления заявками"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='◀️ Назад', callback_data='BackToOrderManagement')]
        ]
    )


async def admin_orders_in_progress_info(index, page):
    """Клавиатура со списком заказов 'В работе' для администратора"""
    keyboard = InlineKeyboardBuilder()

    orders = await db.get_orders_in_progress()

    pre_sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    sorted_orders = sorted(
        pre_sorted_orders,
        key=lambda order: order.customer_id
    )

    for i in range(index - 5, len(sorted_orders)):
        if i >= index or i > len(sorted_orders):
            break
        else:
            workers_count = await db.get_order_workers_count_by_order_id(order_id=sorted_orders[i].id)
            organization = await db.get_customer_organization(customer_id=sorted_orders[i].customer_id)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{organization} | "
                         f"{sorted_orders[i].date[:5:]} {'Д' if sorted_orders[i].day_shift else 'Н'} | "
                         f"{workers_count} из {sorted_orders[i].workers}",
                    callback_data=f"AdminOrderInProgress:{sorted_orders[i].id}"
                )
            )

    pages = len(sorted_orders) // 5 if len(sorted_orders) % 5 == 0 else (len(sorted_orders)//5) + 1
    if 5 >= index >= len(sorted_orders):
        pass
    elif index == 5:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="AdminForwardOrdersInProgress"))
    elif index >= len(sorted_orders):
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="AdminBackOrdersInProgress"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"))
    else:
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="AdminBackOrdersInProgress"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="AdminForwardOrdersInProgress"))

    keyboard.row(InlineKeyboardButton(text=f"Назад", callback_data='BackToAdminWorkersMenu'))

    return keyboard.as_markup()


def admin_order_in_progress_info(order_id):
    """Клавиатура карточки заказа с кнопкой удаления исполнителя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='❌ Удалить исполнителя',
                callback_data=f'AdminOrderWorkers:{order_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data='BackToAdminOrdersInProgress'
            )]
        ]
    )


async def admin_show_order_workers(order_id):
    """Клавиатура со списком исполнителей на заказе"""
    import logging

    keyboard = InlineKeyboardBuilder()
    workers = await db.get_order_workers_id_by_order_id(order_id=order_id)

    logging.info(f"Creating keyboard for order {order_id}, workers: {workers}")

    for worker_id in workers:
        try:
            order_worker = await db.get_order_worker(
                worker_id=worker_id,
                order_id=order_id
            )
            worker = await db.get_user_real_data_by_id(user_id=worker_id)
            rating = await get_rating(user_id=worker_id)
            order_from_friend = '🔵 ' if order_worker.order_from_friend else ''

            button_text = f'{order_from_friend}{worker.last_name} {worker.first_name} {worker.middle_name} | {rating}'
            logging.info(f"Adding button: {button_text}")

            keyboard.row(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f'AdminOrderWorker:{worker_id}:{order_id}'
                )
            )
        except Exception as e:
            logging.error(f"Error adding worker {worker_id} to keyboard: {e}")

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'AdminOrderInProgress:{order_id}'))

    return keyboard.as_markup()


def admin_delete_order_worker(worker_id, order_id):
    """Клавиатура с кнопкой удаления исполнителя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='❌ Удалить исполнителя',
                                  callback_data=f'AdminDeleteOrderWorker:{worker_id}:{order_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'AdminOrderWorkers:{order_id}')]
        ]
    )


def admin_accept_delete_order_worker(worker_id, order_id):
    """Клавиатура подтверждения удаления исполнителя (Да/Нет)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Да', callback_data=f'AdminConfirmDeleteOrderWorker:{worker_id}:{order_id}'),
             InlineKeyboardButton(text='❌ Нет', callback_data=f'AdminOrderWorker:{worker_id}:{order_id}')]
        ]
    )
