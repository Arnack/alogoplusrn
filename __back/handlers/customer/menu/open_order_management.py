from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import texts as txt
import keyboards.inline as ikb
from filters import Customer


router = Router()


@router.callback_query(Customer(), F.data.in_({'CancelAddOrder', 'OrderCancel'}))
@router.message(Customer(), F.text == '⚙️ Управление заявками')
async def order_management(
        event: Message | CallbackQuery
):
    if isinstance(event, Message):
        await event.answer(
            text=txt.orders(),
            reply_markup=ikb.order_management()
        )
    else:
        await event.message.edit_text(
            text=txt.orders(),
            reply_markup=ikb.order_management()
        )
