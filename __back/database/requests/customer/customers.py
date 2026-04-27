from database import (
    Customer, City, CustomerCity, CustomerJob, CustomerAdmin, CustomerForeman, Order, async_session, CustomerCityWay,
    CityWayPhoto, CustomerJobAmount
)
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from typing import Dict, List, NoReturn, Optional


async def set_costumer(
        admins: Dict,
        foremen: Dict,
        organization: Dict,
        day_shift: Optional[str],
        night_shift: Optional[str],
        cities: Dict,
        jobs: Dict
) -> NoReturn:
    async with async_session() as session:
        new_customer = Customer(
            organization=organization,
            day_shift=day_shift,
            night_shift=night_shift
        )
        session.add(new_customer)

        for city_name in cities:
            existing_city = await session.scalar(select(City).where(City.city_name == city_name))
            if not existing_city:
                session.add(City(city_name=city_name))

            new_city = CustomerCity(
                    city=city_name,
                    customer=new_customer
            )
            new_city_way = CustomerCityWay(
                way_to_job=cities[city_name]['CityWayDescription'],
                city=new_city
            )
            session.add(new_city)
            session.add(new_city_way)
            for photo in cities[city_name]['CityWayPhotos']:
                session.add(
                    CityWayPhoto(
                        photo=photo,
                        city_way=new_city_way
                    )
                )

        for job_name, amount in jobs.items():
            new_job = CustomerJob(
                    job=job_name,
                    customer=new_customer
                )
            session.add(new_job)
            session.add(
                CustomerJobAmount(
                    amount=amount,
                    job=new_job
                )
            )

        for full_name, tg_id in admins.items():
            session.add(
                CustomerAdmin(
                    admin=tg_id,
                    admin_full_name=full_name,
                    customer=new_customer
                )
            )

        for full_name, tg_id in foremen.items():
            session.add(
                CustomerForeman(
                    tg_id=tg_id,
                    full_name=full_name,
                    customer=new_customer
                )
            )
        await session.commit()


async def get_customer_full_info(customer_id):
    async with async_session() as session:
        customer = await session.scalar(
            select(Customer).where(
                Customer.id == int(customer_id)
            )
        )
        cities = await session.scalars(
            select(CustomerCity.city).where(
                CustomerCity.customer_id == int(customer_id)
            )
        )
        jobs = await session.scalars(
            select(CustomerJob).where(
                CustomerJob.customer_id == int(customer_id)
            ).options(
                selectinload(
                    CustomerJob.amount
                )
            )
        )
        admins = await session.scalars(
            select(CustomerAdmin.admin).where(
                CustomerAdmin.customer_id == int(customer_id)
            )
        )
        foremen = await session.scalars(
            select(CustomerForeman.tg_id).where(
                CustomerForeman.customer_id == int(customer_id)
            )
        )

        return [
            customer,
            cities.all(),
            jobs.all(),
            [str(admin) for admin in admins],
            [str(foreman) for foreman in foremen]
        ]


async def get_customer(
        customer_id: int
) -> Customer:
    async with async_session() as session:
        return await session.scalar(
            select(Customer).where(
                Customer.id == customer_id
            )
        )


async def get_customers_id_by_city(
        city: str
) -> List[int]:
    async with async_session() as session:
        customers_id = await session.scalars(
            select(CustomerCity.customer_id).where(
                CustomerCity.city == city
            )
        )
        return customers_id.all()


async def get_customers_by_city(
        city: str
) -> List[Customer]:
    async with async_session() as session:
        customers_id = await session.scalars(
            select(CustomerCity.customer_id).where(
                CustomerCity.city == city
            )
        )

        customers = []
        for customer_id in customers_id:
            customers.append(
                await session.scalar(
                    select(Customer).where(
                        Customer.id == customer_id
                    )
                )
            )

        return customers


async def get_customer_info(
        customer_id: int
) -> Customer:
    async with async_session() as session:
        return await session.scalar(
            select(Customer).where(
                Customer.id == customer_id
            )
        )


async def get_customer_organization(customer_id):
    async with async_session() as session:
        return await session.scalar(select(Customer.organization).where(Customer.id == customer_id))


async def get_customer_shifts(admin):
    async with async_session() as session:
        customer_id = await session.scalar(select(CustomerAdmin.customer_id).where(CustomerAdmin.admin == admin))
        return await session.scalar(select(Customer).where(Customer.id == customer_id))


async def get_customers_for_filter():
    async with async_session() as session:
        return [el for el in await session.scalars(select(CustomerAdmin.admin))]


async def get_customers() -> List[Customer]:
    async with async_session() as session:
        customers = await session.scalars(
            select(Customer)
        )
        return customers.all()


async def get_admins_by_customer_id(customer_id):
    async with async_session() as session:
        admins = await session.scalars(select(CustomerAdmin.admin).where(CustomerAdmin.customer_id == customer_id))
        return admins.all()


async def get_customer_admin_by_tg_id(tg_id):
    async with async_session() as session:
        return await session.scalars(select(CustomerAdmin).where(CustomerAdmin.admin == tg_id))


async def delete_customer(customer_id):
    async with async_session() as session:
        await session.execute(delete(Customer).where(Customer.id == customer_id))
        try:
            await session.execute(delete(CustomerAdmin).where(CustomerAdmin.customer_id == customer_id))
            await session.execute(delete(CustomerJob).where(CustomerJob.customer_id == customer_id))
            await session.execute(delete(CustomerCity).where(CustomerCity.customer_id == customer_id))
        except:
            pass
        await session.execute(delete(Order).where(Order.customer_id == customer_id))
        await session.commit()


async def get_customer_admin(
        admin_tg_id: int
) -> CustomerAdmin:
    async with async_session() as session:
        return await session.scalar(
            select(CustomerAdmin).where(
                CustomerAdmin.admin == admin_tg_id
            )
        )


async def get_customer_admin_by_id(admin_id):
    async with async_session() as session:
        return await session.scalar(select(CustomerAdmin).where(CustomerAdmin.id == admin_id))


async def set_travel_compensation(
        customer_id: int,
        amount: int
) -> NoReturn:
    """Установить сумму компенсации Платформы за проезд для заказчика"""
    async with async_session() as session:
        await session.execute(
            update(Customer)
            .where(Customer.id == customer_id)
            .values(travel_compensation=amount)
        )
        await session.commit()


async def get_travel_compensation(
        customer_id: int
) -> Optional[int]:
    """Получить сумму компенсации для заказчика"""
    async with async_session() as session:
        result = await session.scalar(
            select(Customer.travel_compensation)
            .where(Customer.id == customer_id)
        )
        return result
