import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import NoReturn

from handlers.admin.menu.workers.adm_workers import open_workers_menu
from filters import Admin, Director
from aiogram.filters import or_f
import texts as txt
import database as db
import keyboards.inline as ikb


router = Router()


async def open_blocked_workers_menu(
        callback: CallbackQuery,
        state: FSMContext
) -> NoReturn:
    blocked_workers = await db.get_blocked_workers()
    if blocked_workers:
        data = await state.get_data()
        try:
            page = data['BlockedWorkersPage']
            items = data['BlockedWorkersItems']
        except KeyError:
            page = 1
            items = 5
            await state.update_data(
                BlockedWorkersPage=1,
                BlockedWorkersItems=5
            )
        await callback.message.edit_text(
            text=txt.blocked_workers_info(),
            reply_markup=await ikb.blocked_workers_info(
                items=items,
                page=page,
                blocked_workers=blocked_workers
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_blocked_workers(),
            reply_markup=ikb.back_to_adm_workers_menu()
        )


@router.callback_query(or_f(Admin(), Director()), F.data == 'UnblockUser')
async def blocked_workers_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.update_data(
        BlockedWorkersPage=1,
        BlockedWorkersItems=5
    )
    await open_blocked_workers_menu(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'ForwardBlockedWorkers')
async def forward_blocked_workers(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    await state.update_data(
        BlockedWorkersPage=data['BlockedWorkersPage'] + 1,
        BlockedWorkersItems=data['BlockedWorkersItems'] + 5
    )
    await open_blocked_workers_menu(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Admin(), Director()), F.data == 'BackBlockedWorkers')
async def back_blocked_workers(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    await state.update_data(
        BlockedWorkersPage=data['BlockedWorkersPage'] - 1,
        BlockedWorkersItems=data['BlockedWorkersItems'] - 5
    )
    await open_blocked_workers_menu(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('ConfirmationUnblockWorker:'))
async def confirmation_unblock_worker(
        callback: CallbackQuery
):
    worker_id = int(callback.data.split(':')[1])
    worker_real_data = await db.get_user_real_data_by_id(
        user_id=worker_id
    )
    await callback.message.edit_text(
        text=txt.confirmation_unblock_user(
            last_name=worker_real_data.last_name,
            first_name=worker_real_data.first_name,
            middle_name=worker_real_data.middle_name
        ),
        reply_markup=ikb.confirmation_unblock_worker(
            worker_id=worker_id
        )
    )


@router.callback_query(or_f(Admin(), Director()), F.data.startswith('UnblockWorker:'))
async def confirm_unblock(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        worker_id = int(callback.data.split(':')[1])
        worker = await db.get_user_by_id(user_id=worker_id)

        await db.unblock_user(worker_id=worker_id)
        await callback.answer(
            text=txt.worker_unblocked(),
            show_alert=True
        )
        try:
            await callback.bot.send_message(
                chat_id=worker.tg_id,
                text=txt.user_unblocked(),
                protect_content=True
            )
        except:
            pass
    except Exception as e:
        await callback.answer(
            text=txt.unblock_worker_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.clear()
        await open_workers_menu(
            callback=callback
        )
