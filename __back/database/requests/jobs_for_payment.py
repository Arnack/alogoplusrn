from database import User, JobForPayment, async_session, Payment
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from random import randint
import logging

from Schemas import WorkerPaymentSchema
from utils.loggers import write_worker_op_log
from API.fin.workers import fin_get_worker, fin_get_worker_by_inn


def _normalize_card(value: str | None) -> str:
    return ''.join(ch for ch in (value or '') if ch.isdigit())


def _mask_card(value: str | None) -> str:
    digits = _normalize_card(value)
    if len(digits) < 4:
        return 'empty'
    return f'****{digits[-4:]}'


def _get_rr_card(rr_worker: dict | None) -> str:
    if not rr_worker:
        return ''
    return (
        rr_worker.get('bankcardNumber')
        or rr_worker.get('bankcard_number')
        or ''
    )


async def _resolve_rr_worker(api_id: int | None, inn: str | None) -> tuple[dict | None, str]:
    if api_id:
        rr_worker = await fin_get_worker(api_id)
        if rr_worker:
            return rr_worker, 'api_id'
        logging.warning('[payment-method] rr worker lookup failed by api_id=%s, trying inn=%s', api_id, inn)
    if inn:
        rr_worker = await fin_get_worker_by_inn(str(inn))
        if rr_worker:
            return rr_worker, 'inn'
    return None, 'not_found'


async def set_jobs_for_payment(
        jobs_fp: list[dict],
) -> bool:
    async with async_session() as session:
        try:
            max_id = await session.scalar(
                select(func.max(JobForPayment.id))
            )

            if not max_id:
                for job in jobs_fp:
                    session.add(
                        JobForPayment(
                            name=job["name"],
                        )
                    )
            else:
                for job in jobs_fp:
                    if job["id"] <= max_id:
                        await session.execute(
                            update(JobForPayment).where(
                                JobForPayment.id == job["id"],
                            ).values(
                                name=job["name"],
                            )
                        )
                    else:
                        session.add(
                            JobForPayment(
                                name=job["name"],
                            )
                        )

            await session.commit()
            return True
        except Exception as e:
            logging.exception(e)
            await session.rollback()
            return False



async def get_jobs_for_payment() -> list[JobForPayment]:
    async with async_session() as session:
        jobs = await session.scalars(
            select(JobForPayment)
        )
        return jobs.all()


async def get_job_fp_sequence(worker_id: int, count: int) -> list[str]:
    """Возвращает список из `count` ТЗ для отображения в поиске.

    Циклически перебирает JobForPayment начиная со следующей позиции воркера.
    Не изменяет last_job в БД.
    """
    async with async_session() as session:
        try:
            jobs = (await session.scalars(
                select(JobForPayment).order_by(JobForPayment.id)
            )).all()
            if not jobs:
                return [None] * count

            worker: User = await session.scalar(
                select(User).where(User.id == worker_id)
            )
            last_job = worker.last_job or 0
            # найти стартовый индекс в списке (next после last_job)
            ids = [j.id for j in jobs]
            # следующий id после last_job
            next_ids = [i for i in ids if i > last_job]
            start_idx = ids.index(next_ids[0]) if next_ids else 0

            result = []
            for i in range(count):
                result.append(jobs[(start_idx + i) % len(jobs)].name)
            return result
        except Exception as e:
            logging.exception(e)
            return [None] * count


async def get_job_for_wallet_payment(
        worker_id: int,
) -> str | None:
    async with async_session() as session:
        try:
            worker: User = await session.scalar(
                select(User).where(
                    User.id == worker_id,
                )
            )
            max_id = await session.scalar(
                select(func.max(JobForPayment.id))
            )
            if max_id:
                if worker.last_job:
                    new_job_id = 1 if worker.last_job + 1 > max_id else worker.last_job + 1
                    worker.last_job = new_job_id
                else:
                    new_job_id = randint(1, max_id)
                    worker.last_job = new_job_id

                await session.commit()
                return await session.scalar(
                    select(JobForPayment.name).where(
                        JobForPayment.id == new_job_id,
                    )
                )
            else:
                return None
        except Exception as e:
            logging.exception(e)
            await session.rollback()
            return None


async def get_job_fp_for_txt(
        worker_id: int,
) -> str | None:
    async with async_session() as session:
        try:
            worker: User = await session.scalar(
                select(User).where(
                    User.id == worker_id,
                )
            )
            max_id = await session.scalar(
                select(func.max(JobForPayment.id))
            )
            if max_id:
                if worker.last_job:
                    new_job_id = 1 if worker.last_job + 1 > max_id else worker.last_job + 1
                else:
                    new_job_id = randint(1, max_id)

                return await session.scalar(
                    select(JobForPayment.name).where(
                        JobForPayment.id == new_job_id,
                    )
                )
            else:
                return None
        except Exception as e:
            logging.exception(e)
            await session.rollback()
            return None


async def has_jobs_for_payment() -> bool:
    async with async_session() as session:
        return bool(
            await session.scalar(
                select(JobForPayment.id)
            )
        )


async def get_workers_for_payment(
        order_id: int,
) -> tuple[list[WorkerPaymentSchema], list[dict]] | None:
    """Возвращает (workers, skipped) или None при ошибке.

    skipped — список словарей с работниками, пропущенными из-за конфликта/отсутствия способа выплаты.
    Их Payment.paid остаётся False — они останутся в очереди до следующей выплаты.
    """
    async with async_session() as session:
        try:
            payments = await session.scalars(
                select(Payment).where(
                    Payment.order_id == order_id,
                    Payment.paid == False,
                    Payment.in_wallet == False,
                    Payment.amount != '0',
                ).options(
                    joinedload(Payment.user)
                )
            )
            max_id = await session.scalar(
                select(func.max(JobForPayment.id))
            )

            workers = []
            skipped = []
            if max_id:
                for payment in payments:
                    if payment.user.last_job:
                        new_job_id = 1 if payment.user.last_job + 1 > max_id else payment.user.last_job + 1
                        payment.user.last_job = new_job_id
                    else:
                        new_job_id = randint(1, max_id)
                        payment.user.last_job = new_job_id

                    job_fp = await session.scalar(
                        select(JobForPayment.name).where(
                            JobForPayment.id == new_job_id,
                        )
                    )
                    platform_card = _normalize_card(payment.user.card)
                    rr_worker, rr_source = await _resolve_rr_worker(
                        api_id=payment.user.api_id,
                        inn=payment.user.inn,
                    )
                    rr_card = _normalize_card(_get_rr_card(rr_worker))
                    if rr_worker and rr_source == 'inn' and not payment.user.api_id and rr_worker.get('id'):
                        payment.user.api_id = rr_worker.get('id')
                        logging.info(
                            '[payment-method] order=%s worker=%s source=rr action=sync_api_id rr_worker_id=%s',
                            order_id,
                            payment.user.id,
                            rr_worker.get('id'),
                        )

                    if not platform_card and rr_card:
                        payment.user.card = rr_card
                        platform_card = rr_card
                        logging.info(
                            '[payment-method] order=%s worker=%s source=rr action=sync_to_platform method=card rr=%s',
                            order_id,
                            payment.user.id,
                            _mask_card(rr_card),
                        )

                    if platform_card and rr_card and platform_card != rr_card:
                        old_platform_card = platform_card
                        payment.user.card = rr_card
                        platform_card = rr_card
                        logging.info(
                            '[payment-method] order=%s worker=%s source=rr action=sync_to_platform_on_mismatch '
                            'platform_old=%s rr=%s',
                            order_id,
                            payment.user.id,
                            _mask_card(old_platform_card),
                            _mask_card(rr_card),
                        )

                    skip_reason = None
                    conflict_type = None
                    if not rr_worker:
                        skip_reason = 'rr_unavailable'
                        logging.warning(
                            '[payment-method] order=%s worker=%s source=rr(%s) action=move_to_wallet '
                            'reason=worker_not_found_or_unavailable platform=%s rr=unavailable',
                            order_id,
                            payment.user.id,
                            rr_source,
                            _mask_card(platform_card),
                        )
                    elif not rr_card:
                        skip_reason = 'missing_rr'
                        logging.warning(
                            '[payment-method] order=%s worker=%s source=rr(%s) action=move_to_wallet '
                            'reason=missing_payment_method platform=%s rr=empty',
                            order_id,
                            payment.user.id,
                            rr_source,
                            _mask_card(platform_card),
                        )

                    if skip_reason:
                        skipped.append({
                            'user_id': payment.user.id,
                            'tg_id': payment.user.tg_id,
                            'max_id': payment.user.max_id,
                            'payment_id': payment.id,
                            'full_name': (
                                f'{payment.user.last_name} '
                                f'{payment.user.first_name} '
                                f'{payment.user.middle_name}'
                            ).strip(),
                            'inn': payment.user.inn,
                            'amount': payment.amount,
                            'reason': skip_reason,
                            'conflict_type': conflict_type,
                            'platform_method': {'type': 'card' if platform_card else 'none', 'card': _mask_card(platform_card)},
                            'rr_method': {
                                'type': 'card' if rr_card else ('unavailable' if not rr_worker else 'none'),
                                'card': _mask_card(rr_card) if rr_card else ('unavailable' if not rr_worker else 'empty'),
                            },
                        })
                        continue

                    if not platform_card:
                        logging.warning(
                            f'[payment] worker id={payment.user.id} '
                            f'inn={payment.user.inn} пропущен: карта не указана'
                        )
                        skipped.append({
                            'user_id': payment.user.id,
                            'tg_id': payment.user.tg_id,
                            'max_id': payment.user.max_id,
                            'payment_id': payment.id,
                            'full_name': (
                                f'{payment.user.last_name} '
                                f'{payment.user.first_name} '
                                f'{payment.user.middle_name}'
                            ).strip(),
                            'inn': payment.user.inn,
                            'amount': payment.amount,
                            'reason': 'missing_platform',
                            'conflict_type': None,
                            'platform_method': {'type': 'none', 'card': 'empty'},
                            'rr_method': {'type': 'none', 'card': 'empty'},
                        })
                        continue
                    workers.append(
                        WorkerPaymentSchema(
                            first_name=payment.user.first_name,
                            middle_name=payment.user.middle_name,
                            last_name=payment.user.last_name,
                            inn=payment.user.inn,
                            amount=payment.amount,
                            type_of_work=job_fp,
                            card_number=platform_card,
                            phone=payment.user.phone_number.lstrip('+').lstrip('7'),
                        )
                    )
                await session.commit()
                try:
                    log_workers = ''
                    for i, worker in enumerate(workers):
                        log_workers += f'{i}. {worker.inn}\n'
                    write_worker_op_log(
                        message=f'БД. Исполнители для выплаты из заказа n{order_id}\n{log_workers}',
                    )
                except:
                    pass

                return workers, skipped
            else:
                return None

        except Exception as e:
            logging.exception(e)
            await session.rollback()
            return None
