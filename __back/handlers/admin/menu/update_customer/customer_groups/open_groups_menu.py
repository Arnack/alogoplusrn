from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
import texts as txt


router = Router()


@router.callback_query(F.data.startswith('CustomerGroupsMenu:'))
async def open_customer_admins_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.clear()

    await callback.message.edit_text(
        text=txt.customer_groups(),
        reply_markup=ikb.customer_groups_menu(
            customer_id=int(
                callback.data.split(':')[1]
            )
        )
    )
