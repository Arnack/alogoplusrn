from database import Settings, async_session
from sqlalchemy import update


async def update_reg_pic(
        pic_id: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Settings).where(
                Settings.id == 1
            ).values(
                registration_pic=pic_id
            )
        )
        await session.commit()


async def update_rr_manual_pic(
        pic_id: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Settings).where(
                Settings.id == 1
            ).values(
                rr_manual_pic=pic_id
            )
        )
        await session.commit()


async def update_smz_pic(pic_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Settings).where(Settings.id == 1).values(smz_pic=pic_id)
        )
        await session.commit()


async def update_rr_partner_pic(pic_id: str) -> None:
    async with async_session() as session:
        await session.execute(
            update(Settings).where(Settings.id == 1).values(rr_partner_pic=pic_id)
        )
        await session.commit()
