from __future__ import annotations

import database as db


async def resolve_panel_role(tg_id: int) -> str:
    if tg_id and tg_id in await db.get_supervisors_tg_id():
        return 'supervisor'
    if tg_id and tg_id in await db.get_foremen_tg_id():
        return 'foreman'
    return 'worker'


def menu_items_for_role(role: str) -> list[tuple[str, str]]:
    # Порядок как в keyboards/reply/user/main_menu.py (foreman/supervisor)
    head = [
        ('about', 'Обо мне'),
        ('search_orders', 'Поиск заявок'),
        ('contact_management', 'Связь с руководством'),
        ('manage_orders', 'Управление заявкой'),
    ]
    friend = ('order_for_friend', 'Заявка для друга')
    if role == 'foreman':
        return head + [('site_alert', 'Оповещение на объекте'), friend]
    if role == 'supervisor':
        return head + [('coordinator', 'Координатор'), friend]
    return head + [friend]
