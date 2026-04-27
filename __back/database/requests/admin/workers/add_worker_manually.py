import logging
from database import User, DataForSecurity, UserRating, UserRegisteredAt, async_session
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional


async def add_worker_manually(
        last_name: str,
        first_name: str,
        middle_name: Optional[str],
        inn: Optional[str],
        phone_number: Optional[str],
        telegram_id: Optional[int],
        card_number: Optional[str] = None,
) -> Optional[int]:
    """
    Ручное добавление самозанятого в систему

    Args:
        last_name: Фамилия (обязательно)
        first_name: Имя (обязательно)
        middle_name: Отчество (опционально)
        inn: ИНН (опционально, если указан - должен быть 12 цифр)
        phone_number: Номер телефона (опционально, в формате +7XXXXXXXXXX)
        telegram_id: Telegram ID (опционально)

    Returns:
        ID созданного пользователя или None в случае ошибки
    """
    try:
        async with async_session() as session:
            # Проверяем, существует ли уже самозанятый с таким номером телефона или ИНН
            if phone_number:
                existing_by_phone = await session.scalar(
                    select(User).where(User.phone_number == phone_number)
                )
                if existing_by_phone:
                    logging.warning(f'Worker with phone {phone_number} already exists')
                    return None

            if inn:
                existing_by_inn = await session.scalar(
                    select(User).where(User.inn == inn)
                )
                if existing_by_inn:
                    logging.warning(f'Worker with INN {inn} already exists')
                    return None

            # Используем нулевой tg_id для ручных добавлений (временно)
            # Это будет обновлено при первом входе самозанятого в систему
            default_tg_id = telegram_id if telegram_id else 0

            # Создаем нового пользователя
            new_user = User(
                tg_id=default_tg_id,
                username=None,  # Будет добавлено при первом входе
                phone_number=phone_number if phone_number else '',
                city='',  # Город можно будет установить позже через супервайзера
                first_name=first_name,
                middle_name=middle_name if middle_name else '',
                last_name=last_name,
                inn=inn if inn else '',
                card=card_number if card_number else '',
            )
            session.add(new_user)

            # Добавляем данные для охраны (используем те же данные)
            session.add(
                DataForSecurity(
                    phone_number=phone_number if phone_number else '',
                    first_name=first_name,
                    last_name=last_name,
                    middle_name=middle_name if middle_name else '',
                    user=new_user
                )
            )

            # Добавляем дату регистрации
            session.add(
                UserRegisteredAt(
                    date=datetime.now().strftime('%d.%m.%Y'),
                    user=new_user
                )
            )

            # Создаем рейтинг
            session.add(UserRating(user=new_user))

            await session.commit()
            await session.refresh(new_user)

            logging.info(f'Worker manually added: ID={new_user.id}, Name={last_name} {first_name}')
            return new_user.id

    except Exception as e:
        logging.exception(f'Error adding worker manually: {e}')
        return None


async def update_worker_fio_from_api(
        worker_id: int,
        first_name: str,
        last_name: str,
        patronymic: Optional[str],
        phone_number: Optional[str] = None
) -> bool:
    """
    Обновляет ФИО и номер телефона самозанятого в таблице User данными из API "Рабочие руки"
    DataForSecurity остаётся с реальными введёнными данными

    Args:
        worker_id: ID работника в базе данных
        first_name: Имя из API
        last_name: Фамилия из API
        patronymic: Отчество из API (может быть пустым)
        phone_number: Номер телефона из API (опционально, в формате +7XXXXXXXXXX)

    Returns:
        True в случае успеха, False в случае ошибки
    """
    try:
        async with async_session() as session:
            # Формируем словарь для обновления
            update_values = {
                'first_name': first_name,
                'last_name': last_name,
                'middle_name': patronymic if patronymic else ''
            }

            # Если передан номер телефона из API, обновляем и его
            if phone_number:
                update_values['phone_number'] = phone_number

            # Обновляем данные в таблице User
            await session.execute(
                update(User)
                .where(User.id == worker_id)
                .values(**update_values)
            )

            await session.commit()
            phone_log = f', phone: {phone_number}' if phone_number else ''
            logging.info(f'Worker {worker_id} User data updated from API: {last_name} {first_name} {patronymic}{phone_log}')
            return True

    except Exception as e:
        logging.exception(f'Error updating worker {worker_id} User data from API: {e}')
        return False
