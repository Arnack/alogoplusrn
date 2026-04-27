from database import Settings, async_session, HelpLastUse
from sqlalchemy import select, update
from datetime import datetime, timedelta


async def set_help_group(
        group_chat_id: str,
) -> None:
    async with async_session() as session:
        await session.execute(
            update(Settings).where(
                Settings.id == 1
            ).values(
                help_group_chat_id=group_chat_id
            )
        )
        await session.commit()


async def can_use_help(
        worker_id: int,
) -> bool:
    async with async_session() as session:
        last_use: HelpLastUse = await session.scalar(
            select(HelpLastUse).where(
                HelpLastUse.worker_id == worker_id
            )
        )
        if not last_use or (datetime.now() - last_use.last_use > timedelta(hours=6)):
            return True
        else:
            return False




async def help_cooldown_remaining_seconds(worker_id: int) -> int | None:
    """Секунды до следующей возможной отправки SOS, либо None если сейчас можно."""
    async with async_session() as session:
        last_use: HelpLastUse | None = await session.scalar(
            select(HelpLastUse).where(HelpLastUse.worker_id == worker_id)
        )
    if not last_use:
        return None
    elapsed = datetime.now() - last_use.last_use
    limit = timedelta(hours=6)
    if elapsed >= limit:
        return None
    return max(0, int((limit - elapsed).total_seconds()))


async def update_help_last_use(
        worker_id: int,
) -> None:
    async with async_session() as session:
        last_use: HelpLastUse = await session.scalar(
            select(HelpLastUse).where(
                HelpLastUse.worker_id == worker_id
            )
        )

        if not last_use:
            session.add(
                HelpLastUse(
                    worker_id=worker_id,
                    last_use=datetime.now(),
                )
            )
        else:
            last_use.last_use = datetime.now()

        await session.commit()
