from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from filters import Admin, Director
from aiogram.filters import or_f
import texts as txt


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'EraseWorkerTgID')
async def worker_account_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.update_data(
        AccountAction='EraseTgID'
    )
    await callback.message.edit_text(
        text=txt.request_last_name()
    )
    await state.set_state('RequestLastName')
