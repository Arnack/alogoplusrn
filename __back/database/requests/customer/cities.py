from database import City, CustomerCity, CustomerAdmin, async_session
from sqlalchemy import select
from typing import List


async def get_city_by_id(
        city_id: int
) -> City:
    async with async_session() as session:
        return await session.scalar(
            select(City).where(
                City.id == city_id
            )
        )


async def get_city_by_name(
        city_name: str
) -> City:
    async with async_session() as session:
        return await session.scalar(
            select(City).where(
                City.city_name == city_name
            )
        )


async def get_cities_name() -> List[str]:
    async with async_session() as session:
        return await session.scalars(
            select(City.city_name).distinct()
        )


async def get_cities() -> List[City]:
    async with async_session() as session:
        cities = await session.scalars(
            select(City).distinct()
        )
        return cities.all()


async def get_customer_cities_by_admin(admin):
    async with async_session() as session:
        customer_id = await session.scalar(
            select(CustomerAdmin.customer_id).where(
                CustomerAdmin.admin == admin
            )
        )
        return await session.scalars(
            select(CustomerCity.city).where(
                CustomerCity.customer_id == customer_id
            )
        )
