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


@router.callback_query(Admin(), F.data.startswith('UpdateNightShift:'))
async def update_night_shift(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)
    await state.set_state('UpdateNightShift')

    await callback.message.edit_text(
        text=txt.update_customer_night_shift()
    )


@router.message(Admin(), F.text, StateFilter('UpdateNightShift'))
async def confirmation_save_night_shift(
        message: Message,
        state: FSMContext
):
    if '-' in message.text:
        await state.update_data(new_night_shift=message.text)
        data = await state.get_data()
        organization = await db.get_customer_organization(customer_id=data['customer_id'])
        await message.answer(
            text=txt.confirmation_save_night_shift(
                organization=organization,
                time=message.text
            ),
            reply_markup=ikb.confirmation_update_night_shift(
                customer_id=data['customer_id']
            )
        )
    else:
        await message.answer(
            text=txt.time_error()
        )


@router.callback_query(Admin(), F.data == 'SaveNewNightShift')
async def save_new_night_shift(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.update_night_shift(
            customer_id=data['customer_id'],
            night_shift=data['new_night_shift']
        )
        await callback.answer(
            text=txt.night_shift_updated(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.update_night_shift_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
