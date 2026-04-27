from database import (
    DebtorCycle, NoShowEvent, NoShowCashierMessage, User, DataForSecurity,
    async_session
)
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List
from datetime import datetime, timedelta


async def get_active_cycle_for_worker(worker_id: int) -> DebtorCycle | None:
    """Получить активный цикл должника для исполнителя"""
    async with async_session() as session:
        result = await session.scalar(
            select(DebtorCycle)
            .where(DebtorCycle.worker_id == worker_id, DebtorCycle.status == 'active')
            .options(selectinload(DebtorCycle.no_show_events))
        )
        return result


async def create_debtor_cycle(worker_id: int) -> DebtorCycle:
    """Создать новый цикл должника"""
    async with async_session() as session:
        cycle = DebtorCycle(
            worker_id=worker_id,
            status='active',
            created_at=datetime.now()
        )
        session.add(cycle)
        await session.commit()
        await session.refresh(cycle)
        return cycle


async def create_no_show_event(
    cycle_id: int,
    order_archive_id: int | None,
    no_show_date: str,
    assigned_amount: int = 3000
) -> NoShowEvent:
    """Создать событие невыхода"""
    async with async_session() as session:
        event = NoShowEvent(
            cycle_id=cycle_id,
            order_archive_id=order_archive_id,
            no_show_date=no_show_date,
            assigned_amount=assigned_amount,
            buttons_expire_at=datetime.now() + timedelta(hours=24),
            created_at=datetime.now()
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


async def add_cashier_message(
    event_id: int,
    cashier_tg_id: int,
    message_id: int
) -> None:
    """Добавить запись о сообщении кассиру"""
    async with async_session() as session:
        msg = NoShowCashierMessage(
            event_id=event_id,
            cashier_tg_id=cashier_tg_id,
            message_id=message_id
        )
        session.add(msg)
        await session.commit()


async def get_no_show_event(event_id: int) -> NoShowEvent | None:
    """Получить событие невыхода со всеми связанными данными"""
    async with async_session() as session:
        result = await session.scalar(
            select(NoShowEvent)
            .where(NoShowEvent.id == event_id)
            .options(
                selectinload(NoShowEvent.cashier_messages),
                joinedload(NoShowEvent.cycle).joinedload(DebtorCycle.worker).joinedload(User.security)
            )
        )
        return result


async def get_cashier_messages_for_event(event_id: int) -> List[NoShowCashierMessage]:
    """Получить все сообщения кассирам для события"""
    async with async_session() as session:
        result = await session.scalars(
            select(NoShowCashierMessage)
            .where(NoShowCashierMessage.event_id == event_id)
        )
        return result.all()


async def mark_event_reviewed(
    event_id: int,
    cashier_tg_id: int,
    new_amount: int
) -> None:
    """Отметить событие как проверенное кассиром"""
    async with async_session() as session:
        event = await session.scalar(
            select(NoShowEvent).where(NoShowEvent.id == event_id)
        )
        if event:
            event.cashier_reviewed = True
            event.cashier_reviewed_by = cashier_tg_id
            event.cashier_reviewed_at = datetime.now()
            event.assigned_amount = new_amount
            await session.commit()


async def get_max_assigned_amount_for_active_cycle(worker_id: int) -> int:
    """Получить максимальную назначенную сумму для активного цикла исполнителя"""
    async with async_session() as session:
        result = await session.scalar(
            select(func.max(NoShowEvent.assigned_amount))
            .join(DebtorCycle)
            .where(
                DebtorCycle.worker_id == worker_id,
                DebtorCycle.status == 'active'
            )
        )
        return result if result is not None else 0


async def close_cycle_as_deducted(
    cycle_id: int,
    deducted_amount: int
) -> None:
    """Закрыть цикл как удержанный"""
    async with async_session() as session:
        cycle = await session.scalar(
            select(DebtorCycle).where(DebtorCycle.id == cycle_id)
        )
        if cycle:
            cycle.status = 'deducted'
            cycle.deducted_amount = deducted_amount
            cycle.deduction_date = datetime.now().strftime('%d.%m.%Y')
            await session.commit()


async def annul_cycle(
    cycle_id: int,
    admin_tg_id: int
) -> None:
    """Аннулировать цикл (администратором)"""
    async with async_session() as session:
        cycle = await session.scalar(
            select(DebtorCycle).where(DebtorCycle.id == cycle_id)
        )
        if cycle:
            cycle.status = 'annulled'
            cycle.annulled_by = admin_tg_id
            cycle.annulled_at = datetime.now()
            await session.commit()


async def get_no_show_events_for_worker_active_cycle(worker_id: int) -> List[NoShowEvent]:
    """Получить все события невыхода для активного цикла исполнителя"""
    async with async_session() as session:
        result = await session.scalars(
            select(NoShowEvent)
            .join(DebtorCycle)
            .where(
                DebtorCycle.worker_id == worker_id,
                DebtorCycle.status == 'active'
            )
        )
        return result.all()


async def get_workers_with_active_cycles() -> List[DebtorCycle]:
    """Получить всех исполнителей с активными циклами (для отчёта)"""
    async with async_session() as session:
        result = await session.scalars(
            select(DebtorCycle)
            .where(DebtorCycle.status == 'active')
            .options(
                selectinload(DebtorCycle.no_show_events),
                joinedload(DebtorCycle.worker).joinedload(User.security)
            )
        )
        return result.all()


async def get_cycles_for_archive_report(
    start_date_str: str,
    end_date_str: str
) -> List[DebtorCycle]:
    """Получить циклы для отчёта архива удержаний"""
    start_date = datetime.strptime(start_date_str, '%d.%m.%Y')
    end_date = datetime.strptime(end_date_str, '%d.%m.%Y')

    async with async_session() as session:
        # Для удержанных - фильтруем по deduction_date
        # Для аннулированных - фильтруем по annulled_at
        result = await session.scalars(
            select(DebtorCycle)
            .where(
                (
                    (DebtorCycle.status == 'deducted') &
                    (func.to_date(DebtorCycle.deduction_date, 'DD.MM.YYYY').between(start_date, end_date))
                ) |
                (
                    (DebtorCycle.status == 'annulled') &
                    (func.date(DebtorCycle.annulled_at).between(start_date, end_date))
                )
            )
            .options(
                selectinload(DebtorCycle.no_show_events),
                joinedload(DebtorCycle.worker).joinedload(User.security)
            )
        )
        return result.all()


async def get_workers_by_last_name_with_active_cycle(last_name: str) -> List[User]:
    """Получить исполнителей по фамилии с активным циклом (для аннулирования)"""
    async with async_session() as session:
        result = await session.scalars(
            select(User)
            .join(User.security)
            .join(User.debtor_cycles)
            .where(
                DataForSecurity.last_name.ilike(f'%{last_name}%'),
                DebtorCycle.status == 'active'
            )
            .options(joinedload(User.security))
            .distinct()
        )
        return result.all()


async def search_workers_by_lastname(lastname: str) -> List[User]:
    """Поиск работников по фамилии (для ручного добавления должников)"""
    async with async_session() as session:
        result = await session.scalars(
            select(User)
            .join(User.security)
            .where(DataForSecurity.last_name.ilike(f'%{lastname}%'))
            .options(joinedload(User.security))
            .order_by(DataForSecurity.last_name, DataForSecurity.first_name)
        )
        return result.all()


async def get_or_create_debtor_cycle(worker_id: int) -> DebtorCycle:
    """Получить активный цикл или создать новый если его нет"""
    cycle = await get_active_cycle_for_worker(worker_id=worker_id)
    if cycle:
        return cycle
    return await create_debtor_cycle(worker_id=worker_id)
