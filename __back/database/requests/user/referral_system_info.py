from database import Referral, async_session
from sqlalchemy import select, func


async def get_referral_info(tg_id) -> list:
    async with async_session() as session:
        referrals = await session.scalar(select(func.count()).where(Referral.user == tg_id))
        bonus = await session.scalar(select(func.count()).where(Referral.user == tg_id,
                                                                Referral.bonus == True))
        return [referrals, bonus]
