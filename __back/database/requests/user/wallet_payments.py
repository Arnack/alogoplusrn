from sqlalchemy.orm import joinedload
from sqlalchemy import select, update
from datetime import datetime
from decimal import Decimal
import logging

from database import User, DataForSecurity, WalletPayment, async_session


async def set_wallet_payment(
        tg_id: int,
        amount: str,
) -> int | None:
    async with async_session() as session:
        try:
            worker: User = await session.scalar(
                select(User).where(
                    User.tg_id == tg_id,
                ).options(
                    joinedload(User.security)
                )
            )

            wallet_payment: WalletPayment = WalletPayment(
                worker_id=worker.security.id,
                amount=amount,
                date=datetime.strftime(datetime.now(), '%d.%m.%Y'),
            )
            session.add(wallet_payment)

            await session.commit()
            await session.refresh(wallet_payment)
            return wallet_payment.id
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            return None


async def get_wallet_payment(
    wp_id: int,
) -> WalletPayment:
    async with async_session() as session:
        return await session.scalar(
            select(WalletPayment).options(
                joinedload(WalletPayment.worker)
            ).where(
                WalletPayment.id == wp_id,
            )
        )


async def get_wallet_payments(
        date: str,
) -> list[WalletPayment]:
    async with async_session() as session:
        wallet_payments = await session.scalars(
            select(WalletPayment).options(
                joinedload(WalletPayment.worker)
            ).where(
                WalletPayment.date == date,
                WalletPayment.paid == False,
                WalletPayment.status == "MODERATION",
            )
        )
        return wallet_payments.all()


async def get_wallet_payments_for_receipts(
        date: str,
) -> list[WalletPayment]:
    async with async_session() as session:
        wallet_payments = await session.scalars(
            select(WalletPayment).options(
                joinedload(WalletPayment.worker)
            ).where(
                WalletPayment.date == date,
                WalletPayment.paid == False,
                WalletPayment.status.notin_(('REFUSED',)),
            )
        )
        return wallet_payments.all()


async def update_wallet_payment_status(
        wp_id: int,
        status: str,
) -> None:
    async with async_session() as session:
        try:
            wallet_payment: WalletPayment = await session.scalar(
                select(WalletPayment).where(
                    WalletPayment.id == wp_id,
                )
            )
            wallet_payment.status = status

            if status == "ERROR":
                worker_security: DataForSecurity = await session.scalar(
                    select(DataForSecurity).where(DataForSecurity.id == wallet_payment.worker_id)
                )
                user: User = None
                if worker_security:
                    user = await session.scalar(
                        select(User).where(User.id == worker_security.user_id)
                    )
                if user and not wallet_payment.refund:
                    user.balance = str(Decimal(user.balance) + Decimal(wallet_payment.amount))
                    wallet_payment.refund = True

            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.exception(f'\n\n{e}')


async def update_wallet_payment(
        wp_id: int,
        api_registry_id: int,
        status: str,
) -> None:
    async with async_session() as session:
        try:
            await session.execute(
                update(WalletPayment).where(
                    WalletPayment.id == wp_id,
                ).values(
                    api_registry_id=api_registry_id,
                    status=status,
                )
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.exception(f'\n\n{e}')


async def set_wallet_payment_paid_true(
        wp_id: int,
) -> None:
    async with async_session() as session:
        try:
            await session.execute(
                update(WalletPayment).where(
                    WalletPayment.id == wp_id,
                ).values(
                    paid=True,
                )
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.exception(f'\n\n{e}')
