from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(F.data.startswith('DeleteCustomerGroupsMenu:'))
async def delete_customer_groups_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        text=txt.delete_customer_group_menu(),
        reply_markup=await ikb.delete_customer_groups(
            customer_id=customer_id
        )
    )
    await state.update_data(
        CustomerID=customer_id
    )


@router.callback_query(F.data.startswith('DeleteCustomerGroup:'))
async def confirmation_delete_customer_group(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    group_id = int(callback.data.split(':')[1])

    group = await db.get_customer_group_by_id(
        group_id=group_id
    )

    await callback.message.edit_text(
        text=txt.confirmation_delete_customer_group(
            group_name=group.group_name
        ),
        reply_markup=ikb.confirmation_delete_customer_group(
            group_id=group_id,
            customer_id=data['CustomerID']
        )
    )


@router.callback_query(F.data.startswith('ConfirmDeleteCustomerGroup:'))
async def confirm_delete_customer_group(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        await db.delete_customer_group(
            group_id=int(
                callback.data.split(':')[1]
            )
        )
        await callback.answer(
            text=txt.customer_group_deleted(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.delete_customer_group_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        data = await state.get_data()
        await callback.message.edit_text(
            text=txt.delete_customer_group_menu(),
            reply_markup=await ikb.delete_customer_groups(
                customer_id=data['CustomerID']
            )
        )
