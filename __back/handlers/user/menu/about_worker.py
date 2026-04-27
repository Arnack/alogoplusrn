from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

import keyboards.inline as ikb
from utils import get_rating
from filters import Worker
import database as db
import texts as txt


router = Router()


async def show_info_about_worker(
        event: Message | CallbackQuery
) -> None:
    user = await db.get_user(tg_id=event.from_user.id)
    rating = await get_rating(user_id=user.id)
    if isinstance(event, Message):
        await event.answer(
            text=await txt.about_worker(
                user_id=user.id,
                rating=rating
            ),
            reply_markup=ikb.update_worker_info(
                api_worker_id=user.api_id,
            ),
            protect_content=True
        )
    elif isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(
            text=await txt.about_worker(
                user_id=user.id,
                rating=rating
            ),
            reply_markup=ikb.update_worker_info(
                api_worker_id=user.api_id,
            )
        )


@router.callback_query(Worker(), F.data == 'BackToAboutMe')
@router.message(Worker(), F.text == '👤 Обо мне')
async def opem_about_worker(
        event: Message | CallbackQuery
):
    await show_info_about_worker(
        event=event
    )


@router.callback_query(Worker(), F.data == 'UpdateWorkerInfo')
async def update_worker_info(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.update_worker_info(),
        reply_markup=ikb.choose_update()
    )


@router.callback_query(Worker(), F.data == 'EraseWorkerInfo')
async def erase_worker_info(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.erase_worker_info_warning(),
        reply_markup=ikb.confirmation_erase_worker_data()
    )


@router.callback_query(Worker(), F.data == 'ConfirmEraseWorkerData')
async def confirm_erase_data(
        callback: CallbackQuery
):
    await callback.answer()
    worker = await db.get_user(
        tg_id=callback.from_user.id
    )
    await db.erase_worker_data(
        user_id=worker.id
    )
    msg = await callback.message.answer(
        text='.',
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.message.edit_text(
        text=txt.worker_data_erased()
    )
    await callback.bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=msg.message_id
    )
