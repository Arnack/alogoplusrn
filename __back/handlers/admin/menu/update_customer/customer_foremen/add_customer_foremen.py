import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
import keyboards.reply as kb
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('NewCustomerForeman:'))
async def foreman_full_name(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)
    await state.set_state('NewForemanFullName')

    await callback.message.edit_text(
        text=txt.add_customer_foreman_full_name()
    )


@router.message(Admin(), F.text, StateFilter('NewForemanFullName'))
async def save_foreman_full_name(
        message: Message,
        state: FSMContext
):
    await state.update_data(new_foreman_full_name=message.text)
    await state.set_state('NewForemanTgID')

    await message.answer(
        text=txt.add_customer_foreman_tg_id()
    )


@router.message(Admin(), F.text, StateFilter('NewForemanTgID'))
async def save_admin_id(
        message: Message,
        state: FSMContext
):
    try:
        data = await state.get_data()
        organization = await db.get_customer_organization(customer_id=data['customer_id'])
        await state.update_data(new_foreman_tg_id=int(message.text))

        await message.answer(
            text=txt.confirmation_save_customer_foreman(
                admin_fio=data['new_foreman_full_name'],
                admin_id=message.text,
                organization=organization
            ),
            reply_markup=ikb.confirmation_save_customer_foreman(
                customer_id=data['customer_id']
            )
        )
    except ValueError:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(Admin(), F.data == 'SaveNewCustomerForeman')
async def save_new_customer_foreman(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.save_new_foreman(
            customer_id=data['customer_id'],
            foreman_full_name=data['new_foreman_full_name'],
            foreman_tg_id=data['new_foreman_tg_id']
        )
        await callback.answer(
            text=txt.new_customer_foreman_added(),
            show_alert=True
        )
        try:
            organization = await db.get_customer_organization(
                customer_id=data['customer_id']
            )
            await callback.bot.send_message(
                chat_id=data['new_foreman_tg_id'],
                text=txt.forman_notification(
                    customer=organization
                ),
                reply_markup=kb.foreman_menu()
            )
        except:
            pass
    except Exception as e:
        await callback.answer(
            text=txt.save_customer_foreman_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.clear()
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
