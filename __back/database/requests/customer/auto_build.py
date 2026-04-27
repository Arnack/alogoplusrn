from datetime import datetime, timedelta
from sqlalchemy import select

from database import (
    Order,
    Customer,
    CustomerJob,
    CustomerCity,
    async_session
)


async def create_schedule_order(
        customer_id: int
) -> None:
    async with async_session() as session:
        customer = await session.scalar(
            select(Customer).where(
                Customer.id == customer_id
            )
        )
        jobs = await session.scalars(
            select(CustomerJob.job).where(
                CustomerJob.customer_id == customer_id
            )
        )
        cities = await session.scalars(
            select(CustomerCity.city).where(
                CustomerCity.customer_id == customer_id
            )
        )

        jobs = jobs.all()
        cities = cities.all()

        date = datetime.now() + timedelta(days=7)
        date_str = datetime.strftime(date, "%d.%m.%Y")

        for city in cities:
            for job_name in jobs:
                if customer.day_shift:
                    session.add(
                        Order(
                            customer_id=customer_id,
                            job_name=job_name,
                            date=date_str,
                            day_shift=customer.day_shift,
                            night_shift=None,
                            workers=100,
                            city=city
                        )
                    )
                if customer.night_shift:
                    session.add(
                        Order(
                            customer_id=customer_id,
                            job_name=job_name,
                            date=date_str,
                            day_shift=None,
                            night_shift=customer.night_shift,
                            workers=100,
                            city=city
                        )
                    )
        await session.commit()
