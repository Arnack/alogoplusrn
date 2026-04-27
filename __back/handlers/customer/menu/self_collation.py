from aiogram import Router, F
from aiogram.types import InputMediaDocument, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from utils import (
    self_collation_difference_is_more_than_31_days,
    create_collation,
    validate_date
)
from filters import Customer
import database as db
import texts as txt


router = Router()
router.message.filter(Customer())
router.callback_query.filter(Customer())


@router.message(F.text == 'Самосверка')
async def request_start_date(
    message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_self_collation_start_date()
    )
    await state.set_state('RequestStartDate')


@router.message(F.text, StateFilter('RequestStartDate'))
async def request_end_date(
    message: Message,
    state: FSMContext
):
    is_valid, formatted_date = validate_date(
        date_str=message.text
    )
    if is_valid:
        await message.answer(
            text=txt.request_self_collation_end_date()
        )
        await state.set_state('RequestEndDate')
        await state.update_data(
            self_collation_start=formatted_date
        )
    else:
        await message.answer(
            text=txt.self_collation_date_error()
        )


@router.message(F.text, StateFilter('RequestEndDate'))
async def create_self_collation(
    message: Message,
    state: FSMContext
):
    is_valid, formatted_date = validate_date(
        date_str=message.text
    )
    if is_valid:
        data = await state.get_data()
        start_date = datetime.strptime(
            data['self_collation_start'], "%d.%m.%Y"
        )
        end_date = datetime.strptime(
            formatted_date, "%d.%m.%Y"
        )
        if end_date > start_date:
            if self_collation_difference_is_more_than_31_days(
                start_date=data['self_collation_start'],
                end_date=formatted_date,
            ):
                await message.answer(
                    text=txt.difference_is_more_than_31_days_error()
                )
            else:
                await state.set_state(None)
                msg = await message.answer(
                    text=txt.self_collation_wait()
                )
                customer_admin = await db.get_customer_admin(
                    admin_tg_id=message.from_user.id
                )
                organization = await db.get_customer_organization(
                    customer_id=customer_admin.customer_id
                )

                pdf_bytes = await create_collation(
                    start_date_str=data['self_collation_start'],
                    end_date_str=formatted_date,
                    customer_id=customer_admin.customer_id,
                    customer=organization
                )
                pdf_name = f"Сверка_{organization.replace(' ', '_')}_" \
                           f"{data['self_collation_start'].replace('.', '_')}-" \
                           f"{formatted_date.replace('.', '_')}.pdf"

                await message.answer_document(
                    document=BufferedInputFile(
                        file=pdf_bytes,
                        filename=pdf_name
                    )
                )
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=msg.message_id
                )
        else:
            await message.answer(
                text=txt.self_collation_end_date_lower_than_start_date_error()
            )
    else:
        await message.answer(
            text=txt.self_collation_date_error()
        )
