from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt

router = Router()


@router.callback_query(Admin(), F.data.startswith('PremiumWorkersMenu:'))
async def open_premium_workers_menu(
    callback: CallbackQuery
):
    """Открыть главное меню управления исполнителями с дополнительным вознаграждением"""
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    await callback.message.edit_text(
        text=txt.premium_workers_menu(),
        reply_markup=ikb.premium_workers_menu(customer_id=customer_id)
    )


@router.callback_query(Admin(), F.data.startswith('ShowPremiumWorkersList:'))
async def show_premium_workers_list(
    callback: CallbackQuery
):
    """Показать список всех закреплённых исполнителей"""
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])

    premium_workers = await db.get_customer_premium_workers(customer_id)

    if premium_workers:
        await callback.message.edit_text(
            text=txt.premium_workers_list(),
            reply_markup=await ikb.premium_workers_list(
                customer_id=customer_id,
                premium_workers=premium_workers
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_premium_workers(),
            reply_markup=ikb.premium_workers_back(customer_id=customer_id)
        )
