from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from utils import (
    get_day_of_week_by_date,
    validate_date
)
import keyboards.inline as ikb
from filters import Manager
import database as db
import texts as txt


router = Router()
router.message.filter(Manager())
router.callback_query.filter(Manager())


@router.message(F.text == '🗂️ Архив')
async def open_archive(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_date_all_formats()
    )
    await state.set_state('RequestArchiveDate')


async def open_archive_menu(
        event: Message | CallbackQuery,
        menu_page: int,
        date: str
) -> None:
    orders = await db.get_archive_orders(
        archive_date=date
    )
    if orders:
        if isinstance(event, Message):
            await event.answer(
                text=txt.archive_orders_info(),
                reply_markup=await ikb.archive_orders_menu(
                    archive_orders=orders,
                    menu_page=menu_page,
                    date=date
                )
            )
        else:
            await event.message.edit_text(
                text=txt.archive_orders_info(),
                reply_markup=await ikb.archive_orders_menu(
                    archive_orders=orders,
                    menu_page=menu_page,
                    date=date
                )
            )
    else:
        if isinstance(event, Message):
            await event.answer(
                text=txt.no_archive_orders(
                    date=date
                )
            )
        else:
            await event.message.edit_text(
                text=txt.no_archive_orders(
                    date=date
                )
            )


@router.message(F.text, StateFilter('RequestArchiveDate'))
async def get_archive_date(
        message: Message,
        state: FSMContext
):
    is_valid, formatted_date = validate_date(
        date_str=message.text
    )
    if is_valid:
        await state.set_state(None)
        await open_archive_menu(
            event=message,
            menu_page=1,
            date=formatted_date
        )
    else:
        await message.answer(
            text=txt.all_format_date_error()
        )


@router.callback_query(ikb.ShowArchiveOrderCallbackData.filter(F.action == 'BackToArchiveMenu'))
async def back_to_archive_orders_menu(
        callback: CallbackQuery,
        callback_data: ikb.ShowArchiveOrderCallbackData
):
    await open_archive_menu(
        event=callback,
        menu_page=callback_data.menu_page,
        date=callback_data.date
    )


@router.callback_query(ikb.ShowArchiveOrderCallbackData.filter(F.action == 'ForwardArchive'))
async def forward_archive_orders(
        callback: CallbackQuery,
        callback_data: ikb.ShowArchiveOrderCallbackData
):
    await open_archive_menu(
        event=callback,
        menu_page=callback_data.menu_page + 1,
        date=callback_data.date
    )


@router.callback_query(ikb.ShowArchiveOrderCallbackData.filter(F.action == 'BackArchive'))
async def back_archive_orders(
        callback: CallbackQuery,
        callback_data: ikb.ShowArchiveOrderCallbackData
):
    await open_archive_menu(
        event=callback,
        menu_page=callback_data.menu_page - 1,
        date=callback_data.date
    )


@router.callback_query(ikb.ShowArchiveOrderCallbackData.filter(F.action == 'OpenArchiveOrder'))
async def open_archive_order(
        callback: CallbackQuery,
        callback_data: ikb.ShowArchiveOrderCallbackData
):
    await callback.answer()
    archive_order = await db.get_archive_order(
        archive_id=callback_data.archive_id
    )
    archive_workers = await db.get_archive_order_workers(
        archive_id=archive_order.id
    )
    organization = await db.get_customer_organization(
        customer_id=archive_order.customer_id
    )
    await callback.message.edit_text(
        text=txt.open_archive_order(
            order_id=archive_order.order_id,
            city=archive_order.city,
            organization=organization,
            date=archive_order.date,
            job=archive_order.job_name,
            day_shift=archive_order.day_shift,
            night_shift=archive_order.night_shift,
            amount=archive_order.amount,
            real_workers_count=len(archive_workers),
            workers_count=archive_order.workers_count
        ),
        reply_markup=ikb.update_archive_order_workers_count(
            archive_id=archive_order.id,
            menu_page=callback_data.menu_page,
            date=callback_data.date
        )
    )


@router.callback_query(ikb.ShowArchiveOrderCallbackData.filter(F.action == 'UpdArchWorkersCount'))
async def confirmation_update_archive_workers(
        callback: CallbackQuery,
        callback_data: ikb.ShowArchiveOrderCallbackData
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.confirmation_update_archive_order_workers_count(),
        reply_markup=ikb.confirmation_update_archive_order_workers_count(
            archive_id=callback_data.archive_id,
            menu_page=callback_data.menu_page,
            date=callback_data.date
        )
    )


@router.callback_query(Manager(), F.data.startswith('ConfirmUpdateArchiveOrderWorkersCount:'))
async def update_archive_order_workers_count(
        callback: CallbackQuery,
        state: FSMContext
):
    archive_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(
        text=txt.enter_workers_count()
    )
    await state.update_data(
        ArchiveID=archive_id
    )
    await state.set_state("UpdateWorkersCount")


@router.message(Manager(), F.text, StateFilter("UpdateWorkersCount"))
async def save_archive_order_workers_count(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        await state.set_state(None)
        data = await state.get_data()
        archive_order = await db.get_archive_order(
            archive_id=data['ArchiveID']
        )
        result = await db.update_archive_order_workers_count(
            archive_id=data['ArchiveID'],
            workers_count=int(message.text)
        )

        if result[0]:
            users = await db.get_users_by_city(city=archive_order.city)
            workers = await db.get_order_workers_tg_id(order_id=result[1])
            day = get_day_of_week_by_date(date=archive_order.date)

            max_bot = None
            try:
                from maxapi import Bot as MaxBot
                from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                from max_worker_bot.keyboards import worker_keyboards as max_kb
                from config_reader import config as cfg
                if cfg.max_bot_token:
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
            except Exception:
                pass

            for user in users:
                if user.tg_id in workers:
                    continue

                job_fp = await db.get_job_fp_for_txt(
                    worker_id=user.id
                )
                order_text = await txt.sending_order_to_users(
                    city=archive_order.city,
                    customer_id=archive_order.customer_id,
                    job=archive_order.job_name,
                    date=archive_order.date,
                    day=day,
                    day_shift=archive_order.day_shift,
                    night_shift=archive_order.night_shift,
                    amount=archive_order.amount,
                    job_fp=job_fp,
                )
                if user.tg_id:
                    try:
                        await message.bot.send_message(
                            chat_id=user.tg_id,
                            text=order_text,
                            reply_markup=ikb.respond_to_an_order(
                                order_id=result[1]
                            ),
                            protect_content=True
                        )
                    except Exception:
                        pass
                if max_bot and user.max_id:
                    try:
                        await max_bot.send_message(
                            user_id=user.max_id,
                            text=order_text,
                            attachments=[max_kb.respond_to_an_order(order_id=result[1])],
                            parse_mode=MaxParseMode.HTML
                        )
                    except Exception:
                        pass

            if max_bot:
                try:
                    await max_bot.close_session()
                except Exception:
                    pass
        await message.answer(
            text=txt.archive_order_workers_updated()
        )
        await state.clear()
    else:
        await message.answer(
            text=txt.add_id_error()
        )
