import logging

from database import DataForSecurity, User, async_session
from sqlalchemy import select, update


async def get_data_for_security(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return await session.scalar(select(DataForSecurity).where(DataForSecurity.user_id == user.id))


async def update_data_for_security(tg_id, phone_number, first_name, last_name, middle_name):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        await session.execute(update(DataForSecurity).where(DataForSecurity.user_id == user.id).values(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name))
        await session.commit()


async def update_data_for_security_by_user_id(
    user_id: int,
    phone_number: str,
    first_name: str,
    last_name: str,
    middle_name: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(DataForSecurity)
            .where(DataForSecurity.user_id == user_id)
            .values(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
            )
        )
        await session.commit()


async def update_passport_data(
        tg_id: int,
        passport_series: str,
        passport_number: str,
        passport_issue_date: str,
        passport_department_code: str,
        passport_issued_by: str,
        gender: str = None,
) -> None:
    passport_complete = all([
        passport_series, passport_number,
        passport_issue_date, passport_department_code, passport_issued_by,
    ])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return
        await session.execute(
            update(DataForSecurity).where(DataForSecurity.user_id == user.id).values(
                passport_series=passport_series,
                passport_number=passport_number,
                passport_issue_date=passport_issue_date,
                passport_department_code=passport_department_code,
                passport_issued_by=passport_issued_by,
            )
        )
        user_values = {'passport_data_complete': passport_complete}
        if gender:
            user_values['gender'] = gender
        await session.execute(update(User).where(User.id == user.id).values(**user_values))
        await session.commit()


async def sync_worker_data_from_rr(
    user_id: int,
    card: str | None,
    passport_series: str | None,
    passport_number: str | None,
    passport_issue_date: str | None,
) -> bool:
    try:
        async with async_session() as session:
            security_values = {}
            if passport_series:
                security_values['passport_series'] = passport_series
            if passport_number:
                security_values['passport_number'] = passport_number
            if passport_issue_date:
                security_values['passport_issue_date'] = passport_issue_date
            if security_values:
                await session.execute(
                    update(DataForSecurity)
                    .where(DataForSecurity.user_id == user_id)
                    .values(**security_values)
                )
            if card:
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(card=card)
                )
            if not security_values and not card:
                return False
            await session.commit()
            return True
    except Exception as e:
        logging.exception(f'[sync_worker_data_from_rr] user_id={user_id}: {e}')
        return False
