from aiogram import Router, F
from aiogram.types import CallbackQuery

from utils import schedule_delete_shout_message
from filters import Worker
import database as db

router = Router()


@router.callback_query(Worker(), F.data.startswith('ShoutFinish:'))
async def worker_shout_finish(
        callback: CallbackQuery
):
    await callback.answer()
    shout_id = int(callback.data.split(':')[1])

    await db.update_shout_views(shout_id=shout_id)

    if callback.message.photo or callback.message.video or callback.message.audio or callback.message.document:
        await callback.message.edit_caption(
            caption=callback.message.html_text[:-78:]
        )
    else:
        await callback.message.edit_text(
            text=callback.message.html_text[:-78:]
        )

    await schedule_delete_shout_message(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id
    )
