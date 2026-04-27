from database import async_session, Settings
from sqlalchemy import select


async def get_settings() -> Settings:
    async with async_session() as session:
        return await session.scalar(
            select(Settings).where(
                Settings.id == 1
            )
        )
