from aiogram import Router

from filters import Accountant

from handlers.accountant.wallet_payments import router as wallet_payments_router
from handlers.accountant.payments import router as payments_router
from handlers.accountant.accruals_payout import router as accruals_payout_router


accountant_router = Router()
accountant_router.message.filter(Accountant())
accountant_router.callback_query.filter(Accountant())


accountant_router.include_routers(
    wallet_payments_router,
    payments_router,
    accruals_payout_router,
)
