from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from handlers.admin.menu.customers import open_customer_info
from utils import is_number
import keyboards.inline as ikb
import database as db
from filters import Admin
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerJobAmount:'))
async def update_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])
    await state.update_data(
        customer_id=customer_id
    )
    customer_jobs = await db.get_customer_jobs(
        customer_id=customer_id
    )
    await callback.message.edit_text(
        text=txt.customer_job_to_update(),
        reply_markup=ikb.customer_jobs_to_update(
            customer_id=customer_id,
            jobs=customer_jobs
        )
    )


@router.callback_query(Admin(), F.data.startswith('UpdateAmount:'))
async def request_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.update_data(
        job_id=int(callback.data.split(':')[1])
    )
    await callback.message.edit_text(
        text=txt.request_new_amount()
    )
    await state.set_state('RequestNewAmount')


@router.message(Admin(), F.text, StateFilter('RequestNewAmount'))
async def get_new_amount(
        message: Message,
        state: FSMContext
):
    if is_number(message.text):
        await state.update_data(
            new_amount=message.text
        )
        data = await state.get_data()
        job = await db.get_customer_job(
            customer_job_id=data['job_id']
        )
        await message.answer(
            text=txt.confirmation_save_new_amount(
                job_name=job.job,
                new_amount=message.text
            ),
            reply_markup=ikb.confirmation_save_new_amount(
                customer_id=data['customer_id'],
                job_id=data['job_id']
            )
        )
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(Admin(), F.data.startswith('SaveNewCustomerJobAmount:'))
async def confirm_save_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.set_or_update_job_amount(
            job_id=data['job_id'],
            new_amount=data['new_amount']
        )
        await callback.answer(
            text=txt.new_amount_saved(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.save_amount_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
