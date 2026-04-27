import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('AddCustomerCity:'))
async def add_city(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)
    await state.set_state('NewCity')

    await callback.message.edit_text(
        text=txt.add_city()
    )


@router.message(Admin(), F.text, StateFilter('NewCity'))
async def confirmation_save_city(
        message: Message,
        state: FSMContext
):
    await state.update_data(new_city=message.text)
    data = await state.get_data()
    organization = await db.get_customer_organization(customer_id=data['customer_id'])

    await message.answer(
        text=txt.confirmation_save_city(
            organization=organization,
            city=message.text
        ),
        reply_markup=ikb.confirmation_save_city(
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data == 'SaveNewCity')
async def save_new_city(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.save_new_city(
            customer_id=data['customer_id'],
            city=data['new_city']
        )
        await callback.answer(
            text=txt.new_city_added(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.save_city_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
        await state.clear()
