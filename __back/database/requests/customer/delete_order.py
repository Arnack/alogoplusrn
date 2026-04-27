from database import User, OrderApplication, OrderWorker, Order, async_session
from sqlalchemy import select, delete


async def delete_order_customer(order_id):
    async with async_session() as session:
        await session.execute(delete(OrderApplication).where(OrderApplication.order_id == order_id))
        await session.execute(delete(OrderWorker).where(OrderWorker.order_id == order_id))
        await session.execute(delete(Order).where(Order.id == order_id))
        await session.commit()


async def all_users_for_delete_order(order_id):
    async with async_session() as session:
        users = []
        applications = await session.scalars(select(OrderApplication.worker_id).where(
            OrderApplication.order_id == order_id)
        )
        workers = await session.scalars(select(OrderWorker.worker_id).where(
            OrderWorker.order_id == order_id)
        )
        for worker_id in applications:
            users.append(await session.scalar(select(User.tg_id).where(User.id == worker_id)))
        for worker_id in workers:
            users.append(await session.scalar(select(User.tg_id).where(User.id == worker_id)))
        return users
