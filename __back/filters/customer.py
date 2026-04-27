from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union

from database import get_customers_for_filter


class Customer(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        customers = await get_customers_for_filter()
        return event.from_user.id in customers
