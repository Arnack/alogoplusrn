from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
from filters import Admin
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('CustomerAdminsMenu:'))
async def open_customer_admins_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.clear()

    customer_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(
        text=txt.customer_admins(),
        reply_markup=ikb.customer_admins_menu(
            customer_id=customer_id
        )
    )
