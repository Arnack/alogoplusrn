from database import Accountant, async_session
from sqlalchemy import select, delete


async def set_accountant(
        tg_id: int,
        full_name: str
) -> None:
    async with async_session() as session:
        session.add(
            Accountant(
                full_name=full_name,
                tg_id=tg_id
            )
        )
        await session.commit()


async def get_accountants_tg_id() -> list[int]:
    async with async_session() as session:
        tg_ids = await session.scalars(
            select(Accountant.tg_id)
        )
        return tg_ids.all()


async def get_accountants() -> list[Accountant]:
    async with async_session() as session:
        managers_id = await session.scalars(
            select(Accountant)
        )
        return managers_id.all()


async def get_accountant(
        accountant_id: int
) -> Accountant:
    async with async_session() as session:
        return await session.scalar(
            select(Accountant).where(
                Accountant.id == accountant_id
            )
        )


async def get_accountant_by_tg_id(
        tg_id: int
) -> Accountant | None:
    async with async_session() as session:
        return await session.scalar(
            select(Accountant).where(
                Accountant.tg_id == tg_id
            )
        )


async def delete_accountant(
        accountant_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(Accountant).where(
                Accountant.id == accountant_id
            )
        )
        await session.commit()


async def get_all_accountants() -> list[Accountant]:
    """Получить всех кассиров (алиас для get_accountants)"""
    return await get_accountants()
