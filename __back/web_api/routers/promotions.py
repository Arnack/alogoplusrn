from __future__ import annotations

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import database as db
from database.models import User
from web_api.deps import get_current_worker

router = APIRouter()


class PromotionOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    n_orders: int
    period_days: Optional[int]
    bonus_amount: int
    city: str
    participation_id: Optional[int] = None
    current_progress: int = 0
    cycles_completed: int = 0


class BonusOut(BaseModel):
    id: int
    promotion_name: str
    amount: int
    accrued_at: datetime


@router.get('', response_model=list[PromotionOut])
async def list_promotions(user: Annotated[User, Depends(get_current_worker)]):
    promos = await db.get_active_promotions_by_city(city=user.city)
    all_parts = await db.get_worker_participations(worker_id=user.id)
    parts_by_promo = {p.promotion_id: p for p in all_parts}

    result = []
    for p in promos:
        part = parts_by_promo.get(p.id)
        progress = 0
        if part:
            progress = part.current_streak if p.type == 'streak' else part.period_completed
        result.append(PromotionOut(
            id=p.id,
            name=p.name,
            description=p.description,
            type=p.type,
            n_orders=p.n_orders,
            period_days=p.period_days,
            bonus_amount=p.bonus_amount,
            city=p.city,
            participation_id=part.id if part else None,
            current_progress=progress,
            cycles_completed=part.cycles_completed if part else 0,
        ))
    return result


@router.post('/{promotion_id}/join', response_model=dict)
async def join_promotion(
    promotion_id: int,
    user: Annotated[User, Depends(get_current_worker)],
):
    promo = await db.get_promotion_by_id(promotion_id)
    if not promo or not promo.is_active:
        raise HTTPException(404, detail='Акция не найдена или неактивна')
    if promo.city != user.city:
        raise HTTPException(403, detail='Акция недоступна в вашем городе')
    part = await db.join_promotion(worker_id=user.id, promotion_id=promotion_id)
    return {'participation_id': part.id}


@router.post('/cancel-all', response_model=dict)
async def cancel_all_promotions(user: Annotated[User, Depends(get_current_worker)]):
    await db.cancel_all_participations(worker_id=user.id)
    return {'ok': True}


@router.get('/bonuses', response_model=list[BonusOut])
async def my_bonuses(user: Annotated[User, Depends(get_current_worker)]):
    bonuses = await db.get_worker_bonuses(worker_id=user.id)
    return [
        BonusOut(
            id=b.id,
            promotion_name=b.promotion_name,
            amount=b.amount,
            accrued_at=b.accrued_at,
        )
        for b in bonuses
    ]
