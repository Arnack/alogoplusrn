from database import Customer, PlatformEmail, EmailLog, async_session
from sqlalchemy import select, update, desc
from typing import Optional
from datetime import datetime, timedelta


async def get_customer_email_settings(customer_id: int) -> tuple[Optional[str], bool]:
    """
    Получает настройки email заказчика

    Returns:
        tuple: (email_addresses, email_sending_enabled)
    """
    async with async_session() as session:
        customer = await session.scalar(
            select(Customer).where(Customer.id == customer_id)
        )
        if customer:
            return customer.email_addresses, customer.email_sending_enabled
        return None, False


async def update_customer_email_addresses(customer_id: int, email_addresses: str):
    """Обновляет email адреса заказчика"""
    async with async_session() as session:
        await session.execute(
            update(Customer).where(Customer.id == customer_id).values(
                email_addresses=email_addresses
            )
        )
        await session.commit()


async def toggle_customer_email_sending(customer_id: int, enabled: bool):
    """Включает или выключает отправку email для заказчика"""
    async with async_session() as session:
        await session.execute(
            update(Customer).where(Customer.id == customer_id).values(
                email_sending_enabled=enabled
            )
        )
        await session.commit()


async def get_platform_emails() -> Optional[str]:
    """Получает внутренние email адреса платформы"""
    async with async_session() as session:
        platform_email = await session.scalar(
            select(PlatformEmail).where(PlatformEmail.id == 1)
        )
        if platform_email:
            return platform_email.email_addresses
        return None


async def update_platform_emails(email_addresses: str):
    """Обновляет внутренние email адреса платформы"""
    async with async_session() as session:
        platform_email = await session.scalar(
            select(PlatformEmail).where(PlatformEmail.id == 1)
        )

        if platform_email:
            await session.execute(
                update(PlatformEmail).where(PlatformEmail.id == 1).values(
                    email_addresses=email_addresses
                )
            )
        else:
            session.add(
                PlatformEmail(
                    email_addresses=email_addresses
                )
            )
        await session.commit()


async def log_email_sending(
    order_id: int,
    order_date: str,
    shift: str,
    work_cycle: int,
    email_type: str,
    recipients: str,
    status: str,
    error_message: Optional[str] = None
):
    """Логирует отправку email"""
    async with async_session() as session:
        session.add(
            EmailLog(
                order_id=order_id,
                order_date=order_date,
                shift=shift,
                work_cycle=work_cycle,
                email_type=email_type,
                recipients=recipients,
                status=status,
                error_message=error_message
            )
        )
        await session.commit()


async def check_email_already_sent(
    order_id: int,
    order_date: str,
    shift: str,
    work_cycle: int
) -> bool:
    """
    Проверяет, было ли уже отправлено письмо для данной комбинации

    Returns:
        bool: True если письмо уже было отправлено, False иначе
    """
    async with async_session() as session:
        result = await session.scalar(
            select(EmailLog).where(
                EmailLog.order_id == order_id,
                EmailLog.order_date == order_date,
                EmailLog.shift == shift,
                EmailLog.work_cycle == work_cycle,
                EmailLog.status == 'OK'
            )
        )
        return result is not None


async def check_last_email_sent_time(
    order_id: int,
    order_date: str,
    shift: str,
    min_interval_minutes: int = 2
) -> tuple[bool, Optional[datetime]]:
    """
    Проверяет время последней отправки письма для заявки

    Args:
        order_id: ID заявки
        order_date: Дата заявки
        shift: Смена (Д или Н)
        min_interval_minutes: Минимальный интервал между отправками в минутах

    Returns:
        tuple: (можно отправлять: bool, время последней отправки: Optional[datetime])
    """
    async with async_session() as session:
        last_email = await session.scalar(
            select(EmailLog)
            .where(
                EmailLog.order_id == order_id,
                EmailLog.order_date == order_date,
                EmailLog.shift == shift,
                EmailLog.status == 'OK'
            )
            .order_by(desc(EmailLog.sent_at))
        )

        if last_email is None:
            return True, None

        # Вычисляем время, прошедшее с последней отправки
        time_since_last_send = datetime.now() - last_email.sent_at
        min_interval = timedelta(minutes=min_interval_minutes)

        can_send = time_since_last_send >= min_interval
        return can_send, last_email.sent_at
