from database import User, Registry, Payment, DataForSecurity, async_session
from sqlalchemy import select, update
from decimal import Decimal
from typing import List
import logging

from utils.loggers.payments import write_worker_op_log


async def get_workers_with_nonzero_balance() -> List[dict]:
    """Возвращает список работников с ненулевым балансом для PDF-отчёта."""
    async with async_session() as session:
        workers = (await session.scalars(select(User))).all()
        result = []
        for w in workers:
            balance = Decimal(w.balance.replace(',', '.')) if w.balance else Decimal('0')
            if balance == 0:
                continue
            real = await session.scalar(
                select(DataForSecurity).where(DataForSecurity.user_id == w.id)
            )
            real_fio = f'{real.last_name} {real.first_name} {real.middle_name}' if real else ''
            result.append({
                'fio': f'{w.last_name} {w.first_name} {w.middle_name or ""}',
                'real_fio': real_fio,
                'phone': w.phone_number or '',
                'balance': f'{balance:,.2f}',
                'balance_val': float(balance),
            })
        result.sort(key=lambda x: x['fio'])
        return result


async def get_worker_balance_by_tg_id(
        tg_id: int,
) -> Decimal:
    async with async_session() as session:
        balance: str = await session.scalar(
            select(User.balance).where(User.tg_id == tg_id)
        )
        return Decimal(balance.replace(',', '.')) if balance else Decimal('0')


async def update_worker_balance_by_tg_id_op(
        tg_id: int,
        order_id: int,
) -> dict:
    async with async_session() as session:
        try:
            worker: User = await session.scalar(
                select(User).where(
                    User.tg_id == tg_id
                )
            )
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {tg_id} | Заказ №{order_id} | Старый баланс: {worker.balance}',
            )
            registry: Registry = await session.scalar(
                select(Registry.registry_id).where(
                    Registry.order_id == order_id,
                )
            )
            payment: Payment = await session.scalar(
                select(Payment).where(
                    Payment.order_id == order_id,
                    Payment.worker_id == worker.id,
                )
            )
            if registry:
                return {
                    'success': True,
                    'payment_error': True,
                    'reason': '❗Невозможно отправить вознаграждение, так как уже создан платежный реестр'
                }
            if payment.in_wallet:
                return {
                    'success': True,
                    'payment_error': True,
                    'reason': '❗Невозможно отправить вознаграждение, так как оно уже зачислено на ваш баланс'
                }
            if payment.paid:
                return {
                    'success': True,
                    'payment_error': True,
                    'reason': '❗Невозможно отправить вознаграждение, так как оно уже было выполнено'
                }
            if payment.status == 'ERROR':
                return {
                    'success': True,
                    'payment_error': True,
                    'reason': '❗Невозможно отправить вознаграждение. Так как ранее оно уже было создано, но произошла ошибка'
                }

            if not payment.in_wallet and not payment.paid and payment.status != 'ERROR':
                new_balance = str(Decimal(worker.balance) + Decimal(payment.amount))
                worker.balance = new_balance
                payment.in_wallet = True
                payment.notification_confirmed = True
                payment.status = 'success'
                await session.commit()
                write_worker_op_log(
                    message=f'Исполнитель (tg_id) {tg_id} | Заказ №{order_id} | Новый баланс: {new_balance}',
                )
                return {
                    'success': True,
                    'payment_error': False,
                    'reason': ''
                }
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {tg_id} | Заказ №{order_id} | Баланс не изменен',
            )
            return {
                'success': True,
                'payment_error': False,
                'reason': ''
            }
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {tg_id} | Заказ №{order_id} | Баланс не изменен',
            )
            return {
                'success': False,
                'payment_error': False,
                'reason': ''
            }


async def update_worker_balance_op(
        worker_id: int,
        payment_id: int,
):
    async with async_session() as session:
        try:
            worker: User = await session.scalar(
                select(User).where(
                    User.id == worker_id,
                )
            )
            write_worker_op_log(
                message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Старый баланс: {worker.balance}',
            )
            payment: Payment = await session.scalar(
                select(Payment).where(
                    Payment.id == payment_id,
                )
            )
            if payment.in_wallet:
                write_worker_op_log(
                    message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Невозможно отправить вознаграждение, так как оно уже зачислено на баланс',
                    level='ERROR',
                )
                return

            if payment.paid:
                write_worker_op_log(
                    message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Невозможно отправить вознаграждение, так как оно уже было выполнено',
                    level='ERROR',
                )
                return
            if payment.status == 'ERROR':
                write_worker_op_log(
                    message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Невозможно отправить вознаграждение. Так как ранее оно уже было создано, но произошла ошибка',
                    level='ERROR',
                )
                return

            if not payment.in_wallet and not payment.paid and payment.status != 'ERROR':
                new_balance = str(Decimal(worker.balance) + Decimal(payment.amount))
                worker.balance = new_balance
                payment.in_wallet = True
                payment.notification_confirmed = True
                payment.status = 'success'
                await session.commit()
                write_worker_op_log(
                    message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Новый баланс: {new_balance}',
                )
                return
            write_worker_op_log(
                message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Баланс не изменен',
            )
            return
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            write_worker_op_log(
                message=f'Исполнитель (ID) {worker_id} | Начисление (заявка) №{payment_id} | Баланс не изменен',
            )
            return


async def update_worker_balance(
        new_balance: str,
        tg_id: int = 0,
        worker_id: int = 0,
) -> bool:
    async with async_session() as session:
        try:
            if worker_id:
                condition = User.id == worker_id
            else:
                condition = User.tg_id == tg_id
            await session.execute(
                update(User).where(condition).values(balance=new_balance)
            )
            await session.commit()
            return True
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            return False


async def move_payment_to_wallet(worker_id: int, order_id: int) -> str | None:
    """Переводит оплату в начисления (баланс). Возвращает сумму или None при ошибке."""
    async with async_session() as session:
        try:
            worker: User = await session.scalar(select(User).where(User.id == worker_id))
            payment: Payment = await session.scalar(
                select(Payment).where(
                    Payment.order_id == order_id,
                    Payment.worker_id == worker_id,
                )
            )
            if not payment or payment.paid or payment.in_wallet:
                return None
            amount = payment.amount
            new_balance = str(Decimal(worker.balance or '0') + Decimal(amount))
            worker.balance = new_balance
            payment.in_wallet = True
            payment.notification_confirmed = True
            payment.status = 'success'
            await session.commit()
            write_worker_op_log(
                message=f'Исполнитель (ID) {worker_id} | Заказ №{order_id} | Переведено в начисления: {amount}₽',
            )
            return amount
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            return None


async def payment_set_notification_confirmed(
        order_id: int,
        tg_id: int = 0,
        worker_id: int = 0,
) -> bool:
    async with async_session() as session:
        try:
            if not worker_id:
                worker: User = await session.scalar(
                    select(User).where(
                        User.tg_id == tg_id
                    )
                )
                worker_id = worker.id if worker else None
            if not worker_id:
                logging.error(f'payment_set_notification_confirmed: worker not found tg_id={tg_id}')
                return False
            payment: Payment = await session.scalar(
                select(Payment).where(
                    Payment.order_id == order_id,
                    Payment.worker_id == worker_id,
                )
            )
            if not payment:
                logging.error(f'payment_set_notification_confirmed: payment not found order={order_id} worker={worker_id}')
                return False
            payment.notification_confirmed = True
            await session.commit()
            return True
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await session.rollback()
            return False
