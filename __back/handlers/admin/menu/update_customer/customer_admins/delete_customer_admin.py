import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt


router = Router()


async def open_delete_customer_admins_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()

    await callback.message.edit_text(
        text=txt.delete_customer_representative_menu(),
        reply_markup=await ikb.delete_customer_admins(
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data.startswith('DeleteCustomerAdminsMenu:'))
async def delete_customer_admins_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)

    await open_delete_customer_admins_menu(
        callback=callback,
        state=state
    )


@router.callback_query(Admin(), F.data.startswith('DeleteCustomerAdmin:'))
async def confirmation_delete_customer_admin(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    admin_id = int(callback.data.split(':')[1])
    admin = await db.get_customer_admin_by_id(admin_id=admin_id)

    await callback.message.edit_text(
        text=txt.confirmation_delete_customer_admin(
            fio=admin.admin_full_name
        ),
        reply_markup=ikb.confirmation_delete_customer_admin(
            admin_id=admin_id,
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data.startswith('ConfirmDeleteCustomerAdmin:'))
async def delete_customer_id(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        admin_id = int(callback.data.split(':')[1])

        await db.delete_customer_admin(
            admin_id=admin_id
        )
        await callback.answer(
            text=txt.customer_admin_deleted(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.delete_customer_admin_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_delete_customer_admins_menu(
            callback=callback,
            state=state
        )
