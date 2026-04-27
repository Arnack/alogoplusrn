from database import User, async_session
from sqlalchemy import select, func


async def get_workers_count_for_stats():
    async with async_session() as session:
        return await session.scalar(select(func.count(User.id)))
