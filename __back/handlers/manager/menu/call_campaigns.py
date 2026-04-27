from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime

import keyboards.inline as ikb
from filters import Manager
import database as db
import texts as txt

router = Router()
router.message.filter(Manager())
router.callback_query.filter(Manager())


@router.message(F.text == '📞 Прозвоны')
async def open_call_campaigns(message: Message) -> None:
    """Открыть список кампаний прозвона за сегодня."""
    today = datetime.now().strftime('%d.%m.%Y')
    campaigns = await db.get_active_campaigns_by_date(date_str=today)

    if campaigns:
        await message.answer(
            text=txt.call_campaigns_today(date=today),
            reply_markup=await ikb.call_campaigns_menu(campaigns=campaigns, page=1)
        )
    else:
        await message.answer(text=txt.no_call_campaigns_today(date=today))


@router.callback_query(ikb.CallCampaignCallbackData.filter(F.action == 'PageCampaigns'))
async def page_campaigns(
    callback: CallbackQuery,
    callback_data: ikb.CallCampaignCallbackData
) -> None:
    await callback.answer()
    today = datetime.now().strftime('%d.%m.%Y')
    campaigns = await db.get_active_campaigns_by_date(date_str=today)
    await callback.message.edit_reply_markup(
        reply_markup=await ikb.call_campaigns_menu(campaigns=campaigns, page=callback_data.page)
    )


@router.callback_query(ikb.CallCampaignCallbackData.filter(F.action == 'BackToCampaigns'))
async def back_to_campaigns(
    callback: CallbackQuery,
    callback_data: ikb.CallCampaignCallbackData
) -> None:
    await callback.answer()
    today = datetime.now().strftime('%d.%m.%Y')
    campaigns = await db.get_active_campaigns_by_date(date_str=today)
    await callback.message.edit_text(
        text=txt.call_campaigns_today(date=today),
        reply_markup=await ikb.call_campaigns_menu(campaigns=campaigns, page=callback_data.page)
    )


@router.callback_query(ikb.CallCampaignCallbackData.filter(F.action == 'OpenCampaign'))
async def open_campaign(
    callback: CallbackQuery,
    callback_data: ikb.CallCampaignCallbackData
) -> None:
    await callback.answer()
    results = await db.get_campaign_results(campaign_id=callback_data.campaign_id)
    results = [r for r in results if r.worker is not None]
    results = sorted(results, key=lambda r: (r.worker.last_name, r.worker.first_name, r.worker.middle_name))
    await callback.message.edit_text(
        text=txt.call_campaign_workers_list(),
        reply_markup=await ikb.call_campaign_workers_menu(
            results=results,
            campaign_id=callback_data.campaign_id,
            date=callback_data.date or '',
            page=callback_data.page
        )
    )


@router.callback_query(ikb.CallCampaignCallbackData.filter(F.action == 'ShowWorkerPhones'))
async def show_worker_phones(
    callback: CallbackQuery,
    callback_data: ikb.CallCampaignCallbackData
) -> None:
    await callback.answer()
    result = await db.get_call_result(result_id=callback_data.result_id)

    if not result or not result.worker_id:
        await callback.answer(text='Данные исполнителя не найдены', show_alert=True)
        return

    user = await db.get_user_by_id(user_id=result.worker_id)
    real_data = await db.get_user_real_data_by_id(user_id=result.worker_id)
    status_emoji = ikb.STATUS_EMOJI.get(result.status, '⏳')

    full_name = '—'
    if real_data:
        full_name = f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}'

    await callback.message.edit_text(
        text=txt.call_worker_info(
            full_name=full_name,
            status_emoji=status_emoji,
            phone_tg=user.phone_number if user else '—',
            phone_real=real_data.phone_number if real_data else '—',
            call_phone=result.phone_number
        ),
        reply_markup=ikb.worker_phones_keyboard(
            campaign_id=callback_data.campaign_id,
            date=callback_data.date or '',
            page=callback_data.page
        )
    )
