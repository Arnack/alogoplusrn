from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_supervisors_tg_id


class Supervisor(Filter):
    async def __call__(
            self, event: Union[Message, CallbackQuery]
    ) -> bool:
        workers = await get_supervisors_tg_id()
        return event.from_user.id in workers
