from sqlalchemy.orm import joinedload

from database import User, DataForSecurity, async_session
from sqlalchemy.orm import joinedload
from sqlalchemy import select


async def get_user(tg_id) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.tg_id == tg_id
            )
        )


async def get_user_with_data_for_security(
        tg_id: int,
) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.tg_id == tg_id
            ).options(
                joinedload(User.security)
            )
        )


async def get_user_with_security_by_user_id(user_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(
            select(User)
            .where(User.id == user_id)
            .options(joinedload(User.security))
        )


async def get_user_id_by_real_full_name(
        last_name: str,
        first_name: str,
        middle_name: str
) -> int:
    async with async_session() as session:
        return await session.scalar(
            select(DataForSecurity.user_id).where(
                DataForSecurity.first_name == first_name,
                DataForSecurity.last_name == last_name,
                DataForSecurity.middle_name == middle_name
            )
        )


async def get_user_by_api_id(
        api_id: int,
) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.api_id == api_id,
            )
        )


async def get_all_confirmed_smz_workers() -> list:
    async with async_session() as session:
        result = await session.scalars(
            select(User).where(User.smz_status == 'confirmed')
        )
        return result.all()
