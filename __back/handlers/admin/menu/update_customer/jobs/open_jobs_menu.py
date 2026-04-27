from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
from filters import Admin
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('OpenJobsMenu:'))
async def jobs_menu(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.customer_jobs_menu(),
        reply_markup=ikb.customer_jobs_menu(
            customer_id=int(callback.data.split(':')[1])
        )
    )
