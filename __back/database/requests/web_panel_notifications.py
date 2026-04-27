from __future__ import annotations

import asyncio

from sqlalchemy import select

from database import async_session
from database.models import WebPanelNotification


async def add_web_panel_notification(
    worker_id: int,
    body: str,
    title: str = 'Сообщение от администрации',
) -> int:
    text = (body or '').strip()
    if not text:
        return 0
    async with async_session() as session:
        row = WebPanelNotification(worker_id=worker_id, title=title, body=text)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        notification_id = row.id

    try:
        from utils.expo_push import send_push
        asyncio.create_task(send_push(worker_id, title, text))
    except RuntimeError:
        pass  # no running event loop (e.g. tests)

    return notification_id


async def list_web_panel_notifications(worker_id: int, limit: int = 200) -> list[WebPanelNotification]:
    async with async_session() as session:
        res = await session.scalars(
            select(WebPanelNotification)
            .where(WebPanelNotification.worker_id == worker_id)
            .order_by(WebPanelNotification.created_at.desc())
            .limit(limit)
        )
        return list(res.all())
