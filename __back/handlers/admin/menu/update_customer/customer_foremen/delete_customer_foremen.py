import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
import keyboards.reply as kb
from filters import Admin
import database as db
import texts as txt


router = Router()


async def open_delete_customer_foremen_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()

    await callback.message.edit_text(
        text=txt.delete_customer_representative_menu(),
        reply_markup=await ikb.delete_customer_foremen(
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data.startswith('DeleteCustomerForemenMenu:'))
async def delete_customer_foremen_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)

    await open_delete_customer_foremen_menu(
        callback=callback,
        state=state
    )


@router.callback_query(Admin(), F.data.startswith('DeleteCustomerForeman:'))
async def confirmation_delete_customer_foreman(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    foreman_id = int(callback.data.split(':')[1])
    foreman = await db.get_foreman_by_id(foreman_id=foreman_id)

    await callback.message.edit_text(
        text=txt.confirmation_delete_customer_foreman(
            full_name=foreman.full_name
        ),
        reply_markup=ikb.confirmation_delete_customer_foreman(
            foreman_id=foreman_id,
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data.startswith('ConfirmDeleteCustomerForeman:'))
async def delete_customer_foreman(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        foreman_id = int(callback.data.split(':')[1])
        foreman = await db.get_foreman_by_id(foreman_id=foreman_id)

        await db.delete_foreman(
            foreman_id=foreman_id
        )
        await callback.answer(
            text=txt.customer_foreman_deleted(),
            show_alert=True
        )
        try:
            data = await state.get_data()
            organization = await db.get_customer_organization(
                customer_id=data['customer_id']
            )
            await callback.bot.send_message(
                chat_id=foreman.tg_id,
                text=txt.forman_delete_notification(
                    customer=organization
                ),
                reply_markup=kb.user_menu()
            )
        except:
            pass
    except Exception as e:
        await callback.answer(
            text=txt.delete_customer_foreman_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_delete_customer_foremen_menu(
            callback=callback,
            state=state
        )
