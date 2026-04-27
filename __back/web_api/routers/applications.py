from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException

import database as db
import texts as txt
from config_reader import config
from database.models import User
from utils import get_day_of_week_by_date, get_rating, get_rating_coefficient
from utils.refuse_assigned_worker import refuse_assigned_order_worker, strip_html_plain

from web_api.deps import get_current_worker
from web_api.schemas import ApplicationItem, MessageResponse

router = APIRouter()


def _date_key(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except Exception:
        return datetime.min


@router.get('/orders', response_model=list[ApplicationItem])
async def my_orders(user: Annotated[User, Depends(get_current_worker)]):
    raw = await db.get_orders_by_worker_id(worker_id=user.id)
    by_id: dict[int, object] = {}
    for order in raw:
        if order and order.id not in by_id:
            by_id[order.id] = order

    rating = await get_rating(user_id=user.id)
    coefficient = get_rating_coefficient(rating=rating[:-1])

    items: list[ApplicationItem] = []
    for order in by_id.values():
        app_row_id = await db.get_worker_application_id(order_id=order.id, worker_id=user.id)
        ow_id = await db.get_worker_app_id(order_id=order.id, worker_id=user.id)

        if ow_id:
            kind = 'assigned'
            app_public_id = None
            worker_row_id = ow_id
        elif app_row_id:
            kind = 'application'
            app_public_id = app_row_id
            worker_row_id = None
        else:
            continue

        organization = await db.get_customer_organization(order.customer_id)
        day = get_day_of_week_by_date(date=order.date)
        amount_adj = round(Decimal(str(order.amount).replace(',', '.')) * coefficient, 2)

        ow_row = None
        added_by_manager = None
        if kind == 'assigned':
            ow_row = await db.get_order_worker(worker_id=user.id, order_id=order.id)
            if ow_row:
                added_by_manager = bool(ow_row.added_by_manager)

        items.append(
            ApplicationItem(
                order_id=order.id,
                kind=kind,
                application_id=app_public_id,
                order_worker_id=worker_row_id,
                job_name=order.job_name,
                date=order.date,
                city=order.city,
                customer_id=order.customer_id,
                organization=organization,
                day_shift=order.day_shift,
                night_shift=order.night_shift,
                amount_adjusted=str(amount_adj),
                day_of_week=day,
                added_by_manager=added_by_manager,
            )
        )

    items.sort(key=lambda x: _date_key(x.date), reverse=True)
    return items


@router.get('/orders/{order_id}/refusal-notice', response_model=MessageResponse)
async def assigned_refusal_notice(
    order_id: int,
    user: Annotated[User, Depends(get_current_worker)],
):
    ow_id = await db.get_worker_app_id(order_id=order_id, worker_id=user.id)
    if not ow_id:
        raise HTTPException(404, 'Нет подтверждённой заявки по этому заказу')
    ow_row = await db.get_order_worker(worker_id=user.id, order_id=order_id)
    if not ow_row:
        raise HTTPException(404, 'Нет подтверждённой заявки по этому заказу')
    raw = txt.remove_worker_manager_app() if ow_row.added_by_manager else txt.remove_worker()
    return MessageResponse(message=strip_html_plain(raw))


@router.delete('/orders/{order_id}/assignment', response_model=MessageResponse)
async def refuse_assigned_order(
    order_id: int,
    user: Annotated[User, Depends(get_current_worker)],
):
    ow_id = await db.get_worker_app_id(order_id=order_id, worker_id=user.id)
    if not ow_id:
        raise HTTPException(404, 'Нет подтверждённой заявки по этому заказу')
    tok = config.bot_token
    if not tok:
        raise HTTPException(500, 'BOT_TOKEN не задан')
    bot = Bot(token=tok.get_secret_value())
    try:
        res = await refuse_assigned_order_worker(
            worker_app_id=ow_id,
            actor_user=user,
            bot=bot,
            tg_message=None,
        )
    finally:
        await bot.session.close()
    if res.blocked_by_time:
        raise HTTPException(409, res.message_plain)
    if not res.message_plain or res.message_plain in (
        'Запись не найдена',
        'Заявка не найдена',
        'Запись исполнителя по заявке не найдена',
    ):
        raise HTTPException(404, res.message_plain or 'Операция не выполнена')
    if 'Не удалось загрузить данные профиля' in res.message_plain:
        raise HTTPException(500, res.message_plain)
    return MessageResponse(message=res.message_plain)


@router.delete('/orders/{order_id}/application', response_model=MessageResponse)
async def withdraw_application(
    order_id: int,
    user: Annotated[User, Depends(get_current_worker)],
):
    app_id = await db.get_worker_application_id(order_id=order_id, worker_id=user.id)
    if not app_id:
        raise HTTPException(404, 'Активного отклика нет')
    await db.delete_application(app_id)
    return MessageResponse(message='ok')
