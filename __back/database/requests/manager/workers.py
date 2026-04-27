from database import User, async_session
from sqlalchemy import select
from typing import List


async def get_workers_by_city(city: str) -> List[User]:
    """
    Получить всех самозанятых из указанного города, отсортированных по алфавиту

    Args:
        city: Название города

    Returns:
        Список самозанятых из города
    """
    async with async_session() as session:
        result = await session.scalars(
            select(User)
            .where(User.city == city)
            .order_by(User.last_name, User.first_name, User.middle_name)
        )
        return list(result.all())


async def search_workers_by_last_name(city: str, last_name: str) -> List[User]:
    """
    Поиск самозанятых по фамилии в указанном городе

    Args:
        city: Название города
        last_name: Фамилия для поиска (регистронезависимый поиск)

    Returns:
        Список найденных самозанятых
    """
    async with async_session() as session:
        # Поиск по частичному совпадению фамилии (регистронезависимый)
        search_pattern = f'%{last_name.lower()}%'
        result = await session.scalars(
            select(User)
            .where(User.city == city)
            .where(User.last_name.ilike(search_pattern))
            .order_by(User.last_name, User.first_name, User.middle_name)
        )
        return list(result.all())


async def search_workers_all_cities(last_name: str) -> List[User]:
    """
    Поиск самозанятых по фамилии во всех городах

    Args:
        last_name: Фамилия для поиска (регистронезависимый поиск)

    Returns:
        Список найденных самозанятых
    """
    async with async_session() as session:
        # Поиск по частичному совпадению фамилии (регистронезависимый)
        search_pattern = f'%{last_name.lower()}%'
        result = await session.scalars(
            select(User)
            .where(User.last_name.ilike(search_pattern))
            .order_by(User.last_name, User.first_name, User.middle_name)
        )
        return list(result.all())


async def get_worker_by_id(worker_id: int) -> User | None:
    """
    Получить самозанятого по ID

    Args:
        worker_id: ID самозанятого

    Returns:
        Объект User или None
    """
    async with async_session() as session:
        return await session.scalar(
            select(User).where(User.id == worker_id)
        )
