import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt

router = Router()


@router.callback_query(Admin(), F.data.startswith('DeletePremiumWorkersMenu:'))
async def open_delete_menu(
    callback: CallbackQuery
):
    """Открыть меню открепления исполнителей"""
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    premium_workers = await db.get_customer_premium_workers(customer_id)

    if not premium_workers:
        await callback.message.edit_text(
            text=txt.no_premium_workers(),
            reply_markup=ikb.premium_workers_back(customer_id=customer_id)
        )
        return

    await callback.message.edit_text(
        text=txt.select_premium_worker_to_delete(),
        reply_markup=await ikb.delete_premium_workers_list(
            customer_id=customer_id,
            premium_workers=premium_workers
        )
    )


@router.callback_query(Admin(), F.data.startswith('DeletePremiumWorker:'))
async def confirm_delete_premium_worker(
    callback: CallbackQuery
):
    """Подтвердить открепление исполнителя"""
    await callback.answer()
    premium_worker_id = int(callback.data.split(':')[1])

    premium_worker = await db.get_premium_worker_by_id(premium_worker_id)

    await callback.message.edit_text(
        text=txt.confirm_delete_premium_worker(),
        reply_markup=ikb.confirm_delete_premium_worker(
            premium_worker_id=premium_worker_id,
            customer_id=premium_worker.customer_id
        )
    )


@router.callback_query(Admin(), F.data.startswith('ConfirmDeletePremiumWorker:'))
async def delete_premium_worker(
    callback: CallbackQuery
):
    """Открепить исполнителя"""
    try:
        data_parts = callback.data.split(':')
        premium_worker_id = int(data_parts[1])
        customer_id = int(data_parts[2])

        await db.delete_premium_worker(premium_worker_id)

        await callback.answer(
            text=txt.premium_worker_deleted(),
            show_alert=True
        )

        await open_customer_info(
            callback=callback,
            customer_id=customer_id
        )
    except Exception as e:
        await callback.answer(
            text=txt.premium_worker_delete_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
