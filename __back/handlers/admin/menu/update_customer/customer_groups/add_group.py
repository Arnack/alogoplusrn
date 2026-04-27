import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(F.data.startswith('NewCustomerGroup:'))
async def request_group_name(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    await state.update_data(
        CustomerID=int(
            callback.data.split(':')[1]
        )
    )
    await state.set_state('RequestGroupName')

    await callback.message.edit_text(
        text=txt.request_group_name()
    )


@router.message(F.text, StateFilter('RequestGroupName'))
async def get_customer_group_name(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_group_any_message()
    )
    await state.update_data(
        GroupName=message.text
    )
    await state.set_state('GroupChatID')


@router.message(F.text, StateFilter('GroupChatID'))
async def get_customer_group_chat_id(
        message: Message,
        state: FSMContext
):
    if message.text.replace('-', '').isdigit():
        data = await state.get_data()
        organization = await db.get_customer_organization(
            customer_id=data['CustomerID']
        )
        await message.answer(
            text=txt.confirmation_save_customer_group(
                group_name=data['GroupName'],
                organization=organization
            ),
            reply_markup=ikb.confirmation_save_customer_group(
                customer_id=data['CustomerID']
            )
        )
        await state.update_data(
            GroupChatID=message.text
        )
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(F.data == 'SaveNewCustomerGroup')
async def save_new_customer_group(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.set_customer_group(
            customer_id=data['CustomerID'],
            group_name=data['GroupName'],
            group_chat_id=data['GroupChatID']
        )
        await callback.answer(
            text=txt.new_customer_group_added(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.save_customer_group_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['CustomerID']
        )
        await state.clear()
