from sqlalchemy import select, update
from typing import Optional, Dict, Any

from database.models import Receipt, async_session


async def create_receipt(act_id: int, worker_id: int, url: str) -> Receipt:
    async with async_session() as session:
        receipt = Receipt(
            act_id=act_id,
            worker_id=worker_id,
            url=url,
        )
        session.add(receipt)
        await session.commit()
        await session.refresh(receipt)
        return receipt


async def get_receipt_by_act(act_id: int) -> Optional[Receipt]:
    async with async_session() as session:
        return await session.scalar(
            select(Receipt).where(Receipt.act_id == act_id)
        )


async def get_receipt(receipt_id: int) -> Optional[Receipt]:
    async with async_session() as session:
        return await session.scalar(
            select(Receipt).where(Receipt.id == receipt_id)
        )


async def set_receipt_file_path(receipt_id: int, file_path: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Receipt).where(Receipt.id == receipt_id).values(file_path=file_path)
        )
        await session.commit()


async def update_receipt_url(receipt_id: int, url: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Receipt).where(Receipt.id == receipt_id).values(url=url)
        )
        await session.commit()


async def get_receipt_with_act(act_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает чек вместе с данными акта и работника для выплаты.

    Returns:
        dict с receipt, act, worker данными или None
    """
    from sqlalchemy.orm import selectinload
    from database.models import WorkerAct, User

    async with async_session() as session:
        receipt = await session.scalar(
            select(Receipt)
            .where(Receipt.act_id == act_id)
            .options(
                selectinload(Receipt.act).selectinload(WorkerAct.worker),
            )
        )

        if not receipt:
            return None

        act = receipt.act
        worker = act.worker

        return {
            'receipt': receipt,
            'act': act,
            'worker': worker,
            'receipt_url': receipt.url,
            'card_snapshot': act.card_snapshot,
            'inn': worker.inn,
            'amount': act.amount,
        }
