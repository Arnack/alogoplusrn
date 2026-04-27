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


@router.callback_query(Admin(), F.data.startswith('NewCustomerAdmin:'))
async def admin_fio(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)
    await state.set_state('NewAdminFio')

    await callback.message.edit_text(
        text=txt.add_customer_admin_fio()
    )


@router.message(Admin(), F.text, StateFilter('NewAdminFio'))
async def save_admin_fio(
        message: Message,
        state: FSMContext
):
    await state.update_data(new_admin_fio=message.text)
    await state.set_state('NewAdminID')

    await message.answer(
        text=txt.add_customer_admin_tg_id()
    )


@router.message(Admin(), F.text, StateFilter('NewAdminID'))
async def save_admin_id(
        message: Message,
        state: FSMContext
):
    try:
        data = await state.get_data()
        organization = await db.get_customer_organization(customer_id=data['customer_id'])
        await state.update_data(new_admin_id=int(message.text))

        await message.answer(
            text=txt.confirmation_save_customer_admin(
                admin_fio=data['new_admin_fio'],
                admin_id=message.text,
                organization=organization
            ),
            reply_markup=ikb.confirmation_save_customer_admin(
                customer_id=data['customer_id']
            )
        )
    except ValueError:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(Admin(), F.data == 'SaveNewCustomerAdmin')
async def save_new_customer_admin(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.save_new_admin(
            customer_id=data['customer_id'],
            admin_full_name=data['new_admin_fio'],
            admin_tg_id=data['new_admin_id']
        )
        await callback.answer(
            text=txt.new_customer_admin_added(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.save_customer_admin_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
        await state.clear()
