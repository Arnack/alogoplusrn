from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from typing import List

from utils import get_rating
import database as db


async def show_order_workers(order_id):
    keyboard = InlineKeyboardBuilder()
    workers = await db.get_order_workers_id_by_order_id(order_id=order_id)

    for worker_id in workers:
        order_worker = await db.get_order_worker(
            worker_id=worker_id,
            order_id=order_id
        )
        worker = await db.get_user_real_data_by_id(user_id=worker_id)
        rating = await get_rating(user_id=worker_id)
        order_from_friend = '🔵 ' if order_worker.order_from_friend else ''
        rr_mark = '🔺 ' if getattr(order_worker, 'is_rr_worker', False) else ''

        keyboard.row(
            InlineKeyboardButton(
                text=f'{rr_mark}{order_from_friend}{worker.last_name} {worker.first_name} {worker.middle_name} | {rating}',
                callback_data=f'OrderWorker:{worker_id}:{order_id}'
            )
        )

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'ManagerModerationOrder:{order_id}'))

    return keyboard.as_markup()


def delete_order_worker(worker_id, order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='❌Удалить исполнителя',
                                  callback_data=f'DeleteOrderWorker:{worker_id}:{order_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'OrderWorkers:{order_id}')]
        ]
    )


def accept_delete_order_worker(worker_id, order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmDeleteOrderWorker:{worker_id}:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'OrderWorker:{worker_id}:{order_id}')]
        ]
    )


def workers_to_add(
        workers: List[db.DataForSecurity]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for worker in workers:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{worker.last_name} {worker.first_name} {worker.middle_name}',
                callback_data=f'ConfirmationAddToOrderWorkers:{worker.user_id}'
            )
        )

    return keyboard.as_markup()


def confirmation_add_order_worker(
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmAddToOrderWorkers:{worker_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelAddToOrderWorkers')]
        ]
    )
