from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_foremen_tg_id


class Foreman(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        workers = await get_foremen_tg_id()
        return event.from_user.id in workers
