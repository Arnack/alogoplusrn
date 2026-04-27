from database import (
    Customer, CustomerJob, CustomerAdmin, CustomerForeman, CustomerCity, City, User, async_session,
    CustomerCityWay, CityWayPhoto, CustomerJobAmount, CustomerGroup
)
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import NoReturn, List, Optional


async def get_customer_cities(customer_id):
    async with async_session() as session:
        cities = await session.scalars(select(CustomerCity).where(CustomerCity.customer_id == customer_id))
        return cities.all()


async def update_day_shift(customer_id, day_shift):
    async with async_session() as session:
        await session.execute(update(Customer).where(Customer.id == customer_id).values(day_shift=day_shift))
        await session.commit()


async def update_night_shift(customer_id, night_shift):
    async with async_session() as session:
        await session.execute(update(Customer).where(Customer.id == customer_id).values(night_shift=night_shift))
        await session.commit()


async def save_new_job(
        customer_id: int,
        job: str,
        amount: str
):
    async with async_session() as session:
        new_job = CustomerJob(customer_id=customer_id, job=job)
        session.add(new_job)
        session.add(
            CustomerJobAmount(
                amount=amount,
                job=new_job
            )
        )
        await session.commit()


async def save_new_city(customer_id, city):
    async with async_session() as session:
        session.add(CustomerCity(customer_id=customer_id, city=city))
        session.add(City(city_name=city))
        await session.commit()


async def update_city(city, city_id):
    async with async_session() as session:
        old_city = await session.scalar(select(CustomerCity.city).where(CustomerCity.id == city_id))
        await session.execute(update(CustomerCity).where(CustomerCity.id == city_id).values(city=city))
        await session.execute(update(City).where(City.city_name == old_city).values(city_name=city))
        await session.execute(update(User).where(User.city == old_city).values(city=city))
        await session.commit()


async def save_new_admin(customer_id, admin_full_name, admin_tg_id):
    async with async_session() as session:
        session.add(
            CustomerAdmin(
                customer_id=customer_id,
                admin_full_name=admin_full_name,
                admin=admin_tg_id
            )
        )
        await session.commit()


async def set_customer_group(
        customer_id: int,
        group_name: str,
        group_chat_id: str
) -> None:
    async with async_session() as session:
        session.add(
            CustomerGroup(
                customer_id=customer_id,
                group_name=group_name,
                chat_id=group_chat_id
            )
        )
        await session.commit()


async def get_customer_groups(
        customer_id: int
) -> List[CustomerGroup]:
    async with async_session() as session:
        customer_groups = await session.scalars(
            select(CustomerGroup).where(
                CustomerGroup.customer_id == customer_id
            )
        )
        return customer_groups.all()


async def get_customer_group_by_id(
        group_id: int
) -> CustomerGroup:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerGroup).where(
                CustomerGroup.id == group_id
            )
        )


async def delete_customer_admin(admin_id):
    async with async_session() as session:
        await session.execute(delete(CustomerAdmin).where(CustomerAdmin.id == admin_id))
        await session.commit()


async def delete_customer_group(
        group_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(CustomerGroup).where(
                CustomerGroup.id == group_id
            )
        )
        await session.commit()


async def save_new_foreman(customer_id, foreman_full_name, foreman_tg_id):
    async with async_session() as session:
        session.add(
            CustomerForeman(
                customer_id=customer_id,
                full_name=foreman_full_name,
                tg_id=foreman_tg_id
            )
        )
        await session.commit()


async def delete_foreman(foreman_id):
    async with async_session() as session:
        await session.execute(delete(CustomerForeman).where(CustomerForeman.id == foreman_id))
        await session.commit()


async def get_customer_city_id(
        customer_id: int,
        city: str
) -> int:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerCity.id).where(
                CustomerCity.customer_id == customer_id,
                CustomerCity.city == city
            )
        )


async def get_customer_city_way(
        city_id: int
) -> CustomerCityWay:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerCityWay).where(
                CustomerCityWay.customer_city_id == city_id
            ).options(
                selectinload(
                    CustomerCityWay.city_photos
                )
            )
        )


async def set_customer_city_way(
        city_id: int,
        way_description: str,
        way_photos: Optional[List[str]]
) -> NoReturn:
    async with async_session() as session:
        new_way = CustomerCityWay(
            customer_city_id=city_id,
            way_to_job=way_description
        )
        session.add(new_way)

        if way_photos:
            for photo in way_photos:
                session.add(
                    CityWayPhoto(
                        photo=photo,
                        city_way=new_way
                    )
                )
        await session.commit()


async def update_customer_city_way(
        city_id: int,
        way_description: str,
        way_photos: Optional[List[str]]
) -> NoReturn:
    async with async_session() as session:
        await session.execute(
            delete(CustomerCityWay).where(
                CustomerCityWay.customer_city_id == city_id
            )
        )
        new_way = CustomerCityWay(
            customer_city_id=city_id,
            way_to_job=way_description
        )
        session.add(new_way)

        if way_photos:
            for photo in way_photos:
                session.add(
                    CityWayPhoto(
                        photo=photo,
                        city_way=new_way
                    )
                )
        await session.commit()


async def get_customer_jobs(
        customer_id: int
) -> List[CustomerJob]:
    async with async_session() as session:
        jobs = await session.scalars(
            select(CustomerJob).where(
                CustomerJob.customer_id == customer_id
            )
        )
        return jobs.all()


async def get_customer_job(
        customer_job_id: int
) -> CustomerJob:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerJob).where(
                CustomerJob.id == customer_job_id
            )
        )


async def set_or_update_job_amount(
        job_id: int,
        new_amount: str
) -> None:
    async with async_session() as session:
        has_amount = await session.scalar(
            select(CustomerJobAmount).where(
                CustomerJobAmount.job_id == job_id
            )
        )
        if has_amount:
            await session.execute(
                update(CustomerJobAmount).where(
                    CustomerJobAmount.job_id == job_id
                ).values(
                    amount=new_amount
                )
            )
        else:
            session.add(
                CustomerJobAmount(
                    job_id=job_id,
                    amount=new_amount
                )
            )
        await session.commit()
