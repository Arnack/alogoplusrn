from database import UserRating, async_session
from sqlalchemy import select, update


async def set_rating(
        user_id: int
) -> None:
    async with async_session() as session:
        rating = await session.scalar(
            select(UserRating).where(
                UserRating.user_id == user_id
            )
        )
        if not rating:
            session.add(UserRating(user_id=user_id))
            await session.commit()


async def get_user_rating(
        user_id: int
) -> UserRating:
    async with async_session() as session:
        return await session.scalar(
            select(UserRating).where(
                UserRating.user_id == user_id
            )
        )


async def update_rating_total_orders(
        user_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(UserRating).where(
                UserRating.user_id == user_id
            ).values(
                total_orders=UserRating.total_orders + 1
            )
        )
        await session.commit()


async def update_worker_rating(
        total_orders: int,
        worker_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(UserRating).where(
                UserRating.user_id == worker_id
            ).values(
                total_orders=total_orders
            )
        )
        await session.commit()


async def update_rating_successful_orders(
        user_id: int
) -> None:
    async with async_session() as session:
        await session.execute(
            update(UserRating).where(
                UserRating.user_id == user_id
            ).values(
                successful_orders=UserRating.successful_orders + 1
            )
        )
        await session.commit()


async def update_rating_plus(user_id: int, plus_value: int = 1) -> None:
    """Увеличить бонусный процент рейтинга (для EXTRA исполнителей)"""
    async with async_session() as session:
        await session.execute(
            update(UserRating).where(
                UserRating.user_id == user_id
            ).values(
                plus=UserRating.plus + plus_value
            )
        )
        await session.commit()


async def get_worker_stats(worker_id: int) -> tuple[int, int, int]:
    """
    Получить статистику работника

    :param worker_id: ID работника
    :return: Кортеж (total_orders, successful_orders, rejected)
    """
    from database import User

    async with async_session() as session:
        rating = await session.scalar(
            select(UserRating).where(UserRating.user_id == worker_id)
        )
        user = await session.scalar(
            select(User).where(User.id == worker_id)
        )

        if rating and user:
            total_orders = rating.total_orders
            successful_orders = rating.successful_orders
            rejected = user.rejections
            return total_orders, successful_orders, rejected

        return 0, 0, 0


async def is_foreman(worker_id: int) -> bool:
    """
    Проверить, является ли работник представителем (foreman)

    :param worker_id: ID работника
    :return: True если работник является представителем, иначе False
    """
    from database import User, CustomerForeman
    from sqlalchemy import or_

    async with async_session() as session:
        user = await session.scalar(
            select(User).where(User.id == worker_id)
        )

        if not user:
            return False

        # Проверяем по tg_id (для Telegram бота)
        # Для Max бота пока возвращаем False, так как CustomerForeman не имеет max_id
        if user.tg_id and user.tg_id != 0:
            foreman = await session.scalar(
                select(CustomerForeman).where(CustomerForeman.tg_id == user.tg_id)
            )
            return foreman is not None

        # Для Max бота (max_id) пока возвращаем False
        # TODO: добавить поле max_id в CustomerForeman для поддержки Max бота
        return False
