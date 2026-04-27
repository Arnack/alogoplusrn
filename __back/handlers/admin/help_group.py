from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import logging

from filters import Admin
import database as db
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.message(Command('set_help_group'))
async def cmd_set_help_group(
        message: Message
):
    try:
        if message.chat.id < 0:
            await db.set_help_group(
                group_chat_id=str(message.chat.id),
            )
            await message.answer(
                text=txt.help_group_set(),
            )
        else:
            await message.answer(
                text=txt.help_command_warning(),
            )
    except Exception as e:
        logging.exception(e)
        await message.answer(
            text=txt.set_help_group_error(),
        )
