from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
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


@router.callback_query(F.data.startswith('CustomerEmailManagement:'))
async def open_customer_email_management(
    callback: CallbackQuery
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    customer = await db.get_customer_info(customer_id=customer_id)
    email_addresses, email_sending_enabled = await db.get_customer_email_settings(customer_id)

    await callback.message.edit_text(
        text=txt.customer_email_management_info(
            organization=customer.organization,
            email_addresses=email_addresses,
            email_sending_enabled=email_sending_enabled
        ),
        reply_markup=ikb.customer_email_management_menu(customer_id)
    )


@router.callback_query(F.data.startswith('EditCustomerEmails:'))
async def edit_customer_emails(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await state.update_data(customer_id=customer_id)
    await state.set_state('EnterCustomerEmails')

    await callback.message.answer(text=txt.enter_customer_emails())


@router.message(F.text, F.func(lambda m: m.text.lower() != 'отмена'), StateFilter('EnterCustomerEmails'))
async def save_customer_emails_input(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()
    customer_id = data['customer_id']

    # Валидация email адресов
    is_valid, validation_message = validate_email_list(message.text)

    if not is_valid:
        await message.answer(text=txt.email_validation_error(validation_message))
        return

    await state.update_data(email_addresses=message.text)

    customer = await db.get_customer_info(customer_id=customer_id)

    await message.answer(
        text=txt.customer_email_addresses_display(message.text),
        reply_markup=ikb.confirm_save_customer_emails(customer_id)
    )


@router.callback_query(F.data.startswith('SaveCustomerEmails:'))
async def confirm_save_customer_emails(
    callback: CallbackQuery,
    state: FSMContext
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    data = await state.get_data()
    email_addresses = data.get('email_addresses', '')

    await db.update_customer_email_addresses(customer_id, email_addresses)
    await state.clear()

    await callback.message.edit_text(
        text=txt.customer_emails_saved()
    )

    # Возвращаемся к карточке заказчика
    await open_customer_card(callback, customer_id)


@router.callback_query(F.data.startswith('EnableEmailSending:'))
async def enable_email_sending(
    callback: CallbackQuery
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await db.toggle_customer_email_sending(customer_id, True)

    await callback.answer(
        text=txt.customer_email_sending_enabled(),
        show_alert=True
    )

    await open_customer_card(callback, customer_id)


@router.callback_query(F.data.startswith('DisableEmailSending:'))
async def disable_email_sending(
    callback: CallbackQuery
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await db.toggle_customer_email_sending(customer_id, False)

    await callback.answer(
        text=txt.customer_email_sending_disabled(),
        show_alert=True
    )

    await open_customer_card(callback, customer_id)


async def open_customer_card(callback: CallbackQuery, customer_id: int):
    """Вспомогательная функция для открытия карточки заказчика"""
    from utils import check_auto_order_builder

    customer = await db.get_customer_full_info(customer_id=customer_id)
    auto_build = await check_auto_order_builder(customer_id=customer_id)
    _, email_sending_enabled = await db.get_customer_email_settings(customer_id)

    await callback.message.edit_text(
        text=txt.customer_info(
            organization=customer[0].organization,
            admins=customer[3],
            foremen=customer[4],
            customer_cities=customer[1],
            jobs=customer[2],
            customer_day_shift=customer[0].day_shift,
            customer_night_shift=customer[0].night_shift
        ),
        reply_markup=ikb.customer_edit_menu(
            customer_id=customer_id,
            auto_order_builder=auto_build,
            email_sending_enabled=email_sending_enabled
        )
    )
