from database import User, async_session
from sqlalchemy import select, update


async def get_user_current_city(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User.city).where(User.tg_id == tg_id))


async def update_user_city(
        worker_id: int,
        city: str
):
    async with async_session() as session:
        await session.execute(
            update(User).where(
                User.id == worker_id
            ).values(
                city=city
            )
        )
        await session.commit()
