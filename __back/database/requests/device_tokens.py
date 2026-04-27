from __future__ import annotations

from sqlalchemy import select, delete

from database import async_session
from database.models import UserDeviceToken


async def upsert_device_token(user_id: int, token: str) -> None:
    async with async_session() as session:
        existing = await session.scalar(
            select(UserDeviceToken).where(UserDeviceToken.token == token)
        )
        if existing:
            existing.user_id = user_id
        else:
            session.add(UserDeviceToken(user_id=user_id, token=token))
        await session.commit()


async def delete_device_token(token: str) -> None:
    async with async_session() as session:
        await session.execute(
            delete(UserDeviceToken).where(UserDeviceToken.token == token)
        )
        await session.commit()


async def get_device_tokens(user_id: int) -> list[str]:
    async with async_session() as session:
        rows = await session.scalars(
            select(UserDeviceToken.token).where(UserDeviceToken.user_id == user_id)
        )
        return list(rows.all())
