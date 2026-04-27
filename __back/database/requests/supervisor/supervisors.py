from database import Supervisor, async_session
from sqlalchemy import select, delete
from typing import List


async def set_supervisor(
        tg_id: int,
        full_name: str
) -> None:
    async with async_session() as session:
        session.add(
            Supervisor(
                full_name=full_name,
                tg_id=tg_id
            )
        )
        await session.commit()


async def get_supervisors_tg_id() -> List[int]:
    async with async_session() as session:
        tg_ids = await session.scalars(
            select(Supervisor.tg_id)
        )
        return tg_ids.all()


async def get_supervisors() -> List[Supervisor]:
    async with async_session() as session:
        managers_id = await session.scalars(
            select(Supervisor)
        )
        return managers_id.all()


async def get_supervisor(
        supervisor_id: int
) -> Supervisor:
    async with async_session() as session:
        return await session.scalar(
            select(Supervisor).where(
                Supervisor.id == supervisor_id
            )
        )


async def delete_supervisor(
        supervisor_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(Supervisor).where(
                Supervisor.id == supervisor_id
            )
        )
        await session.commit()
