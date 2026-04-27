from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from utils import delete_reminder, cancel_calls_for_worker
import keyboards.inline as ikb
from filters import Manager, Director
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('OrderWorkers:'))
async def show_workers(
        callback: CallbackQuery
):
    order_id = int(callback.data.split(':')[1])
    count = await db.get_order_workers_count_by_order_id(order_id=order_id)

    if count > 0:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.order_workers_info(),
            reply_markup=await ikb.show_order_workers(
                order_id=order_id
            )
        )
    else:
        await callback.answer(
            text=txt.order_workers_none(),
            show_alert=True
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('OrderWorker:'))
async def show_workers(
        callback: CallbackQuery
):
    await callback.answer()
    worker_id = int(callback.data.split(':')[1])
    order_id = int(callback.data.split(':')[2])
    worker = await db.get_user_real_data_by_id(user_id=worker_id)

    await callback.message.edit_text(
        text=txt.worker_info(
            full_name=f'{worker.last_name} {worker.first_name} {worker.middle_name}'
        ),
        reply_markup=ikb.delete_order_worker(
            worker_id=worker_id,
            order_id=order_id
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('DeleteOrderWorker:'))
async def confirmation_delete_worker(
        callback: CallbackQuery
):
    await callback.message.edit_text(
        text=txt.accept_delete_worker(),
        reply_markup=ikb.accept_delete_order_worker(
            worker_id=int(callback.data.split(':')[1]),
            order_id=int(callback.data.split(':')[2])
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('ConfirmDeleteOrderWorker:'))
async def delete_worker(callback: CallbackQuery):
    worker_id = int(callback.data.split(':')[1])
    order_id = int(callback.data.split(':')[2])
    user = await db.get_user_by_id(user_id=worker_id)
    count = await db.get_order_workers_count_by_order_id(order_id=order_id)

    await db.delete_order_worker(
        worker_id=worker_id,
        order_id=order_id
    )
    await delete_reminder(
        tg_id=user.tg_id,
        order_id=order_id
    )
    await cancel_calls_for_worker(
        order_id=order_id,
        worker_id=worker_id
    )
    await callback.answer(
        text=txt.order_worker_deleted(),
        show_alert=True
    )

    if count > 0:
        await callback.message.edit_text(
            text=txt.order_workers_info(),
            reply_markup=await ikb.show_order_workers(
                order_id=order_id
            )
        )
    else:
        order = await db.get_order(order_id=order_id)
        workers_count = await db.get_order_workers_count_by_order_id(order_id=order_id)
        applications_count = await db.get_applications_count_by_order_id(order_id=order_id)

        await callback.message.edit_text(
            text=await txt.moderation_order_info(
                city=order.city,
                customer_id=order.customer_id,
                job=order.job_name,
                date=order.date,
                day_shift=order.day_shift,
                night_shift=order.night_shift,
                amount=order.amount,
                workers_count=workers_count,
                order_workers=order.workers,
                applications_count=applications_count),
            reply_markup=ikb.moder_order_info(
                order_id=order_id
            )
        )
    try:
        await callback.bot.send_message(
            chat_id=user.tg_id,
            text=txt.delete_info(),
            protect_content=True
        )
    except Exception as e:
        logging.warning(f'Could not notify deleted worker (tg_id={user.tg_id}): {e}')
