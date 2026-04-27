from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_managers_tg_id


class Manager(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        managers = await get_managers_tg_id()
        return event.from_user.id in managers
