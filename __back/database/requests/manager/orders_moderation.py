from database import Order, OrderApplication, OrderWorker, DataForSecurity, CustomerJob, async_session
from sqlalchemy import select, func, update, join
from sqlalchemy.orm import selectinload
from typing import List, Union


async def get_orders_count_for_moderation():
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(Order.moderation == True))


async def get_orders_count_for_applications_moderation():
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(Order.moderation == False,
                                                               Order.in_progress == False))


async def get_orders_count_in_progress():
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(Order.in_progress == True))


async def get_orders_for_moderation():
    async with async_session() as session:
        return [el for el in await session.scalars(select(Order).where(Order.moderation == True))]


async def get_orders_for_info() -> List[Order]:
    async with async_session() as session:
        orders = await session.scalars(
            select(Order).where(
                Order.moderation == False,
                Order.in_progress == False
            )
        )
        return orders.all()


async def get_orders_for_supervisor(
        customer_id: int
) -> List[Order]:
    async with async_session() as session:
        orders = await session.scalars(
            select(Order).where(
                Order.moderation == False,
                Order.customer_id == customer_id
            )
        )
        return orders.all()


async def get_orders_in_progress():
    async with async_session() as session:
        return [el for el in await session.scalars(select(Order).where(Order.in_progress == True))]


async def get_applications_count_by_order_id(order_id):
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(OrderApplication.order_id == order_id))


async def get_order_workers_count_by_order_id(
        order_id: int
) -> int:
    async with async_session() as session:
        return await session.scalar(
            select(func.count()).where(
                OrderWorker.order_id == order_id
            )
        )


async def get_order_workers_id_by_order_id(
        order_id: int
) -> List[int]:
    async with async_session() as session:
        join_condition = OrderWorker.worker_id == DataForSecurity.user_id
        order_workers = await session.scalars(
            select(OrderWorker.worker_id).select_from(
                join(OrderWorker, DataForSecurity, join_condition)
            ).where(
                OrderWorker.order_id == order_id
            ).order_by(
                DataForSecurity.last_name.asc()
            )
        )
        return order_workers.all()


async def set_amount(order_id, amount, manager):
    async with async_session() as session:
        await session.execute(
            update(Order).where(
                Order.id == order_id
            ).values(
                amount=amount,
                moderation=False,
                manager=manager
            )
        )
        await session.commit()


async def set_order_workers_count(order_id: int, workers: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(Order).where(Order.id == order_id).values(workers=workers)
        )
        await session.commit()


async def get_job_amount(
        job_name: str,
        customer_id: int
) -> Union[str, None]:
    async with async_session() as session:
        job_data: CustomerJob = await session.scalar(
            select(CustomerJob).where(
                CustomerJob.job == job_name,
                CustomerJob.customer_id == customer_id
            ).options(
                selectinload(
                    CustomerJob.amount
                )
            )
        )
        if job_data and job_data.amount:
            return job_data.amount.amount
        return None
