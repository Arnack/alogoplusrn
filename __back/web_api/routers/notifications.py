from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

import database as db
from database.models import User

from web_api.deps import get_current_worker
from web_api.schemas import NotificationItem, NotificationMarkReadBody, NotificationsResponse

router = APIRouter()

_READ_PREFIX = 'webpanel:notif_read:'
_PERSONAL_NOTIFICATION_TITLES = {
    'Ваша заявка подтверждена',
    'Услуга согласована и подтверждена',
}


def _is_personal_worker_notification(title: str | None, body: str | None) -> bool:
    t = (title or '').strip()
    b = (body or '').strip()
    if t in _PERSONAL_NOTIFICATION_TITLES:
        return True
    return (
        'Ваша заявка подтверждена' in b
        or 'по ранее принятому вами заказу оказание услуг согласовано и подтверждено' in b
    )


async def _read_ids(redis, user_id: int) -> set[str]:
    if redis is None:
        return set()
    key = f'{_READ_PREFIX}{user_id}'
    return set(await redis.smembers(key))


async def _mark_read_ids(redis, user_id: int, ids: list[str]) -> None:
    if redis is None or not ids:
        return
    key = f'{_READ_PREFIX}{user_id}'
    await redis.sadd(key, *ids)


async def _build_items(user_id: int) -> list[NotificationItem]:
    """Личные уведомления исполнителя по заявке (подтверждение/согласование)."""
    rows = await db.list_web_panel_notifications(user_id, limit=200)
    items: list[NotificationItem] = []
    for r in rows:
        if not _is_personal_worker_notification(r.title, r.body):
            continue
        ca = r.created_at
        created = ca.strftime('%d.%m.%Y %H:%M') if ca else ''
        items.append(
            NotificationItem(
                id=f'wpn-{r.id}',
                title=r.title or 'Сообщение от администрации',
                body=r.body,
                created_at=created,
                read=False,
            )
        )
    return items


@router.get('', response_model=NotificationsResponse)
async def list_notifications(
    request: Request,
    user: Annotated[User, Depends(get_current_worker)],
):
    redis = getattr(request.app.state, 'redis', None)
    items = await _build_items(user.id)
    read_set = await _read_ids(redis, user.id)
    for it in items:
        it.read = it.id in read_set
    unread = sum(1 for x in items if not x.read)
    return NotificationsResponse(items=items, unread_count=unread)


@router.post('/mark-read', response_model=NotificationsResponse)
async def mark_notifications_read(
    request: Request,
    user: Annotated[User, Depends(get_current_worker)],
    body: NotificationMarkReadBody,
):
    redis = getattr(request.app.state, 'redis', None)
    await _mark_read_ids(redis, user.id, body.ids)
    return await list_notifications(request, user)
