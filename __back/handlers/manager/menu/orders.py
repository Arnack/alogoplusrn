import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal

from utils import (
    is_number, get_rating,
    get_rating_coefficient
)
from filters import Manager, Director
from aiogram.filters import or_f
from utils import get_day_of_week_by_date
import texts as txt
import keyboards.inline as ikb
import database as db


router = Router()


async def open_order(
        callback: CallbackQuery,
        page: int
) -> None:
    orders = await db.get_orders_for_moderation()

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    organization = await db.get_customer_organization(customer_id=sorted_orders[page].customer_id)
    await callback.message.edit_text(
        text=txt.order_moderation(
            organization=organization,
            job=sorted_orders[page].job_name,
            date=sorted_orders[page].date,
            day_shift=sorted_orders[page].day_shift,
            night_shift=sorted_orders[page].night_shift,
            workers=sorted_orders[page].workers),
        reply_markup=await ikb.order_moder(
            page=page + 1,
            order_id=sorted_orders[page].id
        )
    )


@router.callback_query(or_f(Manager(), Director()), F.data == 'ModerationOrders')
async def moderation_orders(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    count = await db.get_orders_count_for_moderation()
    data = await state.get_data()

    if count > 0:
        try:
            page = data['page']
        except KeyError:
            await state.update_data(page=0)
            page = 0

        await open_order(
            callback=callback,
            page=page
        )
    else:
        await callback.message.edit_text(
            text=txt.no_orders_moderation(),
            reply_markup=ikb.back_to_moderation_menu()
        )


@router.callback_query(or_f(Manager(), Director()), F.data == 'ModerationOrderForward')
async def orders_forward(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data['page'] + 1
    await open_order(
        callback=callback,
        page=page
    )
    await state.update_data(page=page)


@router.callback_query(or_f(Manager(), Director()), F.data == 'ModerationOrderBack')
async def orders_back(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data['page'] - 1
    await open_order(
        callback=callback,
        page=page
    )
    await state.update_data(page=page)


@router.callback_query(F.data == 'None')
async def answer_none(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('Amount:'))
async def request_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(
        order_id=order_id
    )
    job_amount = await db.get_job_amount(
        job_name=order.job_name,
        customer_id=order.customer_id
    )
    if job_amount:
        await callback.message.edit_text(
            text=txt.add_order_amount_in_button(),
            reply_markup=ikb.amount_for_order_in_button(
                amount=job_amount
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.add_order_amount()
        )
        await state.set_state('Amount')
    await state.update_data(order_id=order_id)


async def confirmation_save_amount(
        event: Message | CallbackQuery,
        state: FSMContext,
        amount: str
):
    orders = await db.get_orders_for_moderation()
    data = await state.get_data()
    page = data['page']

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    await state.update_data(
        amount=amount.replace(',', '.'),
        order_id=sorted_orders[page].id
    )

    if isinstance(event, Message):
        await event.answer(
            text=txt.accept_amount(
                amount=amount,
                job=sorted_orders[page].job_name,
                date=sorted_orders[page].date,
                day_shift=sorted_orders[page].day_shift,
                night_shift=sorted_orders[page].night_shift,
                workers=sorted_orders[page].workers
            ),
            reply_markup=ikb.accept_order_moder()
        )
    elif isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_text(
            text=txt.accept_amount(
                amount=amount,
                job=sorted_orders[page].job_name,
                date=sorted_orders[page].date,
                day_shift=sorted_orders[page].day_shift,
                night_shift=sorted_orders[page].night_shift,
                workers=sorted_orders[page].workers
            ),
            reply_markup=ikb.accept_order_moder()
        )


@router.callback_query(or_f(Manager(), Director()), F.data.startswith('SetOrderAmount:'))
async def get_job_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    await confirmation_save_amount(
        event=callback,
        state=state,
        amount=callback.data.split(':')[1]
    )


@router.callback_query(or_f(Manager(), Director()), F.data == 'SetOtherAmount')
async def set_other_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_text(
        text=txt.add_order_amount()
    )
    await state.set_state('Amount')


@router.message(or_f(Manager(), Director()), F.text, StateFilter('Amount'))
async def get_job_amount(
        message: Message,
        state: FSMContext
):
    if is_number(message.text):
        await confirmation_save_amount(
            event=message,
            state=state,
            amount=message.text
        )
    else:
        await message.answer(text=txt.add_id_error())


@router.callback_query(or_f(Manager(), Director()), F.data == 'SaveAmount')
async def save_amount(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    order_id = data.get('order_id')
    amount = data.get('amount')
    if not order_id or not amount:
        await callback.answer(text=txt.amount_error(), show_alert=True)
        return
    try:
        await db.set_amount(
            order_id=order_id,
            amount=amount,
            manager=callback.from_user.id
        )
        await callback.answer(
            text=txt.amount_added(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.amount_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        count = await db.get_orders_count_for_moderation()

        if count > 0:
            await open_order(
                callback=callback,
                page=0
            )
        else:
            await callback.message.edit_text(
                text=txt.no_orders_moderation(),
                reply_markup=ikb.back_to_moderation_menu()
            )

        order = await db.get_order(order_id=order_id)
        users = await db.get_users_by_city(city=order.city)
        day = get_day_of_week_by_date(date=order.date)

        # Подготовка Max бота для уведомлений
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
            rating = await get_rating(
                user_id=user.id
            )
            coefficient = get_rating_coefficient(
                rating=rating[:-1]
            )
            am = round(Decimal(amount.replace(',', '.')) * coefficient, 2)
            job_fp = await db.get_job_fp_for_txt(
                worker_id=user.id
            )

            order_text = await txt.sending_order_to_users(
                city=order.city,
                customer_id=order.customer_id,
                job=order.job_name,
                date=order.date,
                day=day,
                day_shift=order.day_shift,
                night_shift=order.night_shift,
                amount=am,
                job_fp=job_fp,
            )
            if user.tg_id:
                try:
                    await callback.bot.send_message(
                        chat_id=user.tg_id,
                        text=order_text,
                        reply_markup=ikb.respond_to_an_order(
                            order_id=order.id
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
                        attachments=[max_kb.respond_to_an_order(order_id=order.id)],
                        parse_mode=MaxParseMode.HTML
                    )
                except Exception:
                    pass

        if max_bot:
            try:
                await max_bot.close_session()
            except Exception:
                pass
        await state.clear()
        await state.update_data(page=0)
