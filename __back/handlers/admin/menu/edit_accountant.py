from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from filters import Admin
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.in_({'AccountantAddCancel', 'AccountantsMenu'}))
@router.message(Admin(), F.text == '💳 Кассиры')
async def accountants_main_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    await state.clear()
    if isinstance(event, Message):
        await event.answer(
            text=txt.accountants(),
            reply_markup=ikb.accountants_menu()
        )
    else:
        await event.answer()
        await event.message.edit_text(
            text=txt.accountants(),
            reply_markup=ikb.accountants_menu()
        )


@router.callback_query(Admin(), F.data == 'AllAccountants')
async def show_accountants_list(
        callback: CallbackQuery
):
    await callback.answer()
    all_accountants = await db.get_accountants()

    if all_accountants:
        await callback.message.edit_text(
            text=txt.accountants_list(),
            reply_markup=ikb.accountants_list(
                accountants=all_accountants
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_accountants(),
            reply_markup=ikb.accountants_back()
        )


@router.callback_query(Admin(), F.data.startswith('Accountant:'))
async def accountant_info(
        callback: CallbackQuery
):
    await callback.answer()
    accountant_id = int(callback.data.split(':')[1])
    accountant = await db.get_accountant(
        accountant_id=accountant_id
    )

    await callback.message.edit_text(
        text=txt.accountant_info(
            full_name=accountant.full_name,
            tg_id=accountant.tg_id
        ),
        reply_markup=ikb.delete_accountant(
            accountant_id=accountant_id
        )
    )


@router.callback_query(Admin(), F.data == 'AddAccountant')
async def add_accountant(
        callback: CallbackQuery, state: FSMContext
):
    await callback.message.edit_text(
        text=txt.request_accountant_full_name()
    )
    await state.set_state("AccountantFullName")


@router.message(Admin(), F.text, StateFilter("AccountantFullName"))
async def get_accountant_full_name(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_accountant_tg_id()
    )
    await state.update_data(
        AccountantFullName=message.text
    )
    await state.set_state("AccountantTgID")


@router.message(Admin(), F.text, StateFilter("AccountantTgID"))
async def get_accountant_tg_id(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        await state.set_state(None)
        data = await state.get_data()
        await message.answer(
            text=txt.confirmation_add_new_accountant(
                tg_id=message.text,
                full_name=data['AccountantFullName']
            ),
            reply_markup=ikb.confirmation_add_new_accountant()
        )
        await state.update_data(
            AccountantTgID=int(message.text)
        )
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(Admin(), F.data == 'SaveAccountant')
async def save_accountant(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.set_accountant(
            full_name=data['AccountantFullName'],
            tg_id=data['AccountantTgID']
        )
        await callback.answer(
            text=txt.accountant_added(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(
            f'\n\n{e}'
        )
        await callback.answer(
            text=txt.add_accountant_error(),
            show_alert=True
        )
    finally:
        await callback.message.edit_text(
            text=txt.accountants(),
            reply_markup=ikb.accountants_menu()
        )
        await state.clear()


@router.callback_query(Admin(), F.data.startswith('DeleteAccountant:'))
async def confirmation_delete_accountant(
        callback: CallbackQuery
):
    await callback.message.edit_text(
        text=txt.confirmation_delete_accountant(),
        reply_markup=ikb.confirmation_delete_accountant(
            accountant_id=int(callback.data.split(':')[1])
        )
    )


@router.callback_query(Admin(), F.data.startswith('ConfirmDeleteAccountant:'))
async def confirm_delete_accountant(
        callback: CallbackQuery
):
    await db.delete_accountant(
        accountant_id=int(callback.data.split(':')[1])
    )
    all_accountants = await db.get_accountants()
    await callback.answer(
        text=txt.accountant_deleted(),
        show_alert=True
    )

    if all_accountants:
        await callback.message.edit_text(
            text=txt.accountants_list(),
            reply_markup=ikb.accountants_list(
                accountants=all_accountants
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_accountants(),
            reply_markup=ikb.accountants_back()
        )
