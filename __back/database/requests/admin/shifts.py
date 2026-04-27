from database import Settings, async_session
from sqlalchemy import update


async def update_shifts(shifts):
    async with async_session() as session:
        await session.execute(update(Settings).where(Settings.id == 1).values(shifts=shifts))
        await session.commit()
