from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from decimal import Decimal
import asyncio

from filters import Director
from utils import get_day_of_week_by_date, get_rating, get_rating_coefficient
from utils.refuse_assigned_worker import strip_html_plain
import texts as txt
import keyboards.inline as ikb
import database as db
from utils import set_reminder


router = Router()


@router.callback_query(Director(), F.data.startswith('BackToApplications:'))
@router.callback_query(Director(), F.data.startswith('ApplicationsByOrder:'))
async def applications_moderation(
        callback: CallbackQuery
):
    order_id = int(callback.data.split(':')[1])
    count = await db.get_applications_count_by_order_id(order_id=order_id)
    if count > 0:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.applications_moderation(),
            reply_markup=await ikb.applications_menu(
                order_id=order_id
            )
        )
    else:
        await callback.answer(
            text=txt.no_applications_moderation(),
            show_alert=True
        )


@router.callback_query(Director(), F.data.startswith('Application:'))
async def open_application(
        callback: CallbackQuery
):
    try:
        await callback.answer()
        application_id = int(callback.data.split(':')[1])
        application = await db.get_application(application_id=application_id)
        order = await db.get_order(order_id=application.order_id)

        await callback.message.edit_text(
            text=await txt.application_info(
                application_id=application_id),
            reply_markup=ikb.application_moder(
                application_id=application_id,
                order_id=order.id
            )
        )
    except AttributeError:
        await callback.message.edit_text(text=txt.application_error())


@router.callback_query(Director(), F.data.startswith('ConfirmationApprove:'))
async def confirmation_approve_application(
        callback: CallbackQuery
):
    try:
        await callback.answer()
        application_id = callback.data.split(':')[1]

        await callback.message.edit_text(
            text=txt.approve_application(),
            reply_markup=ikb.approve_application(
                application_id=application_id
            )
        )
    except AttributeError:
        await callback.message.edit_text(text=txt.application_error())


@router.callback_query(Director(), F.data.startswith('ApproveApplication:'))
async def approve_application(
        callback: CallbackQuery
):
    try:
        application_id = int(callback.data.split(':')[1])
        application = await db.get_application(application_id=application_id)
        order = await db.get_order(order_id=application.order_id)
        user = await db.get_user_by_id(user_id=application.worker_id)

        await db.set_worker_to_order_workers(
            worker_id=application.worker_id,
            order_id=application.order_id,
            added_by_manager=False,
            order_from_friend=application.order_from_friend
        )
        asyncio.create_task(
            db.create_contracts_for_all_orgs(
                user_id=application.worker_id,
                order_id=application.order_id,
            )
        )
        await db.delete_application(application_id=application_id)

        day = get_day_of_week_by_date(date=order.date)
        rating = await get_rating(user_id=application.worker_id)
        coefficient = get_rating_coefficient(rating=rating[:-1])
        adjusted_amount = round(Decimal(order.amount.replace(',', '.')) * coefficient, 2)
        approved_text = await txt.approved_user_application(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day=day,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=adjusted_amount
        )
        try:
            await db.add_web_panel_notification(
                worker_id=application.worker_id,
                title='Ваша заявка подтверждена',
                body=strip_html_plain(approved_text),
            )
        except Exception:
            pass
        try:
            await callback.bot.send_message(
                chat_id=user.tg_id,
                text=approved_text,
                reply_markup=await ikb.way_to_work(
                    customer_id=order.customer_id,
                    city=order.city
                ),
                protect_content=True
            )
        except:
            pass

        if user.max_id:
            try:
                from maxapi import Bot as MaxBot
                from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                from max_worker_bot.keyboards import worker_keyboards as max_kb
                from config_reader import config as cfg
                if cfg.max_bot_token:
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                    max_way_kb = await max_kb.way_to_work(
                        customer_id=order.customer_id,
                        city=order.city
                    )
                    attachments = [max_way_kb] if max_way_kb else []
                    await max_bot.send_message(
                        user_id=user.max_id,
                        text=approved_text,
                        attachments=attachments,
                        parse_mode=MaxParseMode.HTML
                    )
                    await max_bot.close_session()
            except Exception:
                pass

        time = order.day_shift if order.day_shift else order.night_shift
        await set_reminder(
            tg_id=user.tg_id,
            order_id=order.id,
            date=order.date,
            order_time=time
        )

        await callback.answer(
            text=txt.application_approved(),
            show_alert=True
        )

        count = await db.get_applications_count_by_order_id(order_id=order.id)
        if count > 0:
            await callback.message.edit_text(
                text=txt.applications_moderation(),
                reply_markup=await ikb.applications_menu(
                    order_id=order.id
                )
            )
        else:
            await callback.message.edit_text(
                text=txt.no_applications_moderation(),
                reply_markup=ikb.applications_none(
                    order_id=order.id
                )
            )
    except AttributeError:
        await callback.message.edit_text(text=txt.application_error())


@router.callback_query(Director(), F.data.startswith('ConfirmationReject:'))
async def confirmation_reject_application(
        callback: CallbackQuery
):
    await callback.answer()
    application_id = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=txt.reject_application(),
        reply_markup=ikb.reject_application(
            application_id=application_id
        )
    )


@router.callback_query(Director(), F.data.startswith('RejectApplication:'))
async def reject_application(
        callback: CallbackQuery
):
    try:
        application_id = int(callback.data.split(':')[1])
        application = await db.get_application(application_id=application_id)
        order = await db.get_order(order_id=application.order_id)
        user = await db.get_user_by_id(user_id=application.worker_id)
        day = get_day_of_week_by_date(date=order.date)

        rejected_text = await txt.rejected_user_application(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=order.amount,
            day=day
        )
        try:
            await callback.bot.send_message(
                chat_id=user.tg_id,
                text=rejected_text,
                protect_content=True
            )
        except:
            pass

        if user.max_id:
            try:
                from maxapi import Bot as MaxBot
                from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                from config_reader import config as cfg
                if cfg.max_bot_token:
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                    await max_bot.send_message(
                        user_id=user.max_id,
                        text=rejected_text,
                        parse_mode=MaxParseMode.HTML
                    )
                    await max_bot.close_session()
            except Exception:
                pass

        await db.rating_plus_1(
            worker_id=user.id
        )

        await callback.answer(
            text=txt.application_rejected(),
            show_alert=True
        )

        await db.delete_application(application_id=application_id)

        count = await db.get_applications_count_by_order_id(order_id=order.id)
        if count > 0:
            await callback.message.edit_text(
                text=txt.applications_moderation(),
                reply_markup=await ikb.applications_menu(
                    order_id=order.id
                )
            )
        else:
            await callback.message.edit_text(
                text=txt.no_applications_moderation(),
                reply_markup=ikb.applications_none(
                    order_id=order.id
                 )
            )
    except AttributeError:
        await callback.message.edit_text(text=txt.application_error())
