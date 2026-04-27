from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(F.data == 'ShoutShowStat')
async def open_shout_stat_menu(
        callback: CallbackQuery
):
    foreman_shouts = await db.get_sender_shouts(
        sender_tg_id=callback.from_user.id
    )
    if foreman_shouts:
        await callback.message.edit_text(
            text=txt.shout_stat(),
            reply_markup=await ikb.shout_stat(
                foreman_shouts=foreman_shouts
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.shout_stat_none(),
            reply_markup=ikb.back_to_shout_menu()
        )


@router.callback_query(F.data.startswith('ShowShoutStat:'))
async def show_shout_stat(
        callback: CallbackQuery
):
    shout_id = int(callback.data.split(':')[1])
    shout = await db.get_shout(shout_id=shout_id)

    await callback.message.edit_text(
        text=txt.show_shout_stat(
            shout_id=shout_id,
            views=shout.views,
            workers_count=shout.workers
        ),
        reply_markup=ikb.shout_stat_back()
    )
