from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, LinkPreviewOptions
from typing import Dict, Any, Callable, Awaitable

import texts as txt
import database as db
import keyboards.inline as ikb


class CheckBlockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if await db.has_block(worker_tg_id=event.from_user.id):
            if isinstance(event, Message):
                await event.answer(text=txt.middleware_message_block(),
                                   link_preview_options=LinkPreviewOptions(is_disabled=True),
                                   reply_markup=ikb.support())
            elif isinstance(event, CallbackQuery):
                await event.answer(text=txt.middleware_callback_block(),
                                   show_alert=True)
            return
        return await handler(event, data)
