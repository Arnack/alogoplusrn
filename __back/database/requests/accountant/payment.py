from sqlalchemy import update, select
from sqlalchemy.orm import joinedload

from database import Payment, Registry, async_session


async def get_payments_by_order_id(
        order_id: int,
) -> list[Payment]:
    async with async_session() as session:
        payments = await session.scalars(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.notification_sent == False,
                Payment.amount != '0',
            ).options(
                joinedload(Payment.user)
            )
        )
        return payments.all()


async def payment_notification_sent(
        payment_id: int,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Payment).where(
                Payment.id == payment_id
            ).values(
                notification_sent=True,
            )
        )
        await session.commit()


async def set_registry(
        order_id: int,
) -> int:
    async with async_session() as session:
        new_registry = Registry(
            order_id=order_id,
        )
        session.add(new_registry)
        await session.commit()
        await session.refresh(new_registry)
        return new_registry.id


async def update_registry(
        registry_id: int,
        api_registry_id: int,
        status: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Registry).where(
                Registry.id == registry_id
            ).values(
                registry_id=api_registry_id,
                status=status,
            )
        )
        await session.commit()


async def update_registry_status_by_id(
        registry_id: int,
        status: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Registry).where(
                Registry.id == registry_id
            ).values(
                status=status,
            )
        )
        await session.commit()
