from database.models import async_session, Director
from sqlalchemy import select


async def set_director(tg_id: int, full_name: str):
    """Добавить директора"""
    async with async_session() as session:
        session.add(Director(tg_id=tg_id, full_name=full_name))
        await session.commit()


async def get_directors_tg_id() -> list[int]:
    """Получить все tg_id директоров"""
    async with async_session() as session:
        directors = await session.execute(select(Director.tg_id))
        return directors.scalars().all()


async def get_directors() -> list[Director]:
    """Получить всех директоров"""
    async with async_session() as session:
        directors = await session.execute(select(Director))
        return directors.scalars().all()


async def get_director(director_id: int) -> Director:
    """Получить директора по ID"""
    async with async_session() as session:
        director = await session.execute(
            select(Director).where(Director.id == director_id)
        )
        return director.scalar_one()


async def get_director_by_tg_id(tg_id: int) -> Director | None:
    """Получить директора по Telegram ID (для подписей в документах)"""
    async with async_session() as session:
        director = await session.execute(
            select(Director).where(Director.tg_id == tg_id)
        )
        return director.scalar_one_or_none()


async def delete_director(director_id: int):
    """Удалить директора"""
    async with async_session() as session:
        director = await session.get(Director, director_id)
        await session.delete(director)
        await session.commit()
