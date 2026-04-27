from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
from filters import Admin
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCitiesCustomerMenu:'))
async def open_city_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.clear()

    customer_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(
        text=txt.customer_cities(),
        reply_markup=ikb.update_customer_city(
            customer_id=customer_id
        )
    )
