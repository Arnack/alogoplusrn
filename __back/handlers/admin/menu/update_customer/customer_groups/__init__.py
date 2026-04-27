from aiogram import Router

from filters import Admin

from . import (
    open_groups_menu,
    add_group,
    delete_group
)


groups_router = Router()
groups_router.message.filter(Admin())
groups_router.callback_query.filter(Admin())


groups_router.include_routers(
    open_groups_menu.router,
    add_group.router,
    delete_group.router
)


__all__ = [
    'groups_router'
]
