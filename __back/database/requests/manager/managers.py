from database import Manager, async_session
from sqlalchemy import select, delete


async def set_manager(manager_id, manager_full_name):
    async with async_session() as session:
        session.add(Manager(manager_full_name=manager_full_name,
                            manager_id=manager_id))
        await session.commit()


async def get_managers_tg_id():
    async with async_session() as session:
        managers_id = await session.scalars(
            select(
                Manager.manager_id
            )
        )
        return managers_id.all()


async def get_manager(manager_tg_id):
    async with async_session() as session:
        return await session.scalar(select(Manager).where(Manager.manager_id == manager_tg_id))


async def get_managers():
    async with async_session() as session:
        managers = await session.scalars(select(Manager))
        return managers.all()


async def delete_manager(manager_id):
    async with async_session() as session:
        await session.execute(delete(Manager).where(Manager.manager_id == manager_id))
        await session.commit()
