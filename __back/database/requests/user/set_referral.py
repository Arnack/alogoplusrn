from database import Referral, Settings, User, async_session
from sqlalchemy import select, update


async def set_ref(referral_tg_id, user_id):
    async with async_session() as session:
        ref = await session.scalar(select(Referral).where(Referral.referral == referral_tg_id))

        if not ref:
            user = await session.scalar(select(User).where(User.tg_id == referral_tg_id))
            if not user:
                session.add(Referral(user=user_id, referral=referral_tg_id))
                await session.commit()


async def is_referral(worker_id):
    async with async_session() as session:
        tg_id = await session.scalar(select(User.tg_id).where(User.id == worker_id))
        return await session.scalar(select(Referral).where(Referral.referral == tg_id))


async def get_referral(worker_id):
    async with async_session() as session:
        tg_id = await session.scalar(select(User.tg_id).where(User.id == worker_id))
        return await session.scalar(select(Referral).where(Referral.referral == tg_id))


async def update_shifts_for_referral(worker_id):
    async with async_session() as session:
        tg_id = await session.scalar(select(User.tg_id).where(User.id == worker_id))
        ref_shifts = await session.scalar(select(Referral.shifts_referral).where(Referral.referral == tg_id))
        ref_shifts += 1

        ref_settings = await session.scalar(select(Settings).where(Settings.id == 1))
        if ref_shifts >= ref_settings.shifts:
            await session.execute(update(Referral).where(Referral.referral == tg_id).values(bonus=True))

        await session.execute(update(Referral).where(Referral.referral == tg_id).values(shifts_referral=ref_shifts))
        await session.commit()
