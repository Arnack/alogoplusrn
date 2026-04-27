from aiogram import Router
from .menu import moderation, newsletter, applications, supervisor_orders

router = Router()
router.include_router(moderation.router)
router.include_router(newsletter.router)
router.include_router(applications.router)
router.include_router(supervisor_orders.router)
