from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaDocument
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import asyncio
from io import BytesIO

from utils.xlsx import create_jobs_fp_xlsx, get_jobs_fp_xlsx
from filters import Admin
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


async def send_jobs_fp_xlsx(
        callback: CallbackQuery,
        message_id: int,
) -> None:
    jobs_fp = await db.get_jobs_for_payment()
    if jobs_fp:
        xlsx_bytes = create_jobs_fp_xlsx(
            jobs_fp=jobs_fp,
        )
        xlsx_name = f"Услуги.xlsx"

        await callback.bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=message_id,
            media=InputMediaDocument(
                media=BufferedInputFile(
                    file=xlsx_bytes,
                    filename=xlsx_name,
                ),
            )
        )
    else:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=message_id,
            text=txt.jobs_fp_xlsx_error(),
        )


async def save_jobs_fp(
        message: Message,
        jobs_fp: list[dict],
        message_id: int,
) -> None:
    updated = await db.set_jobs_for_payment(
        jobs_fp=jobs_fp,
    )
    if updated:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=txt.jobs_fp_updated(),
        )
    else:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=txt.update_jobs_fp_error(),
        )


@router.message(F.text == '🛂 Наименование услуг')
async def jobs_fp_menu(
        message: Message
):
    await message.answer(
        text=txt.jobs_fp_menu(),
        reply_markup=ikb.jobs_fp_menu(),
    )


@router.callback_query(F.data == 'JobsFpList')
async def create_jobs_fp_xlsx_list(
        callback: CallbackQuery
):
    await callback.answer()
    msg = await callback.message.edit_text(
        text=txt.jobs_fp_xlsx()
    )
    asyncio.create_task(
        send_jobs_fp_xlsx(
            callback=callback,
            message_id=msg.message_id,
        )
    )


@router.callback_query(F.data == 'JobsFpAdd')
async def request_jobs_fp_xlsx(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_jobs_fp_xlsx(),
    )
    await state.set_state('GetJobsFpLXLSX')


@router.message(F.document, StateFilter('GetJobsFpLXLSX'))
async def get_jobs_fp_xlsx_file(
        message: Message,
        state: FSMContext,
):
    if message.document.file_name.endswith('.xlsx'):
        await state.set_state(None)
        document_data = await message.bot.get_file(
            file_id=message.document.file_id,
        )
        buffer = BytesIO()
        await message.bot.download_file(document_data.file_path, destination=buffer)
        buffer.seek(0)
        jobs_fp = get_jobs_fp_xlsx(
            xlsx_file=buffer.getvalue(),
        )

        msg = await message.reply(
            text=txt.jobs_fp_updating(),
        )

        asyncio.create_task(
            save_jobs_fp(
                message=message,
                jobs_fp=jobs_fp,
                message_id=msg.message_id,
            )
        )
    else:
        await message.answer(
            text=txt.xlsx_file_error(),
        )

