from database import User, OrderWorker, async_session
from sqlalchemy import select, update, delete
from typing import List


async def set_block(worker_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == worker_id).values(block=True))
        await session.commit()


async def get_blocked_workers() -> List[int]:
    async with async_session() as session:
        blocked_workers = await session.scalars(
            select(User.id).where(
                User.block == True
            )
        )
        return blocked_workers.all()


async def unblock_user(worker_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == worker_id).values(block=False))
        await session.commit()


async def block_user(worker_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == worker_id).values(block=True))
        await session.commit()


async def has_block(worker_tg_id):
    async with async_session() as session:
        return await session.scalar(select(User.block).where(User.tg_id == worker_tg_id))


async def update_rejections(worker_id):
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(
                User.id == worker_id
            )
        )
        user.rejections += 1
        await session.commit()


async def delete_order_worker_by_id(
        worker_app_id: int
):
    async with async_session() as session:
        await session.execute(
            delete(OrderWorker).where(
                OrderWorker.id == worker_app_id
            )
        )
        await session.commit()
