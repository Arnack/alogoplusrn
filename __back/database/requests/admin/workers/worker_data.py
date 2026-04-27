from database import User, async_session
from sqlalchemy import select


async def get_user_by_phone(
        phone_number: str
) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.phone_number == phone_number
            )
        )
