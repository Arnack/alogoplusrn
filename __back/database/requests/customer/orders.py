from database import (
    Order,
    CustomerAdmin,
    OrderApplication,
    OrderArchive,
    OrderWorkerArchive,
    OrderWorker,
    async_session,
    Customer
)
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload
from typing import Optional, List, Union
from datetime import datetime
from decimal import Decimal
import pytz


async def set_order(admin, job_name, date, day_shift, night_shift, workers, city):
    async with async_session() as session:
        customer_id = await session.scalar(
            select(CustomerAdmin.customer_id).where(
                CustomerAdmin.admin == admin
            )
        )
        session.add(
            Order(
                customer_id=customer_id,
                job_name=job_name,
                date=date,
                day_shift=day_shift,
                night_shift=night_shift,
                workers=workers,
                city=city
            )
        )
        await session.commit()


async def get_order(
        order_id: int
) -> Order:
    async with async_session() as session:
        return await session.scalar(
            select(Order).where(
                Order.id == order_id
            )
        )


async def get_orders_in_progress() -> List[Order]:
    """Получить все активные заказы (in_progress=True)."""
    async with async_session() as session:
        orders = await session.scalars(
            select(Order).where(Order.in_progress == True)
        )
        return orders.all()


async def get_customer_orders(admin):
    async with async_session() as session:
        customer_id = await session.scalar(
            select(CustomerAdmin.customer_id).where(
                CustomerAdmin.admin == admin
            )
        )
        customer_orders = await session.scalars(
            select(Order).where(
                Order.customer_id == customer_id
            )
        )
        return customer_orders.all()


async def get_orders_count_for_customer(admin):
    async with async_session() as session:
        customer_id = await session.scalar(select(CustomerAdmin.customer_id).where(CustomerAdmin.admin == admin))
        return await session.scalar(select(func.count()).where(Order.customer_id == customer_id))


async def remove_duplicate_workers(order_id: int) -> int:
    """
    Удаляет дубликаты исполнителей из заявки.
    Оставляет только одну уникальную запись для каждого исполнителя.

    Args:
        order_id: ID заявки

    Returns:
        Количество удаленных дубликатов
    """
    async with async_session() as session:
        # Получаем все записи исполнителей для данной заявки
        order_workers = await session.scalars(
            select(OrderWorker).where(OrderWorker.order_id == order_id)
        )
        all_workers = order_workers.all()

        # Словарь для отслеживания уникальных исполнителей
        seen_workers = {}
        duplicates_to_delete = []

        for worker in all_workers:
            if worker.worker_id in seen_workers:
                # Это дубликат, добавляем в список на удаление
                duplicates_to_delete.append(worker.id)
            else:
                # Первая запись для этого исполнителя
                seen_workers[worker.worker_id] = worker.id

        # Удаляем дубликаты
        if duplicates_to_delete:
            for duplicate_id in duplicates_to_delete:
                await session.execute(
                    delete(OrderWorker).where(OrderWorker.id == duplicate_id)
                )
            await session.commit()

        return len(duplicates_to_delete)


async def f_delete_order(order_id):
    async with async_session() as session:
        await session.execute(delete(OrderApplication).where(OrderApplication.order_id == order_id))
        await session.execute(delete(OrderWorker).where(OrderWorker.order_id == order_id))
        await session.execute(delete(Order).where(Order.id == order_id))
        await session.commit()


async def update_order_workers(order_id: int, workers_count: int) -> bool:
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        # new_work_cycle = order.work_cycle + 1 if order else 1

        await session.execute(update(Order).where(Order.id == order_id).values(
            in_progress=False
            # work_cycle=new_work_cycle
        ))
        await session.execute(update(Order).where(Order.id == order_id).values(workers=workers_count))

        current_workers_count = await session.scalar(select(func.count()).where(OrderWorker.order_id == order_id))

        await session.commit()
        return current_workers_count < workers_count


async def order_set_search_workers(order_id):
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        # new_work_cycle = order.work_cycle + 1 if order else 1

        await session.execute(update(Order).where(Order.id == order_id).values(
            in_progress=False
            # work_cycle=new_work_cycle
        ))
        await session.commit()


async def check_time(order_id: int) -> bool:
    async with async_session() as session:
        day_shift = await session.scalar(select(Order.day_shift).where(Order.id == order_id))
        night_shift = await session.scalar(select(Order.night_shift).where(Order.id == order_id))

        time = day_shift if day_shift else night_shift
        date = await session.scalar(select(Order.date).where(Order.id == order_id))

        pattern = '%d.%m.%Y %H:%M'
        start_time = time.split('-')[0]

        moscow_tz = pytz.timezone('Europe/Moscow')
        start_dt = moscow_tz.localize(datetime.strptime(f"{date} {start_time.strip()}", pattern))
        now = datetime.now(moscow_tz)

        return start_dt <= now


async def check_time_less_than_12_hours(order_id: int) -> bool:
    """Проверить, осталось ли менее 12 часов до начала смены"""
    async with async_session() as session:
        day_shift = await session.scalar(select(Order.day_shift).where(Order.id == order_id))
        night_shift = await session.scalar(select(Order.night_shift).where(Order.id == order_id))

        time = day_shift if day_shift else night_shift
        date = await session.scalar(select(Order.date).where(Order.id == order_id))

        pattern = '%d.%m.%Y %H:%M'
        start_time = time.split('-')[0]

        moscow_tz = pytz.timezone('Europe/Moscow')
        start_dt = moscow_tz.localize(datetime.strptime(f"{date} {start_time.strip()}", pattern))
        now = datetime.now(moscow_tz)

        # Вычисляем разницу в часах
        time_diff = (start_dt - now).total_seconds() / 3600

        # Возвращаем True если осталось менее 12 часов (и смена еще не началась)
        return 0 <= time_diff < 12


async def get_orders_count_by_customer_id(customer_id):
    async with async_session() as session:
        return await session.scalar(
            select(func.count()).where(
                Order.customer_id == customer_id,
                Order.moderation == False,
                Order.in_progress == False
            )
        )


async def set_archive_order(
        order_id: int,
        customer_id: int,
        job_name: str,
        date: str,
        day_shift: Optional[str],
        night_shift: Optional[str],
        workers_count,
        city: str,
        manager_tg_id: int,
        amount: str,
        workers_hours: dict,
        workers_statuses: dict = None,
        travel_compensation: int = None
) -> None:
    async with async_session() as session:
        new_archive_order = OrderArchive(
            order_id=order_id,
            customer_id=customer_id,
            job_name=job_name,
            date=date,
            day_shift=day_shift,
            night_shift=night_shift,
            workers_count=workers_count,
            city=city,
            manager_tg_id=manager_tg_id,
            amount=amount
        )
        session.add(new_archive_order)

        workers = await session.scalars(
            select(OrderWorker.worker_id).where(
                OrderWorker.order_id == order_id
            )
        )

        if workers_statuses is None:
            workers_statuses = {}

        for worker_id in workers:
            hours = workers_hours.get(f"{worker_id}", '0')
            status = workers_statuses.get(f"{worker_id}", 'WORKED')

            # Определяем compensation_amount для EXTRA
            compensation_amount = None
            if status == 'EXTRA' and travel_compensation:
                compensation_amount = travel_compensation

            # Сохраняем все записи, включая NOT_OUT (0) и EXTRA (Л)
            session.add(
                OrderWorkerArchive(
                    worker_id=worker_id,
                    archive_order=new_archive_order,
                    worker_hours=hours,
                    date=date,
                    status=status,
                    compensation_amount=compensation_amount
                )
            )
        await session.commit()


async def get_archive_orders(
        archive_date: str
) -> List[OrderArchive]:
    async with async_session() as session:
        archive_orders = await session.scalars(
            select(OrderArchive).where(
                OrderArchive.date == archive_date
            )
        )
        return archive_orders.all()


async def get_archive_order(
        archive_id: int
) -> OrderArchive:
    async with async_session() as session:
        return await session.scalar(
            select(OrderArchive).where(
                OrderArchive.id == archive_id
            )
        )


async def get_archived_order_by_ord_id(
        order_id: int
) -> OrderArchive:
    async with async_session() as session:
        return await session.scalar(
            select(OrderArchive).where(
                OrderArchive.order_id == order_id
            )
        )


async def get_archive_order_workers(
        archive_id: int
) -> List[OrderWorkerArchive]:
    async with async_session() as session:
        archive_workers = await session.scalars(
            select(OrderWorkerArchive).where(
                OrderWorkerArchive.archive_order_id == archive_id,
                OrderWorkerArchive.status == 'WORKED'
            )
        )
        return archive_workers.all()


async def update_archive_order_workers_count(
        archive_id: int,
        workers_count: int
):
    async with async_session() as session:
        try:
            archive_order: OrderArchive = await session.scalar(
                select(OrderArchive).where(
                    OrderArchive.id == archive_id
                )
            )
            new_order = Order(
                    customer_id=archive_order.customer_id,
                    job_name=archive_order.job_name,
                    date=archive_order.date,
                    day_shift=archive_order.day_shift,
                    night_shift=archive_order.night_shift,
                    workers=workers_count,
                    city=archive_order.city,
                    moderation=False,
                    manager=archive_order.manager_tg_id,
                    amount=archive_order.amount
                )
            session.add(new_order)

            archive_order_workers = await session.scalars(
                select(OrderWorkerArchive).where(
                    OrderWorkerArchive.archive_order_id == archive_id
                )
            )

            for worker in archive_order_workers:
                session.add(
                    OrderWorker(
                        worker_id=worker.worker_id,
                        order=new_order
                    )
                )
                await session.execute(
                    delete(OrderWorkerArchive).where(
                        OrderWorkerArchive.id == worker.id
                    )
                )

            current_workers_count = await session.scalar(
                select(func.count()).where(
                    OrderWorkerArchive.archive_order_id == archive_id
                )
            )

            await session.execute(
                delete(OrderArchive).where(
                    OrderArchive.id == archive_id
                )
            )

            await session.commit()
            await session.refresh(new_order)
            return [current_workers_count < workers_count, new_order.id]
        except:
            await session.rollback()


async def get_archive_orders_for_month(month: int, year: int) -> List[dict]:
    """Получить архивные заказы за месяц с данными о получателе и работниках.

    Возвращает список словарей:
    {
        'customer_name': str,
        'date': str (DD.MM.YYYY),
        'day_shift': str | None,
        'night_shift': str | None,
        'workers_count': int (заявка),
        'worked_count': int (вышло - кол-во WORKED)
    }
    """
    month_str = f"{month:02d}.{year}"
    async with async_session() as session:
        archive_orders = (await session.scalars(
            select(OrderArchive)
            .where(OrderArchive.date.like(f'%.{month_str}'))
            .options(selectinload(OrderArchive.archive_order_workers))
        )).all()

        if not archive_orders:
            return []

        customer_ids = list({o.customer_id for o in archive_orders})
        customers = (await session.scalars(
            select(Customer).where(Customer.id.in_(customer_ids))
        )).all()
        customer_map = {c.id: c.organization for c in customers}

        result = []
        for order in archive_orders:
            worked_count = sum(
                1 for w in order.archive_order_workers if w.status == 'WORKED'
            )
            result.append({
                'customer_name': customer_map.get(order.customer_id, 'Неизвестно'),
                'date': order.date,
                'day_shift': order.day_shift,
                'night_shift': order.night_shift,
                'workers_count': order.workers_count,
                'worked_count': worked_count,
            })
        return result


async def get_latest_archive_order_for_order(order_id: int) -> OrderArchive | None:
    """Получить последнюю архивную запись для заказа"""
    async with async_session() as session:
        return await session.scalar(
            select(OrderArchive)
            .where(OrderArchive.order_id == order_id)
            .order_by(OrderArchive.id.desc())
            .limit(1)
        )
