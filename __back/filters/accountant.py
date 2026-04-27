from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_accountants_tg_id


class Accountant(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        accountants = await get_accountants_tg_id()
        return event.from_user.id in accountants
