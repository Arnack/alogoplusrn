from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from decimal import Decimal
import asyncio
import logging

from utils import get_day_of_week_by_date
import keyboards.inline as ikb
from filters import Supervisor
import database as db
import texts as txt
from utils import get_day_of_week_by_date, get_rating, get_rating_coefficient, set_reminder
from utils.refuse_assigned_worker import strip_html_plain


router = Router()
router.message.filter(Supervisor())
router.callback_query.filter(Supervisor())


@router.message(F.text == '👤 Координатор')
async def supervisor_req_city(
        message: Message
):
    cities = await db.get_cities_name()

    await message.answer(
        text=txt.order_cities(),
        reply_markup=ikb.cities_for_supervisor(
            cities=cities
        )
    )


@router.callback_query(F.data.startswith('ReqSupervisorCity:'))
async def get_supervisor_city(
        callback: CallbackQuery
):
    await callback.answer()
    customers = await db.get_customers_by_city(
        city=callback.data.split(':')[1]
    )
    await callback.message.edit_text(
        text=txt.choose_customer(),
        reply_markup=ikb.choose_customer(
            customers=customers
        )
    )


async def open_supervisor_orders_menu(
        callback: CallbackQuery,
        customer_id: int,
        menu_page: int
) -> None:
    orders = await db.get_orders_for_supervisor(
        customer_id=customer_id
    )
    if orders:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.supervisor_orders_info(),
            reply_markup=await ikb.supervisor_orders_info(
                orders=orders,
                customer_id=customer_id,
                menu_page=menu_page
            )
        )
    else:
        await callback.answer(
            text=txt.supervisor_no_orders(),
            show_alert=True
        )


@router.callback_query(F.data.startswith('ReqSupervisorCust:'))
async def choose_customer_action(
        callback: CallbackQuery
):
    await open_supervisor_orders_menu(
        callback=callback,
        customer_id=int(callback.data.split(':')[1]),
        menu_page=1
    )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'BackToSupervisorOrders'))
async def back_to_supervisor_orders(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    await open_supervisor_orders_menu(
        callback=callback,
        customer_id=callback_data.customer_id,
        menu_page=callback_data.menu_page
    )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'ForwardSupervisorOrder'))
async def forward_supervisor_order(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    await open_supervisor_orders_menu(
        callback=callback,
        customer_id=callback_data.customer_id,
        menu_page=callback_data.menu_page + 1
    )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'BackSupervisorOrder'))
async def back_supervisor_order(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    await open_supervisor_orders_menu(
        callback=callback,
        customer_id=callback_data.customer_id,
        menu_page=callback_data.menu_page - 1
    )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'SupervisorOrder'))
async def open_supervisor_order(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.supervisor_order_actions(),
        reply_markup=ikb.supervisor_order_menu(
            customer_id=callback_data.customer_id,
            order_id=callback_data.order_id,
            menu_page=callback_data.menu_page
        )
    )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'SuperApplications'))
async def supervisor_order_applications(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    applications = await db.get_applications_for_moderation(
        order_id=callback_data.order_id
    )
    if applications:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.supervisor_applications(),
            reply_markup=await ikb.supervisor_applications(
                applications=applications,
                order_id=callback_data.order_id,
                customer_id=callback_data.customer_id,
                menu_page=callback_data.menu_page
            )
        )
    else:
        await callback.answer(
            text=txt.supervisor_no_applications(),
            show_alert=True
        )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'SuperWorkers'))
async def supervisor_order_workers(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData
):
    count = await db.get_order_workers_count_by_order_id(
        order_id=callback_data.order_id
    )
    if count > 0:
        await callback.answer()
        await callback.message.edit_text(
            text=txt.supervisor_applications(),
            reply_markup=await ikb.supervisor_order_workers(
                order_id=callback_data.order_id,
                customer_id=callback_data.customer_id,
                menu_page=callback_data.menu_page
            )
        )
    else:
        await callback.answer(
            text=txt.supervisor_no_order_workers(),
            show_alert=True
        )


@router.callback_query(ikb.ShowOrderCallbackData.filter(F.action == 'SuperAddWorker'))
async def supervisor_add_order_worker(
        callback: CallbackQuery,
        callback_data: ikb.ShowOrderCallbackData,
        state: FSMContext
):
    await callback.answer()
    await state.update_data(
        AccountAction='AddWorker',
        OrderID=callback_data.order_id,
        CustomerID=callback_data.customer_id,
        MenuPage=callback_data.menu_page
    )
    await callback.message.edit_text(
        text=txt.request_last_name()
    )
    await state.set_state('RequestLastName')


@router.callback_query(ikb.AddWorkerCallbackData.filter(F.action == 'ConfirmAddWorker'))
async def supervisor_confirm_add_worker(
        callback: CallbackQuery,
        callback_data: ikb.AddWorkerCallbackData,
        state: FSMContext
):
    try:
        await db.set_worker_to_order_workers(
            order_id=callback_data.order_id,
            worker_id=callback_data.worker_id,
            added_by_manager=True
        )
        asyncio.create_task(
            db.create_contracts_for_all_orgs(
                user_id=callback_data.worker_id,
                order_id=callback_data.order_id,
            )
        )

        order = await db.get_order(order_id=callback_data.order_id)
        user = await db.get_user_by_id(user_id=callback_data.worker_id)
        day = get_day_of_week_by_date(date=order.date)
        rating = await get_rating(user_id=callback_data.worker_id)
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
                worker_id=callback_data.worker_id,
                title='Ваша заявка подтверждена',
                body=strip_html_plain(approved_text),
            )
        except Exception:
            logging.exception('web_panel_notification save')

        if user.tg_id:
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
            except Exception:
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
            text=txt.supervisor_worker_added(),
            show_alert=True
        )
        worker = await db.get_user_by_id(
            user_id=callback_data.worker_id
        )
        worker_real_data = await db.get_user_real_data_by_id(
            user_id=callback_data.worker_id
        )
        order = await db.get_order(
            order_id=callback_data.order_id
        )
        organization = await db.get_customer_organization(
            customer_id=order.customer_id
        )
        day = get_day_of_week_by_date(
            date=order.date
        )
        try:
            await callback.bot.send_message(
                chat_id=worker.tg_id,
                text=txt.supervisor_notification_for_add_to_order_workers(
                    order=order,
                    customer=organization,
                    worker_full_name=f'{worker_real_data.last_name} '
                                     f'{worker_real_data.first_name} '
                                     f'{worker_real_data.middle_name}',
                    day=day
                )
            )
        except:
            pass
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.supervisor_add_worker_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await callback.message.edit_text(
            text=txt.supervisor_order_actions(),
            reply_markup=ikb.supervisor_order_menu(
                customer_id=callback_data.customer_id,
                order_id=callback_data.order_id,
                menu_page=callback_data.menu_page
            )
        )
