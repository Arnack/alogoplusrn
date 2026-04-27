from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import keyboards.inline as ikb
import texts as txt


router = Router()


@router.callback_query(F.data == 'OpenShoutMenu')
@router.message(F.text == '📣 Оповещение на объекте')
async def open_shout_menu(
        event: Message or CallbackQuery
):
    if isinstance(event, Message):
        await event.answer(
            text=txt.shout_menu(),
            reply_markup=ikb.shout_menu(),
            protect_content=True
        )
    else:
        await event.message.edit_text(
            text=txt.shout_menu(),
            reply_markup=ikb.shout_menu()
        )
