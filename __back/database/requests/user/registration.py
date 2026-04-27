import logging
from database import (
    User, DataForSecurity, UserRating, UserRegisteredAt, OrderApplication, OrderWorker, CustomerForeman, ShoutStat,
    async_session
)
from aiogram import Bot
from sqlalchemy import select, delete, update, or_
from config_reader import config
from datetime import datetime
from typing import Optional

import texts as txt


async def set_user(
        api_worker_id: int,
        card: str,
        tg_id: int = 0,
        username: Optional[str] = None,
        phone_number: str = None,
        city: str = None,
        first_name: str = None,
        middle_name: str = None,
        last_name: str = None,
        inn: str = None,
        real_phone_number: str = None,
        real_first_name: str = None,
        real_last_name: str = None,
        real_middle_name: str = None,
        max_id: int = 0,
        max_chat_id: int = 0,
        gender: str = None,
        passport_series: str = None,
        passport_number: str = None,
        passport_issue_date: str = None,
        passport_department_code: str = None,
        passport_issued_by: str = None,
) -> int | None:
    passport_complete = all([
        passport_series, passport_number,
        passport_issue_date, passport_department_code, passport_issued_by,
    ])
    async with async_session() as session:
        # Ищем пользователя по tg_id или max_id
        user = None
        if tg_id:
            user = await session.scalar(
                select(User).where(User.tg_id == tg_id)
            )
        elif max_id:
            user = await session.scalar(
                select(User).where(User.max_id == max_id)
            )

        phone_without_plus = phone_number.lstrip('+') if phone_number else ''
        user_by_phone = await session.scalar(
            select(User).where(
                or_(
                    User.phone_number == phone_number,
                    User.phone_number == phone_without_plus
                )
            )
        )

        if not user and user_by_phone and max_id:
            # Пользователь есть в БД (через Telegram), привязываем max_id
            values = {'max_id': max_id}
            if max_chat_id:
                values['max_chat_id'] = max_chat_id
            await session.execute(
                update(User)
                .where(User.id == user_by_phone.id)
                .values(**values)
            )
            await session.commit()
            return user_by_phone.id

        if not user and not user_by_phone:
            new_user = User(
                tg_id=tg_id,
                max_id=max_id,
                max_chat_id=max_chat_id,
                username=username,
                phone_number=phone_number,
                city=city,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                inn=inn,
                api_id=api_worker_id,
                card=card,
                gender=gender,
                passport_data_complete=passport_complete,
            )
            session.add(new_user)

            session.add(
                DataForSecurity(
                    phone_number=real_phone_number,
                    first_name=real_first_name,
                    last_name=real_last_name,
                    middle_name=real_middle_name,
                    passport_series=passport_series,
                    passport_number=passport_number,
                    passport_issue_date=passport_issue_date,
                    passport_department_code=passport_department_code,
                    passport_issued_by=passport_issued_by,
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
        return None


async def update_user_gtrr(
        tg_id: int,
        username: str,
        phone_number: str,
        api_worker_id: int,
        card: str,
) -> bool:
    async with async_session() as session:
        try:
            user: User = await session.scalar(
                select(User).where(
                    User.tg_id == tg_id,
                )
            )
            user.phone_number = phone_number
            user.username = username
            user.api_id = api_worker_id
            user.card = card

            await session.execute(
                update(DataForSecurity).where(
                    DataForSecurity.user_id == user.id,
                ).values(
                    phone_number=phone_number,
                )
            )
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logging.exception(e)
            return False


async def get_worker_by_phone_number(
        phone_number: str
) -> User:
    async with async_session() as session:
        # Ищем по обоим форматам: +79... и 79... (старые записи могут быть без +)
        phone_without_plus = phone_number.lstrip('+')
        return await session.scalar(
            select(User).where(
                or_(
                    User.phone_number == phone_number,
                    User.phone_number == phone_without_plus
                )
            )
        )


async def get_worker_by_inn(
        inn: str
) -> User:
    async with async_session() as session:
        return await session.scalar(
            select(User).where(
                User.inn == inn
            )
        )


async def get_workers_tg_id():
    async with async_session() as session:
        workers = await session.scalars(
            select(User.tg_id)
        )
        return workers.all()


async def delete_inactive_users():
    async with async_session() as session:
        users = await session.scalars(
            select(User.id)
        )
        for user_id in users:
            try:
                applications = await session.scalar(
                    select(OrderApplication.id).where(
                        OrderApplication.worker_id == user_id
                    )
                )
                works = await session.scalar(
                    select(OrderWorker.id).where(
                        OrderWorker.worker_id == user_id
                    )
                )
                rating: UserRating = await session.scalar(
                    select(UserRating).where(
                        UserRating.user_id == user_id
                    )
                )
                result = (datetime.now().date() - datetime.strptime('14.07.2025', '%d.%m.%Y').date()).days > 2

                has_rating = all(
                    [rating.total_orders > 0 and rating.successful_orders > 0]
                ) if rating else False

                if not applications and not works and not has_rating and result:
                    await session.execute(
                        delete(OrderApplication).where(
                            OrderApplication.worker_id == user_id
                        )
                    )
                    await session.execute(
                        delete(OrderWorker).where(
                            OrderWorker.worker_id == user_id
                        )
                    )
                    await session.execute(
                        delete(User).where(
                            User.id == user_id
                        )
                    )
                    tg_id = await session.scalar(
                        select(User.tg_id).where(
                            User.id == user_id
                        )
                    )
                    await session.execute(
                        delete(CustomerForeman).where(
                            CustomerForeman.tg_id == tg_id
                        )
                    )
                    await session.execute(
                        delete(ShoutStat).where(
                            ShoutStat.sender_tg_id == tg_id
                        )
                    )
                    async with Bot(token=config.bot_token.get_secret_value()) as bot:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.delete_inactive_user_notification()
                            )
                        except:
                            pass
            except Exception as e:
                logging.exception(f'\n\n{e}')
        await session.commit()


async def card_unique(
        card: str
) -> bool:
    async with async_session() as session:
        card = await session.scalar(
            select(User.card).where(
                User.card == card
            )
        )
        return bool(card)


async def update_worker_bank_card(
        worker_id: int,
        card: str,
) -> None:
    async with async_session() as session:
        try:
            await session.execute(
                update(User).where(
                    User.id == worker_id,
                ).values(
                    card=card,
                )
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.exception(e)
