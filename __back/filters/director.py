from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_directors_tg_id


class Director(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        directors = await get_directors_tg_id()
        return event.from_user.id in directors
