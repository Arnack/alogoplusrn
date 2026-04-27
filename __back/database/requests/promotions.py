from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from database.models import (
    Promotion,
    PromotionBonus,
    PromotionParticipation,
    OrderWorkerArchive,
    Order,
    OrderArchive,
    async_session,
)

logger = logging.getLogger(__name__)


# ─── Создание / чтение акций ────────────────────────────────────────────────

async def create_promotion(
    customer_id: int,
    type: str,
    name: str,
    description: str,
    n_orders: int,
    period_days: Optional[int],
    bonus_amount: int,
    city: str,
) -> Promotion:
    async with async_session() as session:
        promo = Promotion(
            customer_id=customer_id,
            type=type,
            name=name,
            description=description,
            n_orders=n_orders,
            period_days=period_days,
            bonus_amount=bonus_amount,
            city=city,
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)
        return promo


async def get_active_promotions_by_city(city: str) -> List[Promotion]:
    async with async_session() as session:
        result = await session.scalars(
            select(Promotion).where(Promotion.is_active == True, Promotion.city == city)
        )
        return result.all()


async def get_active_promotions_by_customer(customer_id: int) -> List[Promotion]:
    async with async_session() as session:
        result = await session.scalars(
            select(Promotion).where(
                Promotion.customer_id == customer_id,
                Promotion.is_active == True,
            )
        )
        return result.all()


async def get_promotion_by_id(promotion_id: int) -> Optional[Promotion]:
    async with async_session() as session:
        return await session.get(Promotion, promotion_id)


async def deactivate_promotion(promotion_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(Promotion).where(Promotion.id == promotion_id).values(is_active=False)
        )
        await session.commit()


# ─── Участие ────────────────────────────────────────────────────────────────

async def get_active_participation(
    worker_id: int, promotion_id: int
) -> Optional[PromotionParticipation]:
    async with async_session() as session:
        return await session.scalar(
            select(PromotionParticipation).where(
                PromotionParticipation.worker_id == worker_id,
                PromotionParticipation.promotion_id == promotion_id,
                PromotionParticipation.status == 'active',
            )
        )


async def get_worker_participations(worker_id: int) -> List[PromotionParticipation]:
    async with async_session() as session:
        result = await session.scalars(
            select(PromotionParticipation).where(
                PromotionParticipation.worker_id == worker_id,
                PromotionParticipation.status == 'active',
            ).options(selectinload(PromotionParticipation.promotion))
        )
        return result.all()


async def join_promotion(worker_id: int, promotion_id: int) -> PromotionParticipation:
    """Создаёт запись участия. Если уже есть активная — возвращает её."""
    existing = await get_active_participation(worker_id, promotion_id)
    if existing:
        return existing

    promo = await get_promotion_by_id(promotion_id)
    async with async_session() as session:
        now = datetime.now()
        part = PromotionParticipation(
            promotion_id=promotion_id,
            worker_id=worker_id,
            started_at=now,
            period_start_at=now if promo and promo.type == 'period' else None,
        )
        session.add(part)
        await session.commit()
        await session.refresh(part)
        return part


async def cancel_all_participations(worker_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(PromotionParticipation).where(
                PromotionParticipation.worker_id == worker_id,
                PromotionParticipation.status == 'active',
            ).values(status='cancelled', current_streak=0, period_completed=0)
        )
        await session.commit()


# ─── Бонусы ─────────────────────────────────────────────────────────────────

async def record_promotion_bonus(
    participation_id: int,
    worker_id: int,
    promotion_name: str,
    amount: int,
) -> PromotionBonus:
    async with async_session() as session:
        bonus = PromotionBonus(
            participation_id=participation_id,
            worker_id=worker_id,
            promotion_name=promotion_name,
            amount=amount,
        )
        session.add(bonus)
        await session.commit()
        await session.refresh(bonus)
        return bonus


async def get_worker_bonuses(worker_id: int) -> List[PromotionBonus]:
    async with async_session() as session:
        result = await session.scalars(
            select(PromotionBonus).where(PromotionBonus.worker_id == worker_id)
            .order_by(PromotionBonus.accrued_at.desc())
        )
        return result.all()


async def get_bonuses_by_customer_period(
    customer_id: int,
    date_from: datetime,
    date_to: datetime,
) -> list:
    """Возвращает бонусы по акциям данного получателя услуг за период."""
    async with async_session() as session:
        result = await session.execute(
            select(PromotionBonus, PromotionParticipation, Promotion)
            .join(PromotionParticipation, PromotionBonus.participation_id == PromotionParticipation.id)
            .join(Promotion, PromotionParticipation.promotion_id == Promotion.id)
            .where(
                Promotion.customer_id == customer_id,
                PromotionBonus.accrued_at >= date_from,
                PromotionBonus.accrued_at <= date_to,
            )
            .order_by(PromotionBonus.accrued_at)
        )
        return result.all()


# ─── Логика прогресса ────────────────────────────────────────────────────────

def _is_successful_order(archive_worker: OrderWorkerArchive) -> bool:
    """Заявка считается успешной если worker_hours >= 0.5, статус EXTRA или отклонён модератором."""
    if archive_worker.status == 'EXTRA':
        return True
    try:
        hours = float(archive_worker.worker_hours or 0)
        if hours >= 0.5:
            return True
    except (ValueError, TypeError):
        pass
    return False


async def check_and_process_promotion_progress(
    worker_id: int,
    customer_id: int,
    archive_order_worker: OrderWorkerArchive,
    bot,
) -> None:
    """
    Вызывается при архивации заявки. Обновляет прогресс по акциям.
    bot — объект aiogram Bot для отправки уведомлений.
    """
    from database.models import User
    async with async_session() as session:
        worker = await session.get(User, worker_id)

    if not worker:
        return

    # Получаем город исполнителя для поиска акций
    city = worker.city

    # Находим активные акции для этого получателя услуг в городе исполнителя
    async with async_session() as session:
        promos_result = await session.scalars(
            select(Promotion).where(
                Promotion.customer_id == customer_id,
                Promotion.is_active == True,
                Promotion.city == city,
            )
        )
        promos = promos_result.all()

    if not promos:
        return

    is_success = _is_successful_order(archive_order_worker)
    is_not_out = archive_order_worker.status == 'NOT_OUT'

    for promo in promos:
        part = await get_active_participation(worker_id, promo.id)
        if not part:
            continue

        if promo.type == 'streak':
            await _process_streak(part, promo, is_success, is_not_out, worker, bot)
        elif promo.type == 'period':
            await _process_period(part, promo, is_success, worker, bot)


async def _process_streak(
    part: PromotionParticipation,
    promo: Promotion,
    is_success: bool,
    is_not_out: bool,
    worker,
    bot,
) -> None:
    if is_not_out:
        # Обнуляем серию
        async with async_session() as session:
            await session.execute(
                update(PromotionParticipation)
                .where(PromotionParticipation.id == part.id)
                .values(current_streak=0)
            )
            await session.commit()
        # Уведомление
        if worker.tg_id:
            try:
                await bot.send_message(
                    chat_id=worker.tg_id,
                    text=(
                        f'⚠️ Уведомление\n\n'
                        f'Вы приняли заявку, но не приступили к оказанию услуг.\n\n'
                        f'❌ Прогресс по акции «{promo.name}» аннулирован.\n\n'
                        f'Серия начинается заново.'
                    ),
                )
            except Exception as e:
                logger.warning('[promotion] Ошибка отправки уведомления NOT_OUT: %s', e)
        return

    if not is_success:
        return

    new_streak = part.current_streak + 1
    async with async_session() as session:
        await session.execute(
            update(PromotionParticipation)
            .where(PromotionParticipation.id == part.id)
            .values(current_streak=new_streak)
        )
        await session.commit()

    if new_streak >= promo.n_orders:
        # Начисляем бонус и сбрасываем серию
        total_bonus = promo.n_orders * promo.bonus_amount
        await record_promotion_bonus(
            participation_id=part.id,
            worker_id=part.worker_id,
            promotion_name=promo.name,
            amount=total_bonus,
        )
        async with async_session() as session:
            await session.execute(
                update(PromotionParticipation)
                .where(PromotionParticipation.id == part.id)
                .values(current_streak=0, cycles_completed=part.cycles_completed + 1)
            )
            await session.commit()
        # Уведомление о завершении
        if worker.tg_id:
            try:
                await bot.send_message(
                    chat_id=worker.tg_id,
                    text=(
                        f'🎉 Поздравляем!\n\n'
                        f'Вы выполнили условия акции «{promo.name}».\n\n'
                        f'💰 Дополнительное вознаграждение: {total_bonus} ₽\n\n'
                        f'📊 Сумма учтена в ваших начислениях.'
                    ),
                )
            except Exception as e:
                logger.warning('[promotion] Ошибка отправки уведомления о завершении: %s', e)


async def _process_period(
    part: PromotionParticipation,
    promo: Promotion,
    is_success: bool,
    worker,
    bot,
) -> None:
    if not is_success:
        return

    now = datetime.now()
    period_start = part.period_start_at or part.started_at

    # Проверяем не истёк ли период
    if promo.period_days and (now - period_start).days > promo.period_days:
        # Период истёк без выполнения — начинаем новый
        async with async_session() as session:
            await session.execute(
                update(PromotionParticipation)
                .where(PromotionParticipation.id == part.id)
                .values(period_start_at=now, period_completed=1)
            )
            await session.commit()
        return

    new_completed = part.period_completed + 1
    async with async_session() as session:
        await session.execute(
            update(PromotionParticipation)
            .where(PromotionParticipation.id == part.id)
            .values(period_completed=new_completed)
        )
        await session.commit()

    if new_completed >= promo.n_orders:
        # Условие выполнено — начисляем бонус досрочно / в срок
        total_bonus = promo.n_orders * promo.bonus_amount
        await record_promotion_bonus(
            participation_id=part.id,
            worker_id=part.worker_id,
            promotion_name=promo.name,
            amount=total_bonus,
        )
        # Начинаем новый период
        async with async_session() as session:
            await session.execute(
                update(PromotionParticipation)
                .where(PromotionParticipation.id == part.id)
                .values(
                    period_start_at=now,
                    period_completed=0,
                    cycles_completed=part.cycles_completed + 1,
                )
            )
            await session.commit()
        # Уведомление
        if worker.tg_id:
            try:
                await bot.send_message(
                    chat_id=worker.tg_id,
                    text=(
                        f'🎉 Поздравляем!\n\n'
                        f'Вы выполнили условия акции «{promo.name}».\n\n'
                        f'💰 Дополнительное вознаграждение: {total_bonus} ₽\n\n'
                        f'📊 Сумма учтена в ваших начислениях.'
                    ),
                )
            except Exception as e:
                logger.warning('[promotion] Ошибка отправки уведомления period: %s', e)


async def check_streak_skips_for_date(order_date: str, bot) -> None:
    """
    Ежедневная проверка пропусков (для streak-акций).
    Если у Получателя услуг были заявки на дату, и исполнитель с активным участием
    не принял ни одну — серия обнуляется.
    """
    async with async_session() as session:
        # Находим все заявки за дату в архиве
        archive_orders_result = await session.scalars(
            select(OrderArchive).where(OrderArchive.date == order_date)
        )
        archive_orders = archive_orders_result.all()

    for arch_order in archive_orders:
        customer_id = arch_order.customer_id

        # Активные streak-акции для этого получателя
        async with async_session() as session:
            promos_result = await session.scalars(
                select(Promotion).where(
                    Promotion.customer_id == customer_id,
                    Promotion.type == 'streak',
                    Promotion.is_active == True,
                )
            )
            promos = promos_result.all()

        if not promos:
            continue

        # Кто принял заявки в этот день
        async with async_session() as session:
            worked_result = await session.scalars(
                select(OrderWorkerArchive.worker_id).where(
                    OrderWorkerArchive.archive_order_id == arch_order.id,
                    OrderWorkerArchive.status.in_(['WORKED', 'EXTRA']),
                )
            )
            worked_worker_ids = set(worked_result.all())

        for promo in promos:
            # Участники акции в этом городе
            async with async_session() as session:
                parts_result = await session.scalars(
                    select(PromotionParticipation).where(
                        PromotionParticipation.promotion_id == promo.id,
                        PromotionParticipation.status == 'active',
                    ).options(selectinload(PromotionParticipation.worker))
                )
                parts = parts_result.all()

            for part in parts:
                if part.worker_id not in worked_worker_ids:
                    # Пропуск — обнуляем серию
                    async with async_session() as session:
                        await session.execute(
                            update(PromotionParticipation)
                            .where(PromotionParticipation.id == part.id)
                            .values(current_streak=0)
                        )
                        await session.commit()
                    # Уведомление
                    if part.worker and part.worker.tg_id:
                        try:
                            from database.models import Customer
                            async with async_session() as s2:
                                customer = await s2.get(Customer, customer_id)
                            customer_name = customer.organization if customer else str(customer_id)
                            await bot.send_message(
                                chat_id=part.worker.tg_id,
                                text=(
                                    f'⚠️ Уведомление\n\n'
                                    f'{order_date} у Получателя услуг {customer_name} были размещены заявки, '
                                    f'однако вы не приняли ни одну.\n\n'
                                    f'❌ Прогресс по акции «{promo.name}» аннулирован.\n\n'
                                    f'Для продолжения участия начните серию заново.'
                                ),
                            )
                        except Exception as e:
                            logger.warning('[promotion] Ошибка уведомления о пропуске: %s', e)
