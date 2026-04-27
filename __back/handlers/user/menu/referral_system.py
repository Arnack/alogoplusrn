from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.deep_linking import create_start_link

import keyboards.inline as ikb
from texts import referral
from filters import Worker
import database as db


router = Router()


@router.callback_query(Worker(), F.data == 'GetBonus')
async def create_ref_link(
        callback: CallbackQuery
):
    settings = await db.get_settings()
    ref_info = await db.get_referral_info(tg_id=callback.from_user.id)
    await callback.message.edit_text(
        text=referral(
            link=await create_start_link(
                callback.bot,
                f'ref_{callback.from_user.id}'
            ),
            bonus=settings.bonus,
            shifts=settings.shifts,
            friends=ref_info[0],
            completed=ref_info[1]
        ),
        reply_markup=ikb.back_to_about_worker()
    )
