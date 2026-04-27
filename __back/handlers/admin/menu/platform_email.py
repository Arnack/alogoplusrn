from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import database as db
import texts as txt
import keyboards.inline as ikb

from filters import Admin
from utils.email.email_sender import validate_email_list


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.message(F.text == '📪 Почта')
async def open_platform_email_menu(
    message: Message,
    state: FSMContext
):
    await state.clear()

    platform_emails = await db.get_platform_emails()

    await message.answer(
        text=txt.platform_emails_menu() + '\n\n' + txt.current_platform_emails(platform_emails),
        reply_markup=ikb.platform_email_menu()
    )


@router.callback_query(F.data == 'PlatformEmailMenu')
async def platform_email_menu_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await state.clear()

    platform_emails = await db.get_platform_emails()

    await callback.message.edit_text(
        text=txt.platform_emails_menu() + '\n\n' + txt.current_platform_emails(platform_emails),
        reply_markup=ikb.platform_email_menu()
    )


@router.callback_query(F.data == 'EditPlatformEmails')
async def edit_platform_emails(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    await state.set_state('EnterPlatformEmails')

    await callback.message.answer(text=txt.enter_platform_emails())


@router.message(F.text, StateFilter('EnterPlatformEmails'))
async def save_platform_emails_input(
    message: Message,
    state: FSMContext
):
    # Валидация email адресов
    is_valid, validation_message = validate_email_list(message.text)

    if not is_valid:
        await message.answer(text=txt.email_validation_error(validation_message))
        return

    await state.update_data(platform_emails=message.text)

    await message.answer(
        text=txt.customer_email_addresses_display(message.text),
        reply_markup=ikb.confirm_platform_emails()
    )


@router.callback_query(F.data == 'SavePlatformEmails')
async def confirm_save_platform_emails(
    callback: CallbackQuery,
    state: FSMContext
):
    try:
        data = await state.get_data()
        platform_emails = data.get('platform_emails', '')

        await db.update_platform_emails(platform_emails)
        await state.clear()

        await callback.answer(
            text=txt.platform_emails_updated(),
            show_alert=True
        )

        # Возвращаемся в меню почты
        platform_emails = await db.get_platform_emails()

        await callback.message.edit_text(
            text=txt.platform_emails_menu() + '\n\n' + txt.current_platform_emails(platform_emails),
            reply_markup=ikb.platform_email_menu()
        )

    except Exception:
        await callback.answer(
            text=txt.platform_emails_update_error(),
            show_alert=True
        )


@router.callback_query(F.data == 'AdminMainMenu')
async def return_to_admin_main_menu(
    callback: CallbackQuery
):
    await callback.answer()
    await callback.message.delete()
