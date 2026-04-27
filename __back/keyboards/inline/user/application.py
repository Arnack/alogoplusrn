from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Union

import database as db


async def remove_application(
        order_id: int,
        tg_id: int,
        worker_id: int,
        page: int,
        count: int,
        state: FSMContext
) -> InlineKeyboardMarkup:
    applications = await db.get_applications_by_worker_id(worker_id=worker_id)
    keyboard = InlineKeyboardBuilder()

    foreman = await db.get_foreman_by_tg_id(
        foreman_tg_id=tg_id
    )
    if foreman:
        await state.update_data(
            ForemanWorkerID=worker_id
        )
        check_order_moderation = await db.check_foreman_order_applications(
            customer_id=foreman.customer_id,
            order_id=order_id
        )
        check_order_progress = await db.check_foreman_order_progress(
            customer_id=foreman.customer_id,
            order_id=order_id
        )
        order_workers = await db.get_order_workers_id_by_order_id(
            order_id=order_id
        )

        foreman_in_order_workers = False
        for worker in order_workers:
            if worker == worker_id:
                foreman_in_order_workers = True
                break

        if foreman_in_order_workers:
            order_workers_count = len(order_workers) - 1
        else:
            order_workers_count = len(order_workers)

        if order_workers_count > 0:
            keyboard.row(
                InlineKeyboardButton(
                    text='Исполнители PDF',
                    callback_data=f'ForemanGetPdfWithWorkers:{order_id}'
                )
            )

        if check_order_moderation:
            if not check_order_moderation.moderation and not check_order_moderation.in_progress:
                keyboard.row(
                    InlineKeyboardButton(
                        text='Отклики',
                        callback_data=f'ForemanShowOrderApplications:{order_id}'
                    )
                )
        elif check_order_progress:
            if not check_order_progress.moderation and not check_order_progress.in_progress:
                keyboard.row(
                    InlineKeyboardButton(
                        text='Отклики',
                        callback_data=f'ForemanShowOrderApplications:{order_id}'
                    )
                )

    if order_id in applications:
        application_id = await db.get_worker_application_id(order_id=order_id, worker_id=worker_id)
        keyboard.row(InlineKeyboardButton(text='Отказаться от заявки',
                                          callback_data=f'RemoveApplication:{application_id}'))
    else:
        worker_app_id = await db.get_worker_app_id(order_id=order_id, worker_id=worker_id)
        keyboard.row(InlineKeyboardButton(text='Отказаться от заявки',
                                          callback_data=f'RemoveWorker:{worker_app_id}'))

    if count == 1:
        pass
    elif page == 1:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='UserApplicationsForward'))
    elif page == count:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='UserApplicationsBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'))
    else:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='UserApplicationsBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='UserApplicationsForward'))

    return keyboard.as_markup()


def accept_remove_application(application_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да',
                                  callback_data=f'ConfirmRemoveApplication:{application_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'Reject')]
        ]
    )


def confirmation_remove_worker(worker_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmRemoveWorker:{worker_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'Reject')]
        ]
    )


async def way_to_work(
        customer_id: int,
        city: str
) -> Union[InlineKeyboardMarkup, None]:
    customer_city_id = await db.get_customer_city_id(
        customer_id=customer_id,
        city=city
    )
    way = await db.get_customer_city_way(
        city_id=customer_city_id
    )
    if way:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='‼️ℹ️📍🚍', callback_data=f'WorkerShowCityWay:{customer_city_id}')]
            ]
        )
