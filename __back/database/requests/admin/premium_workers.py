from database import PremiumWorker, PremiumCondition, User, DataForSecurity, async_session
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from decimal import Decimal


async def search_premium_workers_by_last_name(last_name: str) -> List[User]:
    """Поиск исполнителей по фамилии для премиальных исполнителей"""
    async with async_session() as session:
        workers = await session.scalars(
            select(User).join(DataForSecurity).where(
                DataForSecurity.last_name.ilike(f'%{last_name}%')
            )
        )
        return workers.all()


async def get_premium_worker(
    customer_id: int,
    worker_id: int
) -> Optional[PremiumWorker]:
    """Получить премиального исполнителя для заказчика"""
    async with async_session() as session:
        premium_worker = await session.scalar(
            select(PremiumWorker).where(
                PremiumWorker.customer_id == customer_id,
                PremiumWorker.worker_id == worker_id
            ).options(
                selectinload(PremiumWorker.conditions)
            )
        )
        return premium_worker


async def get_premium_worker_by_id(
    premium_worker_id: int
) -> Optional[PremiumWorker]:
    """Получить премиального исполнителя по ID"""
    async with async_session() as session:
        premium_worker = await session.scalar(
            select(PremiumWorker).where(
                PremiumWorker.id == premium_worker_id
            ).options(
                selectinload(PremiumWorker.conditions),
                selectinload(PremiumWorker.worker)
            )
        )
        return premium_worker


async def get_customer_premium_workers(
    customer_id: int
) -> List[PremiumWorker]:
    """Получить всех премиальных исполнителей заказчика"""
    async with async_session() as session:
        workers = await session.scalars(
            select(PremiumWorker).where(
                PremiumWorker.customer_id == customer_id
            ).options(
                selectinload(PremiumWorker.worker),
                selectinload(PremiumWorker.conditions)
            )
        )
        return workers.all()


async def set_premium_worker(
    customer_id: int,
    worker_id: int,
    bonus_type: str,
    conditions: Optional[List[Dict[str, str]]] = None
) -> None:
    """Создать премиального исполнителя"""
    async with async_session() as session:
        # Удаляем существующую запись если есть (перезапись)
        await session.execute(
            delete(PremiumWorker).where(
                PremiumWorker.customer_id == customer_id,
                PremiumWorker.worker_id == worker_id
            )
        )
        await session.flush()

        # Создаём новую запись
        new_premium = PremiumWorker(
            customer_id=customer_id,
            worker_id=worker_id,
            bonus_type=bonus_type
        )
        session.add(new_premium)
        await session.flush()

        # Добавляем условия
        if conditions:
            if bonus_type == 'unconditional':
                # Для безусловной премии сохраняем одно условие с порогом 0%
                session.add(
                    PremiumCondition(
                        premium_worker_id=new_premium.id,
                        threshold_percent='0,00',
                        bonus_amount=conditions[0]['amount']
                    )
                )
            else:
                # Для условной премии сохраняем все условия
                for condition in conditions:
                    session.add(
                        PremiumCondition(
                            premium_worker_id=new_premium.id,
                            threshold_percent=condition['percent'],
                            bonus_amount=condition['amount']
                        )
                    )

        await session.commit()


async def delete_premium_worker(
    premium_worker_id: int
) -> None:
    """Удалить премиального исполнителя"""
    async with async_session() as session:
        await session.execute(
            delete(PremiumWorker).where(
                PremiumWorker.id == premium_worker_id
            )
        )
        await session.commit()


async def calculate_bonus_for_worker(
    customer_id: int,
    worker_id: int,
    completion_percent: Decimal
) -> Decimal:
    """
    Рассчитать премию для исполнителя на основе процента исполнения заявки

    Args:
        customer_id: ID заказчика
        worker_id: ID исполнителя
        completion_percent: Процент исполнения заявки (уже округлённый до 2 знаков)

    Returns:
        Сумма премии (Decimal)
    """
    premium_worker = await get_premium_worker(customer_id, worker_id)

    if not premium_worker or not premium_worker.conditions:
        return Decimal('0')

    if premium_worker.bonus_type == 'unconditional':
        # Безусловная премия - возвращаем фиксированную сумму
        return Decimal(premium_worker.conditions[0].bonus_amount.replace(',', '.'))

    # Условная премия - ищем максимальный достигнутый порог
    eligible_conditions = [
        c for c in premium_worker.conditions
        if Decimal(c.threshold_percent.replace(',', '.')) <= completion_percent
    ]

    if not eligible_conditions:
        return Decimal('0')

    # Находим условие с максимальным порогом
    max_condition = max(
        eligible_conditions,
        key=lambda c: Decimal(c.threshold_percent.replace(',', '.'))
    )

    return Decimal(max_condition.bonus_amount.replace(',', '.'))


async def get_user_real_data_by_id(user_id: int) -> Optional[DataForSecurity]:
    """Получить реальные данные исполнителя (для отображения ФИО)"""
    async with async_session() as session:
        real_data = await session.scalar(
            select(DataForSecurity).where(
                DataForSecurity.user_id == user_id
            )
        )
        return real_data


async def get_user_by_id(user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    async with async_session() as session:
        user = await session.scalar(
            select(User).where(
                User.id == user_id
            )
        )
        return user
