from datetime import datetime, timedelta
from typing import List, Optional, NamedTuple
import pytz
from sqlalchemy import select, update, case
from sqlalchemy.orm import selectinload

from database import CallCampaign, CallResult, PhoneVerification, User, OrderWorker, DataForSecurity, Order, async_session

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Смещения в минутах от начала смены для прозвона (отрицательные = до начала)
CALL_OFFSETS = {
    'day': -75,    # первый звонок за 1:15 до начала дневной смены
    'night': -100  # первый звонок за 1:40 до начала ночной смены
}

# За сколько минут до первого звонка показывать кампанию в меню
SHOW_CAMPAIGN_BEFORE_MINUTES = {
    'day': 5,    # показывать дневную кампанию за 5 минут до первого звонка
    'night': 5   # показывать ночную кампанию за 5 минут до первого звонка
}


class WorkerPhone(NamedTuple):
    """Исполнитель с приоритетным номером для прозвона."""
    id: int
    phone_number: str


async def create_call_campaign(order_id: int, shift: str, order_date: str) -> CallCampaign:
    """Создать запись кампании прозвона."""
    async with async_session() as session:
        campaign = CallCampaign(
            order_id=order_id,
            shift=shift,
            order_date=order_date
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        return campaign


async def create_call_result(campaign_id: int, worker_id: int, phone_number: str) -> CallResult:
    """Создать запись результата звонка для исполнителя."""
    async with async_session() as session:
        result = CallResult(
            campaign_id=campaign_id,
            worker_id=worker_id,
            phone_number=phone_number,
            status='pending',
            attempt_no=0
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result


async def update_call_result_attempt(
    result_id: int,
    zvonok_call_id: Optional[str],
    attempt_no: int
) -> None:
    """Обновить запись результата после инициирования звонка."""
    async with async_session() as session:
        await session.execute(
            update(CallResult)
            .where(CallResult.id == result_id)
            .values(
                zvonok_call_id=zvonok_call_id,
                attempt_no=attempt_no,
                updated_at=datetime.now()
            )
        )
        await session.commit()


async def get_call_result(result_id: int) -> Optional[CallResult]:
    """Получить запись результата по ID."""
    async with async_session() as session:
        return await session.scalar(
            select(CallResult).where(CallResult.id == result_id)
        )


async def set_call_result_status(result_id: int, status: str, raw_response: str = None) -> None:
    """Установить итоговый статус результата звонка."""
    async with async_session() as session:
        values = {'status': status, 'updated_at': datetime.now()}
        if raw_response is not None:
            values['raw_response'] = raw_response
        await session.execute(
            update(CallResult).where(CallResult.id == result_id).values(**values)
        )
        await session.commit()


async def get_campaign(campaign_id: int) -> Optional[CallCampaign]:
    """Получить кампанию по ID."""
    async with async_session() as session:
        return await session.scalar(
            select(CallCampaign).where(CallCampaign.id == campaign_id)
        )


async def get_call_result_by_campaign_and_worker(campaign_id: int, worker_id: int) -> Optional[CallResult]:
    """Получить запись результата звонка для конкретного работника в кампании."""
    async with async_session() as session:
        return await session.scalar(
            select(CallResult).where(
                CallResult.campaign_id == campaign_id,
                CallResult.worker_id == worker_id
            )
        )


async def get_or_create_call_result(campaign_id: int, worker_id: int, phone_number: str) -> CallResult:
    """Получить существующую или создать новую запись результата звонка."""
    async with async_session() as session:
        # Пытаемся найти существующую запись
        result = await session.scalar(
            select(CallResult).where(
                CallResult.campaign_id == campaign_id,
                CallResult.worker_id == worker_id
            )
        )

        if result:
            return result

        # Создаём новую запись
        result = CallResult(
            campaign_id=campaign_id,
            worker_id=worker_id,
            phone_number=phone_number,
            status='pending',
            attempt_no=0
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result


async def set_worker_call_block(worker_id: int, reason: str) -> None:
    """Заблокировать исполнителя от взятия заказов (статус 🟡/🔵)."""
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == worker_id)
            .values(call_block=True, call_block_reason=reason)
        )
        await session.commit()


async def clear_worker_call_block(worker_id: int) -> None:
    """Снять блокировку после верификации телефона."""
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == worker_id)
            .values(call_block=False, call_block_reason=None)
        )
        await session.commit()


async def get_campaign_by_order_id(order_id: int, shift: str) -> Optional[CallCampaign]:
    """Получить кампанию по заявке и типу смены."""
    async with async_session() as session:
        return await session.scalar(
            select(CallCampaign)
            .where(CallCampaign.order_id == order_id, CallCampaign.shift == shift)
        )


async def get_campaign_results(campaign_id: int) -> List[CallResult]:
    """Получить все результаты кампании с данными исполнителей."""
    async with async_session() as session:
        results = await session.scalars(
            select(CallResult)
            .where(CallResult.campaign_id == campaign_id)
            .options(selectinload(CallResult.worker))
        )
        return results.all()


async def get_campaigns_by_date(date_str: str) -> List[CallCampaign]:
    """Получить все кампании за указанную дату (для архива)."""
    async with async_session() as session:
        campaigns = await session.scalars(
            select(CallCampaign).where(CallCampaign.order_date == date_str)
        )
        return campaigns.all()


async def get_active_campaigns_by_date(date_str: str) -> List[CallCampaign]:
    """
    Получить только активные кампании за указанную дату.
    Кампания считается активной, если до времени первого звонка осталось 
    меньше заданного порога или прозвон уже начался.
    """
    async with async_session() as session:
        # Получаем все кампании за дату
        campaigns = await session.scalars(
            select(CallCampaign).where(CallCampaign.order_date == date_str)
        )
        all_campaigns = campaigns.all()
        
        if not all_campaigns:
            return []
        
        # Текущее время по Москве
        now = datetime.now(MOSCOW_TZ)
        active_campaigns = []
        
        for campaign in all_campaigns:
            # Получаем заказ для определения времени смены
            order = await session.scalar(
                select(Order).where(Order.id == campaign.order_id)
            )
            
            if not order:
                continue
            
            # Определяем время начала смены
            shift_str = order.day_shift if campaign.shift == 'day' else order.night_shift
            if not shift_str:
                continue
            
            try:
                # Парсим время начала смены
                start_time = MOSCOW_TZ.localize(
                    datetime.strptime(
                        f'{order.date} {shift_str.split("-")[0].strip()}',
                        '%d.%m.%Y %H:%M'
                    )
                )
                
                # Вычисляем время первого звонка
                first_call_offset = CALL_OFFSETS[campaign.shift]
                first_call_time = start_time + timedelta(minutes=first_call_offset)
                
                # Вычисляем время, когда кампания должна появиться в меню
                show_before = SHOW_CAMPAIGN_BEFORE_MINUTES[campaign.shift]
                show_time = first_call_time - timedelta(minutes=show_before)
                
                # Если текущее время >= времени показа, добавляем кампанию
                if now >= show_time:
                    active_campaigns.append(campaign)
                    
            except (ValueError, KeyError):
                # Если не удалось распарсить - пропускаем эту кампанию
                continue
        
        return active_campaigns


async def get_order_workers_with_phones(order_id: int) -> List[WorkerPhone]:
    """
    Получить исполнителей заявки с приоритетными номерами для прозвона.
    Приоритет: реальный номер (DataForSecurity) → номер из Telegram (User).
    """
    async with async_session() as session:
        # LEFT JOIN с DataForSecurity и COALESCE для приоритета
        stmt = (
            select(
                User.id,
                case(
                    (DataForSecurity.phone_number.is_not(None), DataForSecurity.phone_number),
                    else_=User.phone_number
                ).label('phone_number')
            )
            .join(OrderWorker, OrderWorker.worker_id == User.id)
            .outerjoin(DataForSecurity, DataForSecurity.user_id == User.id)
            .where(OrderWorker.order_id == order_id)
        )
        result = await session.execute(stmt)
        return [WorkerPhone(id=row.id, phone_number=row.phone_number) for row in result]


# ─── Верификация телефона ────────────────────────────────────────────────────

async def get_phone_verification(user_id: int) -> Optional[PhoneVerification]:
    """Получить запись верификации телефона."""
    async with async_session() as session:
        return await session.scalar(
            select(PhoneVerification).where(PhoneVerification.user_id == user_id)
        )


async def upsert_phone_verification(
    user_id: int,
    code_hash: str,
    salt: str,
    pending_phone: str
) -> None:
    """Создать или обновить запись верификации (сохранить код и ожидающий номер)."""
    async with async_session() as session:
        existing = await session.scalar(
            select(PhoneVerification).where(PhoneVerification.user_id == user_id)
        )
        if existing:
            await session.execute(
                update(PhoneVerification)
                .where(PhoneVerification.user_id == user_id)
                .values(code_hash=code_hash, salt=salt, pending_phone=pending_phone)
            )
        else:
            session.add(PhoneVerification(
                user_id=user_id,
                code_hash=code_hash,
                salt=salt,
                pending_phone=pending_phone
            ))
        await session.commit()


async def confirm_phone_verification(user_id: int) -> None:
    """Подтвердить верификацию: обновить verified_at, очистить временные данные."""
    async with async_session() as session:
        await session.execute(
            update(PhoneVerification)
            .where(PhoneVerification.user_id == user_id)
            .values(verified_at=datetime.now(), code_hash=None, salt=None, pending_phone=None)
        )
        await session.commit()


async def update_user_phone(user_id: int, phone: str) -> None:
    """Обновить номер телефона пользователя."""
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(phone_number=phone)
        )
        await session.commit()
