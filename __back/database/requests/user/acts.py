from datetime import datetime
from types import SimpleNamespace
from sqlalchemy import select, update, text
from typing import Optional

from database.models import WorkerAct, async_session


async def _has_wallet_payment_id_column(session) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'worker_acts' AND column_name = 'wallet_payment_id'
            LIMIT 1
            """
        )
    )
    return result.scalar() == 1


def _act_from_row(row) -> SimpleNamespace:
    return SimpleNamespace(
        id=row.id,
        order_id=row.order_id,
        worker_id=row.worker_id,
        wallet_payment_id=getattr(row, 'wallet_payment_id', None),
        legal_entity_id=row.legal_entity_id,
        amount=row.amount,
        date=row.date,
        status=row.status,
        created_at=row.created_at,
        signed_at=row.signed_at,
        file_path=row.file_path,
        card_snapshot=row.card_snapshot,
    )


async def create_worker_act(
        worker_id: int,
        legal_entity_id: int,
        amount: str,
        date: str,
        order_id: int | None = None,
        wallet_payment_id: int | None = None,
        card_snapshot: str | None = None,
) -> WorkerAct:
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        params = {
            'order_id': order_id,
            'worker_id': worker_id,
            'legal_entity_id': legal_entity_id,
            'amount': amount,
            'date': date,
            'status': 'pending',
            'created_at': datetime.now(),
            'signed_at': None,
            'file_path': None,
            'card_snapshot': card_snapshot,
        }
        if has_wallet_payment_id:
            params['wallet_payment_id'] = wallet_payment_id
            query = text(
                """
                INSERT INTO worker_acts
                (order_id, worker_id, wallet_payment_id, legal_entity_id, amount, date, status, created_at, signed_at, file_path, card_snapshot)
                VALUES
                (:order_id, :worker_id, :wallet_payment_id, :legal_entity_id, :amount, :date, :status, :created_at, :signed_at, :file_path, :card_snapshot)
                RETURNING id, order_id, worker_id, wallet_payment_id, legal_entity_id, amount, date, status, created_at, signed_at, file_path, card_snapshot
                """
            )
        else:
            query = text(
                """
                INSERT INTO worker_acts
                (order_id, worker_id, legal_entity_id, amount, date, status, created_at, signed_at, file_path, card_snapshot)
                VALUES
                (:order_id, :worker_id, :legal_entity_id, :amount, :date, :status, :created_at, :signed_at, :file_path, :card_snapshot)
                RETURNING id, order_id, worker_id, legal_entity_id, amount, date, status, created_at, signed_at, file_path, card_snapshot
                """
            )
        result = await session.execute(query, params)
        await session.commit()
        return _act_from_row(result.mappings().first())


async def get_worker_act(act_id: int) -> Optional[WorkerAct]:
    async with async_session() as session:
        return await session.scalar(
            select(WorkerAct).where(WorkerAct.id == act_id)
        )


async def get_acts_by_order_worker(order_id: int, worker_id: int) -> list[WorkerAct]:
    async with async_session() as session:
        result = await session.scalars(
            select(WorkerAct).where(
                WorkerAct.order_id == order_id,
                WorkerAct.worker_id == worker_id,
            )
        )
        return list(result.all())


async def update_worker_act_status(act_id: int, status: str) -> None:
    async with async_session() as session:
        values: dict = {'status': status}
        if status in ('signed', 'auto_signed'):
            values['signed_at'] = datetime.now()
        await session.execute(
            update(WorkerAct).where(WorkerAct.id == act_id).values(**values)
        )
        await session.commit()


async def set_worker_act_file_path(act_id: int, file_path: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(WorkerAct).where(WorkerAct.id == act_id).values(file_path=file_path)
        )
        await session.commit()


async def set_worker_act_card_snapshot(act_id: int, card_snapshot: str) -> None:
    """Фиксирует номер карты в акте (п.10 ТЗ)."""
    async with async_session() as session:
        await session.execute(
            update(WorkerAct).where(WorkerAct.id == act_id).values(card_snapshot=card_snapshot)
        )
        await session.commit()


async def get_latest_receipt_required_act(worker_id: int) -> Optional[WorkerAct]:
    """Возвращает последний подписанный акт, для которого ещё не загружен чек."""
    from sqlalchemy import desc
    from database.models import Receipt

    async with async_session() as session:
        query = (
            select(WorkerAct)
            .outerjoin(Receipt, Receipt.act_id == WorkerAct.id)
            .where(
                WorkerAct.worker_id == worker_id,
                WorkerAct.status.in_(('signed', 'auto_signed')),
                Receipt.id.is_(None),
            )
            .order_by(desc(WorkerAct.created_at), desc(WorkerAct.id))
        )
        return await session.scalar(query)


async def get_wallet_payment_act(wallet_payment_id: int) -> Optional[WorkerAct]:
    async with async_session() as session:
        has_wallet_payment_id = await _has_wallet_payment_id_column(session)
        if not has_wallet_payment_id:
            return None
        query = (
            select(WorkerAct)
            .where(WorkerAct.wallet_payment_id == wallet_payment_id)
            .order_by(WorkerAct.created_at.desc(), WorkerAct.id.desc())
        )
        return await session.scalar(query)
