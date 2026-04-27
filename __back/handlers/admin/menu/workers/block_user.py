import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.admin.menu.workers.adm_workers import open_workers_menu
from filters import Admin, Director
from aiogram.filters import or_f
import texts as txt
import database as db


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data == 'BlockUser')
async def request_worker_full_name(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.update_data(
        AccountAction='BlockUser'
    )
    await callback.message.edit_text(
        text=txt.request_last_name()
    )
    await state.set_state('RequestLastName')


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('BlockWorker:'))
async def block_worker(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        worker_id = int(callback.data.split(':')[1])
        worker = await db.get_user_by_id(user_id=worker_id)

        await db.block_user(worker_id=worker_id)
        await callback.answer(
            text=txt.worker_blocked(),
            show_alert=True
        )
        try:
            await callback.bot.send_message(
                chat_id=worker.tg_id,
                text=txt.user_blocked(),
                protect_content=True
            )
        except:
            pass
    except Exception as e:
        await callback.answer(
            text=txt.block_worker_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.clear()
        await open_workers_menu(
            callback=callback
        )
