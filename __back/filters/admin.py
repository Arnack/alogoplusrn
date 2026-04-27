from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from typing import Union


from config_reader import config


class Admin(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        return event.from_user.id in config.bot_admins


class AdminOrManager(Filter):
    async def __call__(self, event: Union[Message, CallbackQuery]):
        from database import get_managers_tg_id

        # Проверяем, является ли пользователь админом
        if event.from_user.id in config.bot_admins:
            return True

        # Проверяем, является ли пользователь менеджером
        managers = await get_managers_tg_id()
        return event.from_user.id in managers


def admin_filter(
        worker_id: int
) -> bool:
    return worker_id in config.bot_admins
