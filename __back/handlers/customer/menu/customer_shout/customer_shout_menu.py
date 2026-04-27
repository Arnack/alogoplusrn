from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
from filters import Customer, Admin
from aiogram.filters import or_f
import texts as txt


router = Router()


@router.callback_query(or_f(Customer(), Admin()), F.data.startswith('OpenShoutMenu:'))
async def open_shout_menu(
        callback: CallbackQuery
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(
        text=txt.shout_menu(),
        reply_markup=ikb.customer_shout_menu(
            order_id=order_id
        )
    )
