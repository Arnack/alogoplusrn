from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import NoReturn

from filters import Manager, Director
from aiogram.filters import or_f
import texts as txt
import keyboards.inline as ikb
import database as db


router = Router()


async def open_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
) -> NoReturn:
    data = await state.get_data()
    count = await db.get_orders_count_in_progress()

    try:
        page = data['orders_in_progress_page']
        index = data['orders_in_progress_index']
    except KeyError:
        page = 1
        index = 5

    if count > 0:
        await state.update_data(orders_in_progress_page=page, orders_in_progress_index=index)
        await callback.message.edit_text(
            text=txt.orders_in_progress_info(),
            reply_markup=await ikb.orders_in_progress_info(
                index=index,
                page=page
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_orders_in_progress(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data.in_({'ShowOrdersInProgress', 'BackToOrdersInProgress'}))
async def show_orders_in_progress(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await open_orders_in_progress(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Manager(), Director()), F.data == 'ForwardOrdersInProgress')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        orders_in_progress_page=data['orders_in_progress_page'] + 1,
        orders_in_progress_index=data['orders_in_progress_index'] + 5
    )
    await open_orders_in_progress(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Manager(), Director()), F.data == 'BackOrdersInProgress')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        orders_in_progress_page=data['orders_in_progress_page'] - 1,
        orders_in_progress_index=data['orders_in_progress_index'] - 5
    )
    await open_orders_in_progress(
        callback=callback,
        state=state
    )


async def show_order_in_progress(
        callback: CallbackQuery,
        order_id: int
) -> NoReturn:
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
        reply_markup=ikb.order_in_progress_info(
            order_id=order_id
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('OrderInProgress:'))
async def open_moder_order(
        callback: CallbackQuery
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    await show_order_in_progress(
        callback=callback,
        order_id=order_id
    )
