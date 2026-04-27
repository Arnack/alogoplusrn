import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.admin.menu.customers import open_customer_info
from utils import is_number
import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.callback_query(F.data.startswith('NewCustomerJob:'))
async def add_job(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)
    await state.set_state('NewJob')

    await callback.message.edit_text(
        text=txt.add_customer_job()
    )


@router.message(F.text, StateFilter('NewJob'))
async def confirmation_save_job(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        new_job=message.text
    )
    await message.answer(
        text=txt.add_job_amount()
    )
    await state.set_state('SetJobAmount')


@router.message(F.text, StateFilter('SetJobAmount'))
async def get_job_amount(
        message: Message,
        state: FSMContext
):
    if is_number(message.text):
        await state.set_state(None)
        await state.update_data(
            new_job_amount=message.text
        )
        data = await state.get_data()
        organization = await db.get_customer_organization(
            customer_id=data['customer_id']
        )

        await message.answer(
            text=txt.confirmation_save_job(
                organization=organization,
                job=data['new_job'],
                amount=message.text
            ),
            reply_markup=ikb.confirmation_save_job(
                customer_id=data['customer_id']
            )
        )
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(F.data == 'SaveNewJob')
async def save_new_job(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.save_new_job(
            customer_id=data['customer_id'],
            job=data['new_job'],
            amount=data['new_job_amount']
        )
        await callback.answer(
            text=txt.new_job_added(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.save_job_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
        await state.clear()
