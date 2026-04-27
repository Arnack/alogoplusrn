from database import ChangeCity, async_session
from sqlalchemy import select, update


async def set_change_city_request(
        worker_id: int
) -> int:
    async with async_session() as session:
        new_request = ChangeCity(
            worker_id=worker_id
        )
        session.add(new_request)
        await session.commit()
        await session.refresh(new_request)
        return new_request.id


async def get_change_city_request(
        request_id: int
) -> ChangeCity:
    async with async_session() as session:
        return await session.scalar(
            select(ChangeCity).where(
                ChangeCity.id == request_id
            )
        )


async def complete_change_city_request(
        request_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(ChangeCity).where(
                ChangeCity.id == request_id
            ).values(
                changed=True
            )
        )
        await session.commit()
