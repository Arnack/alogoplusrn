from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f
from datetime import datetime
import logging

from utils import (
    create_collation, is_date,
    parse_date_from_str_to_str
)
import keyboards.inline as ikb
from filters import Admin, Director
import database as db
import texts as txt


router = Router()


@router.message(or_f(Admin(), Director()), F.text == '📄 Сформировать сверку')
async def request_start_date(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_start_date()
    )
    await state.set_state('GetStartDate')


@router.message(or_f(Admin(), Director()), F.text, StateFilter('GetStartDate'))
async def get_start_date(
        message: Message,
        state: FSMContext
):
    parsed_date = parse_date_from_str_to_str(message.text)
    if parsed_date:
        await state.update_data(
            CollationStartDate=parsed_date
        )
        await message.answer(
            text=txt.request_end_date()
        )
        await state.set_state('GetEndDate')
    else:
        await message.answer(
            text=txt.date_error()
        )


@router.message(or_f(Admin(), Director()), F.text, StateFilter('GetEndDate'))
async def get_end_date(
        message: Message,
        state: FSMContext
):
    parsed_date = parse_date_from_str_to_str(message.text)
    if parsed_date:
        data = await state.get_data()
        start_date = datetime.strptime(
            data['CollationStartDate'], "%d.%m.%Y"
        )
        end_date = datetime.strptime(
            parsed_date, "%d.%m.%Y"
        )
        if end_date > start_date:
            await state.update_data(
                CollationEndDate=parsed_date
            )
            await message.answer(
                text=txt.select_customer(),
                reply_markup=await ikb.select_customer(
                    menu_page=1
                )
            )
            await state.set_state(None)
        else:
            await message.answer(
                text=txt.end_date_lower_than_start_date_error()
            )
    else:
        await message.answer(
            text=txt.date_error()
        )


@router.callback_query(or_f(Admin(), Director()), ikb.CollationCallbackData.filter(F.action == 'ForwardCollationMenu'))
async def forward_collation_menu(
        callback: CallbackQuery,
        callback_data: ikb.CollationCallbackData
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.select_customer(),
        reply_markup=await ikb.select_customer(
            menu_page=callback_data.menu_page + 1
        )
    )


@router.callback_query(or_f(Admin(), Director()), ikb.CollationCallbackData.filter(F.action == 'BackCollationMenu'))
async def back_collation_menu(
        callback: CallbackQuery,
        callback_data: ikb.CollationCallbackData
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.select_customer(),
        reply_markup=await ikb.select_customer(
            menu_page=callback_data.menu_page - 1
        )
    )


@router.callback_query(or_f(Admin(), Director()), ikb.CollationCallbackData.filter(F.action == 'SelectCustomer'))
async def create_admin_collation(
        callback: CallbackQuery,
        callback_data: ikb.CollationCallbackData,
        state: FSMContext
):
    msg = await callback.message.edit_text(
        text=txt.collation_pdf()
    )
    try:
        data = await state.get_data()
        organization = await db.get_customer_organization(
            customer_id=callback_data.customer_id
        )
        pdf_bytes = await create_collation(
            start_date_str=data['CollationStartDate'],
            end_date_str=data['CollationEndDate'],
            customer_id=callback_data.customer_id,
            customer=organization
        )
        pdf_name = f"Сверка_{organization.replace(' ', '_')}_" \
                   f"{data['CollationStartDate'].replace('.', '_')}-" \
                   f"{data['CollationEndDate'].replace('.', '_')}.pdf"
        await callback.message.answer_document(
            document=BufferedInputFile(
                file=pdf_bytes,
                filename=pdf_name
            ),
        )
        await callback.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=msg.message_id
        )
    except ValueError as ve:
        if str(ve) == "Нет данных для формирования сверки":
            await callback.bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=msg.message_id,
                text=txt.create_collation_error_no_orders()
            )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=msg.message_id,
            text=txt.create_collation_error()
        )
