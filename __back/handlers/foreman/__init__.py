from aiogram import Router

from filters import Foreman

from .shout import *
from . import (
    applications,
    rules_for_foreman
)


foreman_router = Router()
foreman_router.message.filter(Foreman())
foreman_router.callback_query.filter(Foreman())


foreman_router.include_routers(
    shout_menu.router,
    send_message.router,
    applications.router,
    stat.router,
    rules_for_foreman.router
)


__all__ = [
    'foreman_router'
]
