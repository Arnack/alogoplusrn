from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from handlers.user.menu.about_worker import show_info_about_worker
import keyboards.inline as ikb
import keyboards.reply as kb
from filters import Worker
import database as db
import texts as txt


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())


@router.callback_query(F.data == 'UpdateDataForSecurity')
async def registration_for_security(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.answer(
        text=txt.phone_for_security(),
        reply_markup=kb.request_phone_number(),
        link_preview_options=LinkPreviewOptions(
            is_disabled=True
        )
    )
    await callback.message.delete()
    await state.set_state("UpdateRealPhoneNumber")


@router.message(F.contact, StateFilter('UpdateRealPhoneNumber'))
async def update_real_phone_number(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        NewRealPhoneNumber=message.contact.phone_number
    )
    await message.answer(
        text=txt.last_name_for_security(),
        reply_markup=ReplyKeyboardRemove(),
        protect_content=True
    )
    await state.set_state("UpdateRealLastName")


@router.message(F.text, StateFilter('UpdateRealLastName'))
async def update_real_last_name(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        NewRealLastName=message.text.capitalize()
    )
    await message.answer(
        text=txt.first_name_for_security(),
        protect_content=True
    )
    await state.set_state("UpdateRealFirstName")


@router.message(F.text, StateFilter('UpdateRealFirstName'))
async def update_real_first_name(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        NewRealFirstName=message.text.capitalize()
    )
    await message.answer(
        text=txt.middle_name_for_security(),
        protect_content=True
    )
    await state.set_state("UpdateRealMiddleName")


@router.message(F.text, StateFilter('UpdateRealMiddleName'))
async def update_real_middle_name(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        NewRealMiddleName=message.text.capitalize()
    )
    data = await state.get_data()

    await message.answer(
        text=txt.confirmation_save_new_data_for_security(
            phone_number=data['NewRealPhoneNumber'],
            last_name=data['NewRealLastName'],
            first_name=data['NewRealFirstName'],
            middle_name=data['NewRealMiddleName']
        ),
        reply_markup=ikb.confirmation_update_data_for_security(),
        protect_content=True
    )


@router.callback_query(F.data == 'SaveNewDataForSecurity')
async def update_data_for_security(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        data = await state.get_data()
        await db.update_data_for_security(
            tg_id=callback.from_user.id,
            phone_number=data['NewRealPhoneNumber'],
            first_name=data['NewRealFirstName'],
            last_name=data['NewRealLastName'],
            middle_name=data['NewRealMiddleName']
        )
        await callback.answer(
            text=txt.data_for_security_updated(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.update_data_for_security_error(),
            show_alert=True
        )
    finally:
        await state.set_state(None)
        await show_info_about_worker(
            event=callback
        )
