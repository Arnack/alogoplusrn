from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import database as db


def worker_account_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Удалить исполнителя (НПД)', callback_data='DeleteWorker')],
            [InlineKeyboardButton(text='Стереть идентификаторы входа', callback_data='EraseWorkerTgID')],
            [InlineKeyboardButton(text='Корректировка рейтинга', callback_data='CorrectWorkerRating')],
            [InlineKeyboardButton(text='Информация', callback_data='BotRules')],
            [InlineKeyboardButton(text='Назад', callback_data='BackToAdmWorkersMenu')]
        ]
    )


def confirmation_delete_worker(
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmDeleteWorker:{worker_id}'),
             InlineKeyboardButton(text='Нет', callback_data='BackToAdmWorkersMenu')]
        ]
    )


def confirmation_erase_worker_tg_id(
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmEraseWorkerTgID:{worker_id}'),
             InlineKeyboardButton(text='Нет', callback_data='BackToAdmWorkersMenu')]
        ]
    )


def correct_worker_rating(
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Обновить рейтинг',
                callback_data=f'CorrectWorkerRating:{worker_id}'
            )]
        ]
    )


def confirmation_update_total_orders(
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmUpdateTotalOrders:{worker_id}'),
             InlineKeyboardButton(text='Нет', callback_data='BackToAdmWorkersMenu')]
        ]
    )


def workers_to_search(
        workers: List[db.DataForSecurity]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for worker in workers:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{worker.last_name} {worker.first_name} {worker.middle_name}',
                callback_data=f'ConfirmSearchAction:{worker.user_id}'
            )
        )

    return keyboard.as_markup()
