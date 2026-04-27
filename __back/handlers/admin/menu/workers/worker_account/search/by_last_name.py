from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f

import keyboards.inline as ikb
from utils import get_rating
from filters import (
    Admin, Supervisor, Director
)
import database as db
import texts as txt


router = Router()


@router.message(or_f(Admin(), Director()), F.text, StateFilter('RequestLastName'))
@router.message(Supervisor(), F.text, StateFilter('RequestLastName'))
async def get_worker_last_name(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    workers = await db.get_workers_by_last_name(
        last_name=message.text
    )
    if workers:
        await message.answer(
            text=txt.choose_worker_to_search(),
            reply_markup=ikb.workers_to_search(
                workers=workers
            )
        )
        await state.update_data(
            WorkerLastName=message.text
        )
    else:
        await message.answer(
            text=txt.worker_not_found()
        )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('ConfirmSearchAction:'))
@router.callback_query(Supervisor(), F.data.startswith('ConfirmSearchAction:'))
async def get_worker_last_name(
        callback: CallbackQuery,
        state: FSMContext
):
    worker_id = int(callback.data.split(':')[1])
    worker = await db.get_user_real_data_by_id(
        user_id=worker_id
    )
    full_name = f'{worker.last_name} {worker.first_name} {worker.middle_name}'
    data = await state.get_data()

    if data['AccountAction'] == 'Delete':
        await callback.message.edit_text(
            text=txt.confirmation_delete_worker(
                full_name=full_name
            ),
            reply_markup=ikb.confirmation_delete_worker(
                worker_id=worker_id
            )
        )
    elif data['AccountAction'] == 'EraseTgID':
        await callback.message.edit_text(
            text=txt.confirmation_erase_worker_tg_id(
                full_name=full_name
            ),
            reply_markup=ikb.confirmation_erase_worker_tg_id(
                worker_id=worker_id
            )
        )
    elif data['AccountAction'] == 'CorrectRating':
        rating = await get_rating(
            user_id=worker_id
        )
        user_rating = await db.get_user_rating(
            user_id=worker_id
        )
        await callback.message.edit_text(
            text=txt.confirmation_erase_worker_rating(
                full_name=full_name,
                rating=rating,
                successful_orders=user_rating.successful_orders,
                total_orders=user_rating.total_orders
            ),
            reply_markup=ikb.correct_worker_rating(
                worker_id=worker_id
            )
        )
    elif data['AccountAction'] == 'AddWorker':
        await callback.message.edit_text(
            text=txt.supervisor_confirmation_add_order_worker(
                full_name=full_name
            ),
            reply_markup=ikb.supervisor_confirmation_add_order_worker(
                order_id=data['OrderID'],
                worker_id=worker_id,
                customer_id=data['CustomerID'],
                menu_page=data['MenuPage']
            )
        )
    elif data['AccountAction'] == 'BlockUser':
        await callback.message.edit_text(
            text=txt.confirmation_block_user(
                full_name=full_name
            ),
            reply_markup=ikb.confirmation_block_worker(
                worker_id=worker_id
            )
        )
