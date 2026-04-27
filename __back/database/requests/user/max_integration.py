from database import User, Verification, async_session
from sqlalchemy import select, update
from typing import Optional


async def get_worker_by_max_id(max_id: int) -> Optional[User]:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(User.max_id == max_id).limit(1)
        )


async def update_worker_max_id(
        worker_id: int,
        max_id: int,
        max_chat_id: int | None = None,
) -> None:
    async with async_session() as session:
        values = {'max_id': max_id}
        if max_chat_id is not None:
            values['max_chat_id'] = max_chat_id
        await session.execute(
            update(User)
            .where(User.id == worker_id)
            .values(**values)
        )
        await session.commit()


async def get_user_by_max_id(max_id: int) -> Optional[User]:
    return await get_worker_by_max_id(max_id)


async def set_verification_code_max(
        worker_id: int,
        max_id: int,
        code_hash: str,
        salt: str
) -> int:
    async with async_session() as session:
        new_code = Verification(
            worker_id=worker_id,
            tg_id=0,
            max_id=max_id,
            code_hash=code_hash,
            salt=salt
        )
        session.add(new_code)
        await session.commit()
        await session.refresh(new_code)
        return new_code.id


async def get_workers_max_id():
    async with async_session() as session:
        workers = await session.scalars(
            select(User.max_id).where(User.max_id != 0)
        )
        return workers.all()


async def erase_worker_max_id(worker_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == worker_id)
            .values(max_id=0, max_chat_id=0)
        )
        await session.commit()


async def set_user_max(
        max_id: int,
        username: Optional[str],
        phone_number: str,
        city: str,
        first_name: str,
        middle_name: str,
        last_name: str,
        inn: str,
        real_phone_number: str,
        real_first_name: str,
        real_last_name: str,
        real_middle_name: str,
        max_chat_id: int = 0,
) -> int:
    from database import DataForSecurity, UserRating, UserRegisteredAt
    from datetime import datetime

    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.max_id == max_id)
        )
        user_by_phone = await session.scalar(
            select(User).where(User.phone_number == phone_number)
        )

        if not user or not user_by_phone:
            new_user = User(
                max_id=max_id,  # Max ID вместо tg_id
                max_chat_id=max_chat_id,
                tg_id=0,  # Оставляем tg_id = 0 для совместимости
                username=username,
                phone_number=phone_number,
                city=city,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                inn=inn
            )
            session.add(new_user)

            session.add(
                DataForSecurity(
                    phone_number=real_phone_number,
                    first_name=real_first_name,
                    last_name=real_last_name,
                    middle_name=real_middle_name,
                    user=new_user
                )
            )

            session.add(
                UserRegisteredAt(
                    date=datetime.now().strftime('%d.%m.%Y'),
                    user=new_user
                )
            )

            session.add(UserRating(user=new_user))

            await session.commit()
            await session.refresh(new_user)
            return new_user.id


async def update_data_for_security_max(
        max_id: int,
        phone_number: str,
        first_name: str,
        last_name: str,
        middle_name: str
) -> None:
    from database import DataForSecurity

    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.max_id == max_id)
        )

        if user:
            await session.execute(
                update(DataForSecurity)
                .where(DataForSecurity.user_id == user.id)
                .values(
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name
                )
            )
            await session.commit()
