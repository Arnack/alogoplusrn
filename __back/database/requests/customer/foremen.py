from database import User, CustomerForeman, OrderWorker, Customer, Order, ShoutStat, DataForSecurity, async_session
from sqlalchemy import select, join, update
from typing import List


async def get_customer_foremen(customer_id):
    async with async_session() as session:
        foremen = await session.scalars(select(CustomerForeman).where(CustomerForeman.customer_id == customer_id))
        return foremen.all()


async def get_foremen_tg_id():
    async with async_session() as session:
        foremen = await session.scalars(
            select(
                CustomerForeman.tg_id
            )
        )
        return foremen.all()


async def get_foreman_by_id(foreman_id):
    async with async_session() as session:
        return await session.scalar(
            select(CustomerForeman).where(
                CustomerForeman.id == foreman_id
            )
        )


async def get_foremen_by_customer_id(
        customer_id: int
) -> List[CustomerForeman]:
    async with async_session() as session:
        foremen = await session.scalars(
            select(CustomerForeman).where(
                CustomerForeman.customer_id == customer_id
            )
        )
        return foremen.all()


async def get_foreman_by_tg_id(
        foreman_tg_id: int
) -> CustomerForeman:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerForeman).where(
                CustomerForeman.tg_id == foreman_tg_id
            )
        )


async def get_foreman_by_max_id(
        foreman_max_id: int
) -> CustomerForeman:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerForeman).where(
                CustomerForeman.max_id == foreman_max_id
            )
        )


async def get_sender_shouts(
        sender_tg_id: int
) -> List[ShoutStat]:
    async with async_session() as session:
        shouts = await session.scalars(
            select(ShoutStat).where(
                ShoutStat.sender_tg_id == sender_tg_id
            )
        )
        return shouts.all()


async def customer_get_sender_shouts(
        sender_tg_id: int,
        order_id: int
) -> List[ShoutStat]:
    async with async_session() as session:
        shouts = await session.scalars(
            select(ShoutStat).where(
                ShoutStat.sender_tg_id == sender_tg_id,
                ShoutStat.order_id == order_id
            )
        )
        return shouts.all()


async def get_shout(shout_id):
    async with async_session() as session:
        return await session.scalar(select(ShoutStat).where(ShoutStat.id == shout_id))


async def get_foreman_shout_order(customer_id: int) -> Order | None:
    """Активная заявка заказчика в работе, на которой больше одного исполнителя (как для оповещения бригады)."""
    async with async_session() as session:
        orders = await session.scalars(
            select(Order).where(
                Order.customer_id == customer_id,
                Order.in_progress == True,
                Order.moderation == False,
            ).order_by(Order.id.desc())
        )
        order_list = orders.all()
    for order in order_list:
        workers = await get_workers_from_order_workers(order_id=order.id)
        if len(workers) > 1:
            return order
    return None


async def check_foreman_order_progress(
        customer_id: int,
        order_id: int
) -> Order:
    async with async_session() as session:
        return await session.scalar(
            select(Order).select_from(join(Customer, Order)).where(
                Customer.id == customer_id,
                Order.id == order_id
            )
        )


async def check_foreman_order_applications(
        customer_id: int,
        order_id: int
) -> Order:
    async with async_session() as session:
        return await session.scalar(
            select(Order).select_from(join(Customer, Order)).where(
                Customer.id == customer_id,
                Order.id == order_id
            )
        )


async def workers_for_shout(order_id) -> List[int]:
    """Возвращает список tg_id работников (для совместимости с Telegram версией)"""
    async with async_session() as session:
        workers = []
        workers_uid = await session.scalars(
                select(DataForSecurity.user_id).select_from(join(DataForSecurity, OrderWorker)).where(
                    OrderWorker.order_id == order_id
                )
            )
        for worker in workers_uid:
            workers.append(
                await session.scalar(
                    select(User.tg_id).where(
                        User.id == worker
                    )
                )
            )
        return workers


async def get_workers_for_shout(order_id) -> List[User]:
    """Возвращает полные объекты User для отправки в оба мессенджера"""
    async with async_session() as session:
        workers = await session.scalars(
            select(User).select_from(
                join(OrderWorker, User, OrderWorker.worker_id == User.id)
            ).where(
                OrderWorker.order_id == order_id
            )
        )
        return workers.all()


async def set_shout_stat(
        sender_tg_id: int,
        order_id: int
) -> int:
    async with async_session() as session:
        shout = ShoutStat(
            sender_tg_id=sender_tg_id,
            order_id=order_id
        )
        session.add(shout)
        await session.commit()
        await session.refresh(shout)
        return shout.id


async def update_shout_workers(shout_id, workers_count):
    async with async_session() as session:
        await session.execute(
            update(ShoutStat).where(
                ShoutStat.id == shout_id
            ).values(
                workers=workers_count
            )
        )
        await session.commit()


async def update_shout_views(shout_id):
    async with async_session() as session:
        views = await session.scalar(
            select(ShoutStat.views).where(
                ShoutStat.id == shout_id
            )
        )
        await session.execute(
            update(ShoutStat).where(
                ShoutStat.id == shout_id
            ).values(
                views=views + 1
            )
        )
        await session.commit()


async def get_workers_from_order_workers(order_id):
    async with async_session() as session:
        workers = await session.scalars(
            select(DataForSecurity).select_from(
                join(OrderWorker, DataForSecurity)
            ).where(
                OrderWorker.order_id == order_id
            )
        )
        return workers.all()
