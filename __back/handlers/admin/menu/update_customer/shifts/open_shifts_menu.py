from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerShift:'))
async def update_shift(
        callback: CallbackQuery,
        state: FSMContext

):
    await callback.answer()
    await state.clear()

    customer_id = int(callback.data.split(':')[1])
    customer = await db.get_customer_info(customer_id=customer_id)

    await callback.message.edit_text(
        text=txt.update_customer_shift(),
        reply_markup=ikb.update_customer_shift(
            customer_id=customer_id,
            day_shift=customer.day_shift,
            night_shift=customer.night_shift
        )
    )
