from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from math import ceil

import database as db

STATUS_EMOJI = {
    'green': '🟢',
    'red': '🔴',
    'blue': '🔵',
    'yellow': '🟡',
    'pending': '⏳',
}


class CallCampaignCallbackData(CallbackData, prefix='CallCamp'):
    campaign_id: Optional[int] = None
    result_id: Optional[int] = None
    action: str
    date: Optional[str] = None
    page: int = 1


async def call_campaigns_menu(
    campaigns: List[db.CallCampaign],
    page: int = 1,
    items_per_page: int = 8
) -> InlineKeyboardMarkup:
    """Список кампаний прозвона (сегодняшних или по дате)."""
    keyboard = InlineKeyboardBuilder()
    total_pages = max(1, ceil(len(campaigns) / items_per_page))
    start = (page - 1) * items_per_page
    end = start + items_per_page

    for campaign in campaigns[start:end]:
        organization = await db.get_customer_organization(
            customer_id=(await db.get_order(order_id=campaign.order_id)).customer_id
        )
        shift_label = 'Д' if campaign.shift == 'day' else 'Н'
        # Формат: "Организация 1202 Д"
        date_short = campaign.order_date[:5] if campaign.order_date else ''
        label = f'{organization} {date_short} {shift_label}'
        keyboard.row(InlineKeyboardButton(
            text=label,
            callback_data=CallCampaignCallbackData(
                campaign_id=campaign.id,
                action='OpenCampaign',
                date=campaign.order_date,
                page=page
            ).pack()
        ))

    # Пагинация
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton(
                text='◀️ Назад',
                callback_data=CallCampaignCallbackData(action='PageCampaigns', page=page - 1).pack()
            ))
        nav.append(InlineKeyboardButton(text=f'{page}/{total_pages}', callback_data='None'))
        if page < total_pages:
            nav.append(InlineKeyboardButton(
                text='Вперёд ▶️',
                callback_data=CallCampaignCallbackData(action='PageCampaigns', page=page + 1).pack()
            ))
        keyboard.row(*nav)

    return keyboard.as_markup()


async def call_campaign_workers_menu(
    results: List[db.CallResult],
    campaign_id: int,
    date: str,
    page: int = 1
) -> InlineKeyboardMarkup:
    """Список исполнителей кампании с emoji-статусом."""
    keyboard = InlineKeyboardBuilder()

    for result in results:
        emoji = STATUS_EMOJI.get(result.status, '⏳')
        full_name = '—'
        if result.worker_id:
            real_data = await db.get_user_real_data_by_id(user_id=result.worker_id)
            if real_data:
                full_name = f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}'
        keyboard.row(InlineKeyboardButton(
            text=f'{full_name} {emoji}',
            callback_data=CallCampaignCallbackData(
                campaign_id=campaign_id,
                result_id=result.id,
                action='ShowWorkerPhones',
                date=date,
                page=page
            ).pack()
        ))

    keyboard.row(InlineKeyboardButton(
        text='◀️ К списку прозвонов',
        callback_data=CallCampaignCallbackData(action='BackToCampaigns', page=page).pack()
    ))
    return keyboard.as_markup()


def worker_phones_keyboard(
    campaign_id: int,
    date: str,
    page: int = 1
) -> InlineKeyboardMarkup:
    """Кнопка возврата из карточки исполнителя."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text='◀️ Назад',
            callback_data=CallCampaignCallbackData(
                campaign_id=campaign_id,
                action='OpenCampaign',
                date=date,
                page=page
            ).pack()
        )
    ]])


def call_archive_back() -> InlineKeyboardMarkup:
    """Кнопка возврата в архив прозвонов."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='◀️ К архиву', callback_data='BackToCallArchive')
    ]])
