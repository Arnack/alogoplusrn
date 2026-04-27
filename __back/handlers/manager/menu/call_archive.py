from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from utils import validate_date
import keyboards.inline as ikb
from filters import Manager
import database as db
import texts as txt

router = Router()
router.message.filter(Manager())
router.callback_query.filter(Manager())


@router.message(F.text == '📋 Архив прозвонов')
async def open_call_archive(message: Message, state: FSMContext) -> None:
    """Запросить дату для архива прозвонов."""
    await message.answer(text=txt.request_call_archive_date())
    await state.set_state('RequestCallArchiveDate')


@router.callback_query(F.data == 'BackToCallArchive')
async def back_to_call_archive(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_text(text=txt.request_call_archive_date())
    await state.set_state('RequestCallArchiveDate')


@router.message(F.text, StateFilter('RequestCallArchiveDate'))
async def get_call_archive_date(message: Message, state: FSMContext) -> None:
    is_valid, formatted_date = validate_date(date_str=message.text)
    if not is_valid:
        await message.answer(text=txt.archive_date_error())
        return

    await state.clear()
    campaigns = await db.get_campaigns_by_date(date_str=formatted_date)

    if not campaigns:
        await message.answer(text=txt.no_call_campaigns_archive(date=formatted_date))
        return

    await message.answer(
        text=txt.call_campaigns_archive(date=formatted_date),
        reply_markup=await ikb.call_campaigns_menu(campaigns=campaigns, page=1)
    )


@router.callback_query(ikb.CallCampaignCallbackData.filter(F.action == 'OpenCampaign'))
async def archive_open_campaign(
    callback: CallbackQuery,
    callback_data: ikb.CallCampaignCallbackData
) -> None:
    """Открыть список исполнителей кампании из архива."""
    await callback.answer()
    results = await db.get_campaign_results(campaign_id=callback_data.campaign_id)
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
