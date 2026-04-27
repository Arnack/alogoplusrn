from database import async_session, Settings
from sqlalchemy import select


async def set_default_settings():
    async with async_session() as session:
        settings = await session.scalar(select(Settings).where(Settings.id == 1))

        if not settings:
            session.add(Settings(shifts=10, bonus=1000))
            await session.commit()
