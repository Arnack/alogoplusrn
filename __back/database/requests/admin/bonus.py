from database import Settings, async_session
from sqlalchemy import update


async def update_bonus(bonus):
    async with async_session() as session:
        await session.execute(update(Settings).where(Settings.id == 1).values(bonus=bonus))
        await session.commit()
