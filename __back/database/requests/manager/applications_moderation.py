from database import OrderApplication, User, DataForSecurity, OrderWorker, CustomerAdmin, Order, OrderWorkerArchive, async_session
from sqlalchemy import select, func, delete, update, join
from sqlalchemy.orm import joinedload

from utils.rating.rating import get_rating
from database.models import UserRating
from typing import List, Optional, NoReturn
import logging


async def get_applications_count_by_order_id(order_id):
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(OrderApplication.order_id == order_id))


async def get_applications_by_order_id(order_id):
    async with async_session() as session:
        return await session.scalars(select(OrderApplication).where(OrderApplication.order_id == order_id))


async def get_applications_for_moderation(
        order_id: int
) -> List[OrderApplication]:
    async with async_session() as session:
        join_condition = OrderApplication.worker_id == DataForSecurity.user_id
        applications = await session.scalars(
            select(OrderApplication).select_from(
                join(OrderApplication, DataForSecurity, join_condition)
            ).where(
                OrderApplication.order_id == order_id
            ).order_by(
                DataForSecurity.last_name.asc()
            )
        )
        return applications.all()


async def get_application(application_id) -> OrderApplication:
    async with async_session() as session:
        return await session.scalar(select(OrderApplication).where(OrderApplication.id == application_id))


async def delete_application(application_id):
    async with async_session() as session:
        await session.execute(delete(OrderApplication).where(OrderApplication.id == application_id))
        await session.commit()


async def get_worker_app_data(
        worker_app_id: int
) -> OrderWorker:
    async with async_session() as session:
        return await session.scalar(
            select(OrderWorker).where(
                OrderWorker.id == worker_app_id
            )
        )


async def delete_applications_by_order_id(order_id):
    async with async_session() as session:
        await session.execute(delete(OrderApplication).where(OrderApplication.order_id == order_id))
        await session.commit()


async def get_user_real_data_by_id(
        user_id: int
) -> DataForSecurity:
    async with async_session() as session:
        return await session.scalar(
            select(DataForSecurity).where(
                DataForSecurity.user_id == user_id
            )
        )


async def get_user_by_id(user_id) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.id == user_id
            )
        )


async def set_worker_to_order_workers(
        order_id: int,
        worker_id: int,
        added_by_manager: bool,
        order_from_friend: Optional[bool] = False
):
    async with async_session() as session:
        session.add(
            OrderWorker(
                order_id=order_id,
                worker_id=worker_id,
                added_by_manager=added_by_manager,
                order_from_friend=order_from_friend
            )
        )
        await session.commit()


async def get_reg_order_workers(order_id):
    async with async_session() as session:
        return await session.scalar(select(func.count()).where(OrderWorker.order_id == order_id))


async def get_order_workers_tg_id(
        order_id: int,
) -> list[int]:
    async with async_session() as session:
        workers: list[OrderWorker] = await session.scalars(
            select(OrderWorker).where(
                OrderWorker.order_id == order_id
            ).options(
                joinedload(OrderWorker.user)
            )
        )

        return [worker.user.tg_id for worker in workers]


async def get_order_worker(worker_id, order_id) -> OrderWorker:
    async with async_session() as session:
        return await session.scalar(
            select(OrderWorker).where(
                OrderWorker.worker_id == worker_id,
                OrderWorker.order_id == order_id
            )
        )


async def get_customer_admins(customer_id):
    async with async_session() as session:
        customer_admins = await session.scalars(select(CustomerAdmin).where(CustomerAdmin.customer_id == customer_id))
        return customer_admins.all()


async def get_workers_for_pdf(
        order_id: int
) -> dict:
    async with async_session() as session:
        workers_id = await session.scalars(select(OrderWorker.worker_id).where(OrderWorker.order_id == order_id))

        result = {}
        for worker_id in workers_id:
            worker = await session.scalar(select(DataForSecurity).where(DataForSecurity.user_id == worker_id))

            if worker is None:
                # Критическая ошибка: работник в заказе, но нет данных для безопасности
                logging.error(
                    f'КРИТИЧЕСКАЯ ОШИБКА: Работник с ID {worker_id} в заказе {order_id}, '
                    f'но отсутствуют данные в таблице DataForSecurity! '
                    f'Этот работник НЕ ПОПАДЁТ в PDF и bad_workers!'
                )
                # Получаем основные данные работника из таблицы User в качестве запасного варианта
                user = await session.scalar(select(User).where(User.id == worker_id))
                if user:
                    logging.warning(
                        f'Используем данные из таблицы User для работника {worker_id}: '
                        f'{user.last_name} {user.first_name} {user.middle_name}'
                    )
                    result[f'{user.id}'] = {
                        'last_name': user.last_name,
                        'first_name': user.first_name,
                        'middle_name': user.middle_name
                    }
                else:
                    logging.critical(
                        f'Работник {worker_id} не найден ни в DataForSecurity, ни в User! '
                        f'Пропускаем этого работника.'
                    )
                continue

            result[f'{worker.user_id}'] = {
                'last_name': worker.last_name,
                'first_name': worker.first_name,
                'middle_name': worker.middle_name
            }
        return result


async def get_all_workers_for_adm_pdf():
    async with async_session() as session:
        workers = await session.scalars(
            select(User)
        )

        result = []
        for worker in workers.all():
            worker_real = await session.scalar(select(DataForSecurity).where(DataForSecurity.user_id == worker.id))
            rating = await session.scalar(select(UserRating).where(UserRating.user_id == worker.id))
            user_rating = await get_rating(worker.id)

            result.append(
                {
                    'fio': f'{worker.last_name} {worker.first_name} {worker.middle_name}',
                    'city': worker.city,
                    'phone_number': worker.phone_number,
                    'real_fio': f'{worker_real.last_name} {worker_real.first_name} {worker_real.middle_name}',
                    'real_phone_number': worker_real.phone_number,
                    'tg_id': worker.tg_id,
                    'max_id': worker.max_id,
                    'rating': f'{rating.total_orders}/{rating.successful_orders} {user_rating}',
                    'web_ip': worker.last_web_ip or '',
                }
            )

        return result


async def order_set_in_progress(order_id, manager_tg_id):
    async with async_session() as session:
        await session.execute(
            update(Order).where(Order.id == order_id).values(
                in_progress=True,
                manager=manager_tg_id
            )
        )
        await session.commit()


async def get_workers_by_last_name(
        last_name: str
) -> List[DataForSecurity]:
    async with async_session() as session:
        workers = await session.scalars(
            select(DataForSecurity).where(
                DataForSecurity.last_name == last_name
            )
        )
        return workers.all()


async def rating_plus_1(
        worker_id: int
) -> None:
    async with async_session() as session:
        rating = await session.scalar(
            select(UserRating).where(
                UserRating.user_id == worker_id
            )
        )
        rating.plus += 1
        await session.commit()
