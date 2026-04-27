from database import Rule, async_session
from sqlalchemy import select
from datetime import datetime


async def set_or_update_rules(
        new_rules: str,
        rules_for: str,
) -> None:
    async with async_session() as session:
        rules = await session.scalar(
            select(Rule).where(
                Rule.role == rules_for
            )
        )
        new_date = datetime.now().strftime('%d.%m.%Y')
        if not rules:
            session.add(
                Rule(
                    role=rules_for,
                    rules=new_rules,
                    date=new_date
                )
            )
        else:
            rules.rules = new_rules
            rules.date = new_date
        await session.commit()


async def get_rules(
        rules_for: str,
) -> Rule:
    async with async_session() as session:
        return await session.scalar(
            select(Rule).where(
                Rule.role == rules_for
            )
        )
