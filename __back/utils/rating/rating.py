from decimal import Decimal

import database as db


async def get_rating(
        user_id: int
) -> str:
    user_rating = await db.get_user_rating(user_id=user_id)
    if not user_rating:
        await db.set_rating(user_id=user_id)
        return '100.00%'
    if user_rating.total_orders == 0:
        return '100.00%'
    rating = (
        (Decimal(user_rating.successful_orders) / Decimal(user_rating.total_orders)) * Decimal('100')
    ) + Decimal(f'{user_rating.plus}')

    return f'{rating:.2f}%'
