from aiogram import Router, F
from aiogram.types import CallbackQuery

import keyboards.inline as ikb
from filters import Foreman
import database as db
import texts as txt


router = Router()


@router.callback_query(Foreman(), F.data == 'BotRules')
async def show_worker_rules(
        callback: CallbackQuery
):
    rules = await db.get_rules(
        rules_for='foremen'
    )
    if rules:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.show_rules_text(
                text=rules.rules,
                date=rules.date
            ),
            reply_markup=ikb.back_to_about_worker()
        )
    else:
        await callback.answer(
            text=txt.no_rules(),
            show_alert=True
        )
