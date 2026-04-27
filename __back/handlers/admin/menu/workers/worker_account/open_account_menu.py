from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
from filters import Admin, Director
from aiogram.filters import or_f
import texts as txt


router = Router()


async def open_worker_account_menu(
        callback: CallbackQuery
) -> None:
    await callback.answer()
    await callback.message.edit_text(
        text=txt.worker_account_menu(),
        reply_markup=ikb.worker_account_menu()
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'WorkerAccount')
async def request_worker_info(
        callback: CallbackQuery
):
    await open_worker_account_menu(
        callback=callback
    )
