from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from decimal import Decimal
import logging

from handlers.admin.menu.workers.adm_workers import open_workers_menu
import keyboards.inline as ikb
from filters import Admin, Director
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('CorrectWorkerRating:'))
async def confirm_correct_rating(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_text(
        text=txt.request_new_total_orders()
    )
    await state.set_state('RequestTotalOrders')
    await state.update_data(
        WorkerID=int(callback.data.split(':')[1])
    )


@router.message(F.text, StateFilter('RequestTotalOrders'))
async def get_new_total_orders(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        new_total_orders = int(message.text)
        data = await state.get_data()
        user_rating = await db.get_user_rating(
            user_id=data['WorkerID']
        )
        if user_rating.successful_orders <= new_total_orders:
            await state.set_state(None)
            await state.update_data(
                TotalOrders=new_total_orders
            )
            real_data = await db.get_user_real_data_by_id(
                user_id=data['WorkerID']
            )
            new_rating = (
                (Decimal(user_rating.successful_orders) / Decimal(new_total_orders)) * Decimal('100')
            ) + Decimal(f'{user_rating.plus}')
            await message.answer(
                text=txt.confirmation_update_total_orders(
                    full_name=f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}',
                    rating=f'{new_rating:.2f}%'
                ),
                reply_markup=ikb.confirmation_update_total_orders(
                    worker_id=data['WorkerID']
                ),
            )
        else:
            await message.answer(
                text=txt.new_total_orders_error()
            )
    else:
        await message.answer(
            text=txt.number_error()
        )


@router.callback_query(F.data.startswith('ConfirmUpdateTotalOrders:'))
async def confirmation_update_worker_rating(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        data = await state.get_data()
        worker_id = int(callback.data.split(':')[1])
        await db.update_worker_rating(
            total_orders=data['TotalOrders'],
            worker_id=worker_id
        )
        await callback.answer(
            text=txt.worker_rating_updated(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.update_worker_rating_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await open_workers_menu(
            callback=callback
        )
