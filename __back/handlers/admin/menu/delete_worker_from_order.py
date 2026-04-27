import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import NoReturn

from utils import delete_reminder, get_day_of_week_by_date, cancel_calls_for_worker
import keyboards.inline as ikb
from filters import Admin, Director
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


async def open_admin_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
) -> NoReturn:
    """Открыть список заказов 'В работе' для администратора"""
    data = await state.get_data()
    count = await db.get_orders_count_in_progress()

    try:
        page = data['admin_orders_in_progress_page']
        index = data['admin_orders_in_progress_index']
    except KeyError:
        page = 1
        index = 5

    if count > 0:
        await state.update_data(admin_orders_in_progress_page=page, admin_orders_in_progress_index=index)
        await callback.message.edit_text(
            text=txt.orders_in_progress_info(),
            reply_markup=await ikb.admin_orders_in_progress_info(
                index=index,
                page=page
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_orders_in_progress(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Admin(), Director()), F.data.in_({'AdminDeleteFromOrder', 'BackToAdminOrdersInProgress'}))
async def show_admin_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
):
    """Показать меню 'В работе' администратору"""
    await callback.answer()
    await open_admin_orders_in_progress(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'AdminForwardOrdersInProgress')
async def admin_forward_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
):
    """Навигация вперед по списку заказов"""
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        admin_orders_in_progress_page=data['admin_orders_in_progress_page'] + 1,
        admin_orders_in_progress_index=data['admin_orders_in_progress_index'] + 5
    )
    await open_admin_orders_in_progress(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'AdminBackOrdersInProgress')
async def admin_back_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
):
    """Навигация назад по списку заказов"""
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        admin_orders_in_progress_page=data['admin_orders_in_progress_page'] - 1,
        admin_orders_in_progress_index=data['admin_orders_in_progress_index'] - 5
    )
    await open_admin_orders_in_progress(
        callback=callback,
        state=state
    )


async def show_admin_order_in_progress(
        callback: CallbackQuery,
        order_id: int
) -> NoReturn:
    """Показать карточку заказа с кнопкой удаления исполнителя"""
    order = await db.get_order(order_id=order_id)
    workers_count = await db.get_order_workers_count_by_order_id(order_id=order_id)

    await callback.message.edit_text(
        text=await txt.order_in_progress_info(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=order.amount,
            workers_count=workers_count,
            order_workers=order.workers
        ),
        reply_markup=ikb.admin_order_in_progress_info(
            order_id=order_id
        )
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AdminOrderInProgress:'))
async def admin_open_order_in_progress(
        callback: CallbackQuery
):
    """Обработчик выбора заказа из списка"""
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    await show_admin_order_in_progress(
        callback=callback,
        order_id=order_id
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'BackToAdminWorkersMenu')
async def back_to_admin_workers_menu(
        callback: CallbackQuery
):
    """Вернуться в меню 'Самозанятые'"""
    await callback.answer()
    workers_count = await db.get_workers_count_for_stats()
    await callback.message.edit_text(
        text=txt.stats(workers_count=workers_count),
        reply_markup=ikb.adm_workers_menu()
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AdminOrderWorkers:'))
async def show_admin_order_workers(
        callback: CallbackQuery
):
    """Показать список исполнителей на заказе"""
    order_id = int(callback.data.split(':')[1])
    count = await db.get_order_workers_count_by_order_id(order_id=order_id)

    logging.info(f"Admin viewing workers for order {order_id}, count: {count}")

    if count > 0:
        await callback.answer()
        # Проверяем какие исполнители будут показаны
        workers_ids = await db.get_order_workers_id_by_order_id(order_id=order_id)
        logging.info(f"Workers IDs: {workers_ids}")

        await callback.message.edit_text(
            text=txt.order_workers_info(),
            reply_markup=await ikb.admin_show_order_workers(
                order_id=order_id
            )
        )
    else:
        await callback.answer(
            text=txt.order_workers_none(),
            show_alert=True
        )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AdminOrderWorker:'))
async def show_admin_order_worker(
        callback: CallbackQuery
):
    """Показать информацию об исполнителе с кнопкой удаления"""
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])
    order_id = int(callback.data.split(':')[2])
    worker = await db.get_user_real_data_by_id(user_id=worker_id)

    await callback.message.edit_text(
        text=txt.worker_info(
            full_name=f'{worker.last_name} {worker.first_name} {worker.middle_name}'
        ),
        reply_markup=ikb.admin_delete_order_worker(
            worker_id=worker_id,
            order_id=order_id
        )
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AdminDeleteOrderWorker:'))
async def confirmation_admin_delete_worker(
        callback: CallbackQuery
):
    """Показать подтверждение удаления исполнителя"""
    worker_id = int(callback.data.split(':')[1])
    order_id = int(callback.data.split(':')[2])
    worker = await db.get_user_real_data_by_id(user_id=worker_id)

    await callback.message.edit_text(
        text=f'Вы действительно хотите удалить\n'
             f'{worker.last_name} {worker.first_name} {worker.middle_name}\n'
             f'исполнителя?',
        reply_markup=ikb.admin_accept_delete_order_worker(
            worker_id=worker_id,
            order_id=order_id
        )
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('AdminConfirmDeleteOrderWorker:'))
async def admin_delete_worker(callback: CallbackQuery):
    """Удалить исполнителя с заказа (администратор)"""
    worker_id = int(callback.data.split(':')[1])
    order_id = int(callback.data.split(':')[2])
    user = await db.get_user_by_id(user_id=worker_id)
    count = await db.get_order_workers_count_by_order_id(order_id=order_id)

    # Проверка: нельзя удалить последнего исполнителя
    if count <= 1:
        await callback.answer(
            text='❌ Нельзя удалить последнего исполнителя с заявки',
            show_alert=True
        )
        return

    # Удалить исполнителя из order_workers
    await db.delete_order_worker(
        worker_id=worker_id,
        order_id=order_id
    )

    # Удалить напоминание
    await delete_reminder(
        tg_id=user.tg_id,
        order_id=order_id
    )

    # Отменить запланированные звонки
    await cancel_calls_for_worker(
        order_id=order_id,
        worker_id=worker_id
    )

    # Показать alert админу
    await callback.answer(
        text='✅ Исполнитель удален',
        show_alert=True
    )

    # Отправить уведомление исполнителю
    order = await db.get_order(order_id=order_id)
    day = get_day_of_week_by_date(date=order.date)

    job_fp = await db.get_job_fp_for_txt(
        worker_id=worker_id
    )

    try:
        # 1. Сначала карточка заказа
        await callback.bot.send_message(
            chat_id=user.tg_id,
            text=await txt.show_order_search(
                city=order.city,
                customer_id=order.customer_id,
                job=order.job_name,
                date=order.date,
                day=day,
                day_shift=order.day_shift,
                night_shift=order.night_shift,
                amount=order.amount,
                job_fp=job_fp
            ),
            protect_content=True
        )

        # 2. Затем текст уведомления
        await callback.bot.send_message(
            chat_id=user.tg_id,
            text=txt.admin_delete_worker_notification(),
            protect_content=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')

    # Вернуться к карточке заказа
    await show_admin_order_in_progress(callback, order_id)
