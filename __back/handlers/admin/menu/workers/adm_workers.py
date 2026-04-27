from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import or_f

import keyboards.inline as ikb
from filters import Admin, Director
import database as db
import texts as txt


router = Router()


async def open_workers_menu(
        callback: CallbackQuery
):
    workers_count = await db.get_workers_count_for_stats()

    await callback.message.edit_text(
        text=txt.stats(
            workers_count=workers_count
        ),
        reply_markup=ikb.adm_workers_menu()
    )


@router.callback_query(or_f(Admin(), Director()), F.data.in_({'BlockCancel', 'BackToAdmWorkersMenu'}))
@router.message(or_f(Admin(), Director()), F.text == '👤 Исполнители (НПД)')
async def workers_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    await state.clear()
    workers_count = await db.get_workers_count_for_stats()

    if isinstance(event, Message):
        await event.answer(
            text=txt.stats(
                workers_count=workers_count
            ),
            reply_markup=ikb.adm_workers_menu()
        )
    else:
        if event.data == 'BlockCancel':
            await event.answer(
                text=txt.block_cancel(),
                show_alert=True
            )
        await open_workers_menu(
            callback=event
        )
