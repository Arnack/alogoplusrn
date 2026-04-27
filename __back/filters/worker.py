from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_workers_tg_id


class Worker(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        workers = await get_workers_tg_id()
        return event.from_user.id in workers
