from database import User, CustomerForeman, OrderApplication, ShoutStat, OrderWorker, async_session
from sqlalchemy import delete, update


async def delete_worker_by_id(
        user_id: int,
        tg_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(OrderApplication).where(
                OrderApplication.worker_id == user_id
            )
        )
        await session.execute(
            delete(OrderWorker).where(
                OrderWorker.worker_id == user_id
            )
        )
        await session.execute(
            delete(User).where(
                User.id == user_id
            )
        )
        await session.execute(
            delete(CustomerForeman).where(
                CustomerForeman.tg_id == tg_id
            )
        )
        await session.execute(
            delete(ShoutStat).where(
                ShoutStat.sender_tg_id == tg_id
            )
        )
        await session.commit()


async def erase_worker_tg_id(
        user_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(
                User.id == user_id
            ).values(
                tg_id=0,
                max_id=0,
                last_web_ip=None,
            )
        )
        await session.commit()


async def erase_worker_data(
        user_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(
                User.id == user_id
            ).values(
                tg_id=0,
                max_id=0,
                phone_number=f'erased_{user_id}'
            )
        )
        await session.execute(
            delete(OrderApplication).where(
                OrderApplication.worker_id == user_id
            )
        )
        await session.commit()
