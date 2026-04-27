import logging
from database import (
    User, Order, OrderApplication, OrderWorker, CodeForOrder, CodeDailyAttempts, OrderForFriendLogging, async_session
)
from sqlalchemy import select, func, delete, update
from datetime import datetime, timedelta
from typing import NoReturn, List

logger = logging.getLogger(__name__)


async def get_users_by_city(
        city: str
) -> List[User]:
    async with async_session() as session:
        users = await session.scalars(
            select(User).where(
                User.city == city
            )
        )
        return users.all()


async def skip_users(order_id):
    async with async_session() as session:
        workers_id = await session.scalars(select(OrderWorker.worker_id).where(OrderWorker.order_id == order_id))

        workers = []
        for worker_id in workers_id:
            workers.append(await session.scalar(select(User.tg_id).where(User.id == worker_id)))

        return workers


async def set_application(
        order_id: int,
        worker_id: int,
        order_from_friend: bool
) -> str:
    """
    Creates an application.
    Returns:
      'ok'        – inserted successfully
      'duplicate' – worker already applied to this order
      'error'     – unexpected DB error (logged)
    """
    try:
        async with async_session() as session:
            existing = await session.scalar(
                select(OrderApplication).where(
                    OrderApplication.order_id == order_id,
                    OrderApplication.worker_id == worker_id
                )
            )
            if existing:
                return 'duplicate'
            session.add(
                OrderApplication(
                    order_id=order_id,
                    worker_id=worker_id,
                    order_from_friend=order_from_friend
                )
            )
            await session.commit()
            return 'ok'
    except Exception as exc:
        logger.exception(f'set_application(order={order_id}, worker={worker_id}): {exc}')
        return 'error'


async def get_orders_count_for_search(worker_city, customer_id, worker_id):
    async with async_session() as session:
        worker_applications = await session.scalars(
            select(OrderApplication.order_id).where(OrderApplication.worker_id == worker_id)
        )
        worker_order_workers = await session.scalars(
            select(OrderWorker.order_id).where(OrderWorker.worker_id == worker_id)
        )

        orders_count = await session.scalar(
            select(func.count()).where(
                Order.city == worker_city,
                Order.customer_id == customer_id,
                Order.in_progress == False,
                Order.moderation == False,
                ~Order.id.in_(
                    [
                        *worker_applications.all(),
                        *worker_order_workers.all()
                    ]
                )
            )
        )
        return orders_count


async def get_orders_for_search(
        worker_city,
        worker_id,
        customer_id
):
    async with async_session() as session:

        worker_applications = await session.scalars(
            select(OrderApplication.order_id).where(OrderApplication.worker_id == worker_id)
        )
        worker_order_workers = await session.scalars(
            select(OrderWorker.order_id).where(OrderWorker.worker_id == worker_id)
        )

        orders = await session.scalars(
            select(Order).where(
                Order.city == worker_city,
                Order.customer_id == customer_id,
                Order.moderation == False,
                Order.in_progress == False,
                ~Order.id.in_(
                    [*worker_applications.all(),
                     *worker_order_workers.all()]
                )
            )
        )

        return orders.all()


async def has_application(worker_id, order_id):
    async with async_session() as session:
        return bool(await session.scalar(select(OrderApplication.id).where(OrderApplication.worker_id == worker_id,
                                                                           OrderApplication.order_id == order_id)))


async def get_applications_by_worker_id(worker_id):
    async with async_session() as session:
        return [app for app in await session.scalars(select(OrderApplication.order_id).where(
            OrderApplication.worker_id == worker_id))]


async def get_worker_application_id(order_id, worker_id):
    async with async_session() as session:
        return await session.scalar(select(OrderApplication.id).where(OrderApplication.order_id == order_id,
                                                                      OrderApplication.worker_id == worker_id))


async def get_worker_app_id(order_id, worker_id):
    async with async_session() as session:
        return await session.scalar(select(OrderWorker.id).where(OrderWorker.order_id == order_id,
                                                                 OrderWorker.worker_id == worker_id))


async def has_work(worker_id):
    async with async_session() as session:
        return bool(await session.scalar(select(OrderWorker.id).where(OrderWorker.worker_id == worker_id)))


async def get_orders_by_worker_id(worker_id):
    async with async_session() as session:
        orders = []
        applications = await session.scalars(select(OrderApplication).where(OrderApplication.worker_id == worker_id))
        workers = await session.scalars(select(OrderWorker).where(OrderWorker.worker_id == worker_id))
        for app in applications:
            orders.append(await session.scalar(select(Order).where(Order.id == app.order_id)))
        for w in workers:
            orders.append(await session.scalar(select(Order).where(Order.id == w.order_id)))
        return orders


async def delete_worker(worker_app_id):
    async with async_session() as session:
        await session.execute(delete(OrderWorker).where(OrderWorker.id == worker_app_id))
        await session.commit()


async def delete_order_worker(worker_id, order_id):
    async with async_session() as session:
        await session.execute(delete(OrderWorker).where(OrderWorker.worker_id == worker_id,
                                                        OrderWorker.order_id == order_id))
        await session.commit()


async def get_worker_dates(worker_id):
    async with async_session() as session:
        dates = []
        apps = await session.scalars(select(OrderApplication.order_id).where(OrderApplication.worker_id == worker_id))
        approved_apps = await session.scalars(select(OrderWorker.order_id).where(OrderWorker.worker_id == worker_id))

        worker_orders = [*apps.all(), *approved_apps.all()]

        for app_id in worker_orders:
            order = await session.scalar(select(Order).where(Order.id == app_id))
            dates.append(f"{order.date} {'день' if order.day_shift else 'ночь'}")

        return dates


async def set_code_for_order(
        code_hash: str,
        salt: str
) -> int:
    async with async_session() as session:
        new_code = CodeForOrder(
                code_hash=code_hash,
                salt=salt
        )
        session.add(new_code)
        await session.commit()
        await session.refresh(new_code)
        return new_code.id


async def get_code_for_order(
        code_id: str
) -> CodeForOrder:
    async with async_session() as session:
        return await session.scalar(
            select(CodeForOrder).where(
                CodeForOrder.id == code_id
            )
        )


async def delete_code_for_order(
        code_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(CodeForOrder).where(
                CodeForOrder.id == code_id
            )
        )
        await session.commit()


async def check_daily_code_attempts(
        phone_number: str
) -> bool:
    async with async_session() as session:
        now = datetime.now()

        attempt_record = await session.scalar(
            select(CodeDailyAttempts).where(
                CodeDailyAttempts.phone_number == phone_number
            )
        )

        if not attempt_record:
            new_attempt = CodeDailyAttempts(
                phone_number=phone_number,
                last_usage=now,
                attempts=2
            )
            session.add(new_attempt)
            await session.commit()
            return True
        else:
            if attempt_record.attempts > 0:
                attempt_record.attempts -= 1

                if attempt_record.attempts == 0:
                    attempt_record.last_usage = now

                await session.commit()
                return True
            else:
                time_diff = now - attempt_record.last_usage

                if time_diff >= timedelta(days=1):
                    attempt_record.last_usage = now
                    attempt_record.attempts = 2
                    await session.commit()
                    return True
                else:
                    return False


async def set_order_for_friend_log(
        order_id: int,
        who_signed: int,
        who_signed_tg_id: int,
        friend_id: int,
        friend_tg_id: int
) -> None:
    async with async_session() as session:
        session.add(
            OrderForFriendLogging(
                order_id=order_id,
                who_signed=who_signed,
                who_signed_tg_id=who_signed_tg_id,
                friend_id=friend_id,
                friend_tg_id=friend_tg_id
            )
        )
        await session.commit()


async def delete_order_for_friend_log(
        order_id: int,
        worker_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(OrderForFriendLogging).where(
                OrderForFriendLogging.order_id == order_id,
                OrderForFriendLogging.friend_id == worker_id
            ).values(
                order_deleted=True,
                when_deleted=datetime.now()
            )
        )
        await session.commit()
