from database import User, Verification, RegCode, async_session
from sqlalchemy import select, delete, update
from typing import NoReturn


async def set_verification_code(
        worker_id: int,
        tg_id: int,
        code_hash: str,
        salt: str
) -> int:
    async with async_session() as session:
        new_code = Verification(
                worker_id=worker_id,
                tg_id=tg_id,
                code_hash=code_hash,
                salt=salt
            )
        session.add(new_code)
        await session.commit()
        await session.refresh(new_code)
        return new_code.id


async def get_code_by_id(
        code_id: str
) -> Verification:
    async with async_session() as session:
        return await session.scalar(
            select(Verification).where(
                Verification.id == code_id
            )
        )


async def delete_verification_code(
        code_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(Verification).where(
                Verification.id == code_id
            )
        )
        await session.commit()


async def update_worker_tg_id(worker_id, tg_id):
    async with async_session() as session:
        await session.execute(update(User).where(User.id == worker_id).values(tg_id=tg_id))
        await session.commit()


async def set_registration_code(
        code_hash: str,
        salt: str
) -> int:
    async with async_session() as session:
        new_code = RegCode(
            code_hash=code_hash,
            salt=salt
        )
        session.add(new_code)
        await session.commit()
        await session.refresh(new_code)
        return new_code.id


async def get_registration_code_by_id(
        code_id: str
) -> RegCode:
    async with async_session() as session:
        return await session.scalar(
            select(RegCode).where(
                RegCode.id == code_id
            )
        )


async def delete_registration_code(
        code_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            delete(RegCode).where(
                RegCode.id == code_id
            )
        )
        await session.commit()
