from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from utils import validate_date
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.message(Admin(), F.text == '📊 Математика')
async def request_start_date(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_start_date()
    )
    await state.set_state('GetMathStartDate')


@router.message(Admin(), F.text, StateFilter('GetMathStartDate'))
async def get_start_date(
        message: Message,
        state: FSMContext
):
    is_valid, formatted_date = validate_date(message.text)
    if is_valid:
        await state.update_data(
            MathStartDate=formatted_date
        )
        await message.answer(
            text=txt.request_end_date()
        )
        await state.set_state('GetMathEndDate')
    else:
        await message.answer(
            text=txt.date_error()
        )


@router.message(Admin(), F.text, StateFilter('GetMathEndDate'))
async def get_end_date(
        message: Message,
        state: FSMContext
):
    is_valid, formatted_date = validate_date(message.text)
    if is_valid:
        data = await state.get_data()
        start_date = datetime.strptime(
            data['MathStartDate'], "%d.%m.%Y"
        )
        end_date = datetime.strptime(
            formatted_date, "%d.%m.%Y"
        )
        if end_date > start_date:
            await state.clear()
            saving = await db.get_saving(
                start_date_str=data['MathStartDate'],
                end_date_str=formatted_date
            )
            if saving:
                await message.answer(
                    text=txt.show_saving(
                        start_date=data['MathStartDate'],
                        end_date=formatted_date,
                        data=saving
                    )
                )
            else:
                await message.answer(
                    text=txt.show_saving_error(
                        start_date=data['MathStartDate'],
                        end_date=formatted_date
                    )
                )
        else:
            await message.answer(
                text=txt.end_date_lower_than_start_date_error()
            )
    else:
        await message.answer(
            text=txt.date_error()
        )
