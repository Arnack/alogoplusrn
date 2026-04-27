from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from handlers.admin.menu.workers.adm_workers import open_workers_menu
from filters import Admin, Director
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('ConfirmDeleteWorker:'))
async def confirm_delete_worker(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        user_id = int(callback.data.split(':')[1])
        worker = await db.get_user_by_id(
            user_id=user_id
        )
        await db.delete_worker_by_id(
            user_id=user_id,
            tg_id=worker.tg_id
        )
        try:
            await callback.bot.send_message(
                chat_id=worker.tg_id,
                text=txt.user_deleted(),
                protect_content=True
            )
        except:
            pass
        await callback.answer(
            text=txt.worker_deleted(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.delete_worker_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await open_workers_menu(
            callback=callback
        )
