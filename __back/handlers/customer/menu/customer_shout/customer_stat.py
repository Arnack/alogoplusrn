from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

import keyboards.inline as ikb
from filters import Customer, Admin
from aiogram.filters import or_f
import database as db
import texts as txt


router = Router()


@router.callback_query(or_f(Customer(), Admin()), F.data.startswith('ShoutShowStat:'))
async def open_shout_stat_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    await state.update_data(order_id=order_id)
    customer_admin_shouts = await db.customer_get_sender_shouts(
        sender_tg_id=callback.from_user.id,
        order_id=order_id
    )
    if customer_admin_shouts:
        await callback.message.edit_text(
            text=txt.shout_stat(),
            reply_markup=await ikb.customer_shout_stat(
                customer_admin_shouts=customer_admin_shouts,
                order_id=order_id
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.customer_shout_stat_none(),
            reply_markup=ikb.customer_back_to_shout_menu(
                order_id=order_id
            )
        )


@router.callback_query(or_f(Customer(), Admin()), F.data.startswith('ShowShoutStat:'))
async def show_shout_stat(
        callback: CallbackQuery,
        state: FSMContext
):
    shout_id = int(callback.data.split(':')[1])
    shout = await db.get_shout(shout_id=shout_id)
    data = await state.get_data()

    await callback.message.edit_text(
        text=txt.show_shout_stat(
            shout_id=shout_id,
            views=shout.views,
            workers_count=shout.workers
        ),
        reply_markup=ikb.customer_shout_stat_back(
            order_id=data['order_id']
        )
    )
