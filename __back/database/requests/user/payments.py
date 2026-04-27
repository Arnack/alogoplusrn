from database import OrderArchive, Registry, DataForSecurity, Payment, async_session
from sqlalchemy import select, update, func
import logging

from Schemas import WorkerChangeAmountSchema


async def set_payment(
        worker_id: int,
        order_id: int,
        amount: str,
) -> int:
    async with async_session() as session:
        payment = await session.scalar(
            select(Payment).where(
                Payment.worker_id == worker_id,
                Payment.order_id == order_id,
            )
        )
        if not payment:
            new_payment = Payment(
                worker_id=worker_id,
                order_id=order_id,
                amount=amount,
            )
            session.add(new_payment)
            await session.commit()
            await session.refresh(new_payment)
            return new_payment.id

        return payment.id


async def get_orders_for_payment(
        date: str
) -> list[OrderArchive]:
    async with async_session() as session:
        archive_orders = await session.scalars(
            select(OrderArchive).where(
                OrderArchive.date == date
            )
        )
        orders_to_return = []
        for order in archive_orders.all():
            has_payment = await session.scalar(
                select(Payment).where(
                    Payment.order_id == order.order_id,
                    Payment.paid == False,
                    Payment.in_wallet == False,
                    Payment.status == 'MODERATION',
                    Payment.amount != '0',
                )
            )

            results = await session.scalars(
                select(Registry).where(
                    Registry.order_id == order.order_id,
                )
            )
            results = results.all()

            if has_payment and not results:
                orders_to_return.append(order)
        return orders_to_return


async def get_payments(
        order_id: int
) -> list[dict]:
    async with async_session() as session:
        payments = await session.scalars(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.paid == False,
                Payment.in_wallet == False,
                Payment.amount != '0',
            )
        )
        workers = []
        for payment in payments.all():
            worker: DataForSecurity = await session.scalar(
                select(DataForSecurity).where(
                    DataForSecurity.user_id == payment.worker_id
                )
            )
            workers.append({
                'full_name': f'{worker.last_name} {worker.first_name} {worker.middle_name}',
                'amount': payment.amount,
            })
        return workers


async def set_payment_paid_true(
        order_id: int,
        worker_id: int,
) -> bool:
    async with async_session() as session:
        try:
            await session.execute(
                update(Payment).where(
                    Payment.order_id == order_id,
                    Payment.worker_id == worker_id,
                ).values(
                    paid=True,
                    status='success'
                )
            )
            await session.commit()
            return True
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            await session.execute(
                update(Payment).where(
                    Payment.order_id == order_id,
                    Payment.worker_id == worker_id,
                ).values(
                    status='ERROR'
                )
            )
            await session.commit()
            return False


async def set_payment_status_error(
        worker_id: int,
        order_id: int,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Payment).where(
                Payment.order_id == order_id,
                Payment.worker_id == worker_id,
            ).values(
                status='ERROR'
            )
        )
        await session.commit()


async def get_payment_counts(
        order_id: int,
) -> tuple:
    async with (async_session() as session):
        try:
            successful_payments_count = await session.scalar(
                select(func.count()).where(
                    Payment.order_id == order_id,
                    Payment.paid == True,
                )
            )
            total_payments_count = await session.scalar(
                select(func.count()).where(
                    Payment.order_id == order_id,
                )
            )
            return successful_payments_count, total_payments_count
        except Exception as e:
            logging.exception(f'\n\n{e}')
            return None, None


async def workers_for_change_payment_amounts(
        order_id: int,
) -> list[WorkerChangeAmountSchema]:
    async with async_session() as session:
        payments = await session.scalars(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.paid == False,
                Payment.in_wallet == False,
                Payment.amount != '0',
            )
        )
        workers = []
        for payment in payments.all():
            worker_real_data: DataForSecurity = await session.scalar(
                    select(DataForSecurity).where(
                        DataForSecurity.user_id == payment.worker_id
                    )
                )
            workers.append(
                WorkerChangeAmountSchema(
                    payment_id=payment.id,
                    full_name=f'{worker_real_data.last_name} {worker_real_data.first_name} {worker_real_data.middle_name}',
                    old_amount=payment.amount,
                )
            )
        return workers


async def update_payment_amounts(
        workers: list[WorkerChangeAmountSchema],
) -> bool:
    async with async_session() as session:
        try:
            for worker in workers:
                await session.execute(
                    update(Payment).where(
                        Payment.id == worker.payment_id
                    ).values(
                        amount=worker.new_amount,
                    )
                )
            await session.commit()
            return True
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            return False

