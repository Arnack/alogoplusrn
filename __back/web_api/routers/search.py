from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

import database as db
import texts as txt
from database.models import User
from utils import get_day_of_week_by_date, get_rating, get_rating_coefficient

from web_api.deps import get_current_worker
from web_api.extras_friend import get_friend_verified
from web_api.schemas import (
    ApplyOrderBody,
    ApplyPreviewOut,
    CustomerSearchItem,
    MessageResponse,
    OrderSearchItem,
)

router = APIRouter()


def _sort_orders(orders):
    def key_fn(order):
        t = order.day_shift[:5] if order.day_shift else (order.night_shift[:5] if order.night_shift else '00:00')
        return datetime.strptime(f'{order.date} {t}', '%d.%m.%Y %H:%M')

    return sorted(orders, key=key_fn)


def _resolve_search_worker(user: User, for_friend: bool) -> tuple[int, str]:
    if not for_friend:
        return user.id, user.city
    ctx = get_friend_verified(user.id)
    if not ctx:
        raise HTTPException(
            400,
            'Подтвердите друга в разделе «Заявка для друга» (код из SMS).',
        )
    friend_id, friend_city = ctx
    return friend_id, friend_city


@router.get('/order-customers', response_model=list[CustomerSearchItem])
async def order_customers(
    user: Annotated[User, Depends(get_current_worker)],
    for_friend: bool = Query(False),
):
    worker_id, city = _resolve_search_worker(user, for_friend)
    customer_ids = await db.get_customers_id_by_city(city=city)
    out: list[CustomerSearchItem] = []
    for customer_id in customer_ids:
        orders = await db.get_orders_for_search(
            worker_city=city,
            worker_id=worker_id,
            customer_id=customer_id,
        )
        if orders:
            cust = await db.get_customer(customer_id=customer_id)
            out.append(
                CustomerSearchItem(
                    customer_id=customer_id,
                    organization=cust.organization if cust else str(customer_id),
                    orders_available=len(orders),
                )
            )
    return out


@router.get('/orders', response_model=list[OrderSearchItem])
async def search_orders_list(
    user: Annotated[User, Depends(get_current_worker)],
    customer_id: int,
    for_friend: bool = Query(False),
):
    worker_id, city = _resolve_search_worker(user, for_friend)
    orders = await db.get_orders_for_search(
        worker_city=city,
        worker_id=worker_id,
        customer_id=customer_id,
    )
    if not orders:
        return []

    rating = await get_rating(user_id=worker_id)
    coef = get_rating_coefficient(rating=rating[:-1])

    sorted_o = _sort_orders(orders)
    job_fps = await db.get_job_fp_sequence(worker_id=worker_id, count=len(sorted_o))

    result: list[OrderSearchItem] = []
    for i, o in enumerate(sorted_o):
        base = Decimal(o.amount.replace(',', '.'))
        amount_adj = round(base * coef, 2)
        travel = await db.get_travel_compensation(customer_id=o.customer_id)
        result.append(
            OrderSearchItem(
                id=o.id,
                job_name=o.job_name,
                date=o.date,
                city=o.city,
                customer_id=o.customer_id,
                day_shift=o.day_shift,
                night_shift=o.night_shift,
                amount_base=str(o.amount),
                amount_with_rating=str(amount_adj),
                job_fp=job_fps[i],
                travel_compensation_rub=travel if travel and travel > 0 else None,
            )
        )
    return result


@router.get('/orders/{order_id}/apply-preview', response_model=ApplyPreviewOut)
async def apply_preview(
    order_id: int,
    user: Annotated[User, Depends(get_current_worker)],
    for_friend: bool = Query(False),
):
    """Текст подтверждения отклика для веб-панели (структурированный HTML; порог высокого рейтинга 93)."""
    worker_id, _city = _resolve_search_worker(user, for_friend)
    order = await db.get_order(order_id=order_id)
    if not order:
        raise HTTPException(404, 'Заявка не найдена')

    if for_friend:
        ctx = get_friend_verified(user.id)
        if not ctx:
            raise HTTPException(
                400,
                'Подтвердите друга в разделе «Заявка для друга» (код из SMS).',
            )
        friend_id, _ = ctx
        real_data = await db.get_user_real_data_by_id(user_id=friend_id)
        friend_user = await db.get_user_by_id(user_id=friend_id)
        if not real_data or not friend_user:
            raise HTTPException(404, 'Данные друга не найдены')
        rating = await get_rating(user_id=friend_user.id)
        coefficient = get_rating_coefficient(rating=rating[:-1])
        amount_adj = str(round(Decimal(order.amount.replace(',', '.')) * coefficient, 2))
        travel = await db.get_travel_compensation(customer_id=order.customer_id)
        message_html = await txt.apply_preview_html_for_friend(
            order_id=order_id,
            first_name=real_data.first_name,
            middle_name=real_data.middle_name,
            last_name=real_data.last_name,
            amount=amount_adj,
            travel_compensation=travel,
        )
        return ApplyPreviewOut(message_html=message_html, order_summary_html='')

    rating = await get_rating(user_id=worker_id)
    user_rating = await db.get_user_rating(user_id=worker_id)
    if not user_rating:
        await db.set_rating(user_id=worker_id)
        user_rating = await db.get_user_rating(user_id=worker_id)
    if not user_rating:
        raise HTTPException(500, 'Не удалось загрузить рейтинг исполнителя')
    coefficient = get_rating_coefficient(rating=rating[:-1])
    amount_adj = str(round(Decimal(order.amount.replace(',', '.')) * coefficient, 2))
    organization = await db.get_customer_organization(order.customer_id)
    job_fp = await db.get_job_fp_for_txt(worker_id=worker_id)
    travel = await db.get_travel_compensation(customer_id=order.customer_id)
    order_summary_html = txt.apply_preview_order_summary_html(
        city=order.city,
        organization=organization or '',
        job=order.job_name,
        date=order.date,
        day=get_day_of_week_by_date(date=order.date),
        period_time=order.day_shift or order.night_shift or '',
        is_day_shift=bool(order.day_shift),
        amount=amount_adj,
        job_fp=job_fp,
        travel_compensation=travel,
    )
    if Decimal(rating[:-1]) >= Decimal('93'):
        message_html = txt.apply_preview_html_high_rating()
    else:
        message_html = txt.apply_preview_html_low_rating(
            rating=rating,
            amount=order.amount,
            total_orders=user_rating.total_orders,
            successful_orders=user_rating.successful_orders,
            plus=user_rating.plus,
            coefficient=coefficient,
        )
    return ApplyPreviewOut(
        message_html=message_html,
        order_summary_html=order_summary_html,
    )


@router.post('/orders/{order_id}/applications', response_model=MessageResponse)
async def apply_to_order(
    order_id: int,
    user: Annotated[User, Depends(get_current_worker)],
    body: ApplyOrderBody,
):
    if body.order_from_friend:
        ctx = get_friend_verified(user.id)
        if not ctx:
            raise HTTPException(
                400,
                'Подтвердите друга в разделе «Заявка для друга» (код из SMS).',
            )
        friend_id, _friend_city = ctx
        target_worker_id = friend_id
    else:
        target_worker_id = user.id

    exists = await db.has_application(worker_id=target_worker_id, order_id=order_id)
    if exists:
        raise HTTPException(409, 'Уже есть отклик на эту заявку')

    ow = await db.get_worker_app_id(order_id=order_id, worker_id=target_worker_id)
    if ow:
        raise HTTPException(409, 'Исполнитель уже назначен на эту заявку')

    order = await db.get_order(order_id=order_id)
    if not order:
        raise HTTPException(404, 'Заявка не найдена')

    worker_dates = await db.get_worker_dates(worker_id=target_worker_id)
    order_shift = f"{order.date} {'день' if order.day_shift else 'ночь'}"
    if order_shift in worker_dates:
        raise HTTPException(409, 'На эту дату у исполнителя уже есть занятость')

    res = await db.set_application(
        order_id=order_id,
        worker_id=target_worker_id,
        order_from_friend=body.order_from_friend,
    )
    if res == 'duplicate':
        raise HTTPException(409, 'Дубликат отклика')
    if res == 'error':
        raise HTTPException(500, 'Не удалось сохранить отклик')

    if body.order_from_friend and res == 'ok':
        friend = await db.get_user_by_id(user_id=friend_id)
        if not friend:
            raise HTTPException(500, 'Профиль друга не найден')
        await db.set_order_for_friend_log(
            order_id=order_id,
            who_signed=user.id,
            who_signed_tg_id=user.tg_id or 0,
            friend_id=friend.id,
            friend_tg_id=friend.tg_id or 0,
        )

    return MessageResponse(message=txt.send_respond())
