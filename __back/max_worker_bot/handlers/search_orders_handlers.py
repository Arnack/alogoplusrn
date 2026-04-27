"""
Обработчики поиска заявок для Max бота
Адаптировано из Telegram бота
"""
from datetime import datetime
from decimal import Decimal
from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from max_worker_bot.keyboards import worker_keyboards as kb
from max_worker_bot.states import SearchOrdersStates
from utils import (
    get_day_of_week_by_date,
    get_rating_coefficient,
    get_rating
)
from utils.max_delivery import remember_dialog_from_event
from utils.debtor_pricing import calculate_reduced_unit_price
import database as db
import texts.worker as txt


router = Router()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def open_order(event: MessageCallback, context: MemoryContext, orders, page: int, withholding: int = 0):
    """Открыть конкретную заявку по индексу страницы"""

    if not orders or page >= len(orders) or page < 0:
        await event.message.answer(text=txt.no_orders_for_search(), parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    if order_for == 'myself':
        user = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
        user_id = user.id
    else:
        user_id = data['FriendID']

    day = get_day_of_week_by_date(date=orders[page].date)
    rating = await get_rating(user_id=user_id)
    coefficient = get_rating_coefficient(rating=rating[:-1])
    unit_price = Decimal(orders[page].amount.replace(',', '.'))
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = round(unit_price * coefficient, 2)
    job_fp = await db.get_job_fp_for_txt(worker_id=user_id)

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=await txt.show_order_search(
                job=orders[page].job_name,
                date=orders[page].date,
                day=day,
                day_shift=orders[page].day_shift,
                night_shift=orders[page].night_shift,
                city=orders[page].city,
                customer_id=orders[page].customer_id,
                amount=amount,
                job_fp=job_fp,
            ),
            attachments=[await kb.show_order_for_search(
                page=page + 1,
                orders=orders,
                order_id=orders[page].id
            )],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=await txt.show_order_search(
                job=orders[page].job_name,
                date=orders[page].date,
                day=day,
                day_shift=orders[page].day_shift,
                night_shift=orders[page].night_shift,
                city=orders[page].city,
                customer_id=orders[page].customer_id,
                amount=amount,
                job_fp=job_fp,
            ),
            attachments=[await kb.show_order_for_search(
                page=page + 1,
                orders=orders,
                order_id=orders[page].id
            )],
            parse_mode=ParseMode.HTML
        )


async def open_customer_search_menu(event: MessageCreated | MessageCallback, context: MemoryContext):
    """Открыть меню выбора получателя услуг"""
    remember_dialog_from_event(event)

    data = await context.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    if order_for == 'myself':
        user = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
        user_id = user.id
        user_city = user.city
        if not user_city:
            await event.message.answer(
                text='❗ Ваш город не установлен. Перейдите в «Обо мне» → «Обновить данные» → «Город».',
                parse_mode=ParseMode.HTML
            )
            return
    else:
        user_id = data['FriendID']
        user_city = data['FriendCity']

    # Получаем список получателей услуг с доступными заявками
    customers = []
    customers_id = await db.get_customers_id_by_city(city=user_city)

    for customer_id in customers_id:
        orders = await db.get_orders_for_search(
            worker_city=user_city,
            worker_id=user_id,
            customer_id=customer_id
        )
        if orders:
            customers.append(customer_id)

    # Пагинация
    if isinstance(event, MessageCallback):
        page = data.get('CustomerSearchPage', 1)
        items = data.get('CustomerSearchItems', 5)
    else:
        page = 1
        items = 5

    await context.update_data(
        CustomerSearchPage=page,
        CustomerSearchItems=items
    )

    keyboard = await kb.customer_search_orders(
        customers=customers,
        items=items,
        page=page
    )

    if isinstance(event, MessageCreated):
        await event.message.answer(
            text=txt.customer_search_orders(),
            attachments=[keyboard],
            parse_mode=ParseMode.HTML
        )
    elif isinstance(event, MessageCallback):
        try:
            await event.bot.edit_message(message_id=event.message.body.mid,
                text=txt.customer_search_orders(),
                attachments=[keyboard],
                parse_mode=ParseMode.HTML
            )
        except (AttributeError, Exception):
            await event.message.answer(
                text=txt.customer_search_orders(),
                attachments=[keyboard],
                parse_mode=ParseMode.HTML
            )


# ==================== ПОИСК ЗАЯВОК ====================

@router.message_callback(F.callback.payload == 'BackToCustomerSearchOrders')
@router.message_callback(F.callback.payload == 'search_orders')
@router.message_created(F.message.body.text == '🔍 Поиск заявок')
async def search_orders(event: MessageCreated | MessageCallback, context: MemoryContext):
    """Открыть меню поиска заявок"""

    # Очищаем состояние при входе
    await context.clear()

    # Проверяем, зарегистрирован ли пользователь
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        if isinstance(event, MessageCreated):
            await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        else:
            await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    await context.update_data(SearchOrderFor=order_for)
    await open_customer_search_menu(event=event, context=context)


# ==================== НАВИГАЦИЯ ПО ПОЛУЧАТЕЛЯМ ====================

@router.message_callback(F.callback.payload == 'ForwardCustomerSearchOrders')
async def forward_customer_search(event: MessageCallback, context: MemoryContext):
    """Следующая страница получателей услуг"""

    data = await context.get_data()
    if data.get('CustomerSearchPage') is None:
        await event.message.answer(
            text='⚠️ Сессия устарела. Откройте поиск заново.',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return
    await context.update_data(
        CustomerSearchPage=data['CustomerSearchPage'] + 1,
        CustomerSearchItems=data['CustomerSearchItems'] + 5
    )
    await open_customer_search_menu(event=event, context=context)


@router.message_callback(F.callback.payload == 'BackCustomerSearchOrders')
async def back_customer_search(event: MessageCallback, context: MemoryContext):
    """Предыдущая страница получателей услуг"""

    data = await context.get_data()
    if data.get('CustomerSearchPage') is None:
        await event.message.answer(
            text='⚠️ Сессия устарела. Откройте поиск заново.',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return
    await context.update_data(
        CustomerSearchPage=data['CustomerSearchPage'] - 1,
        CustomerSearchItems=data['CustomerSearchItems'] - 5
    )
    await open_customer_search_menu(event=event, context=context)


# ==================== ПРОСМОТР ЗАЯВОК ПОЛУЧАТЕЛЯ ====================

@router.message_callback(F.callback.payload.startswith('CustomerSearchOrders:'))
async def show_customer_orders(event: MessageCallback, context: MemoryContext):
    """Показать заявки конкретного получателя услуг"""

    data = await context.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    if order_for == 'myself':
        user = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
        user_id = user.id
        user_city = user.city
    else:
        user_id = data['FriendID']
        user_city = data['FriendCity']

    customer_id = int(event.callback.payload.split(':')[1])

    await context.update_data(
        customer_id_search=customer_id,
        worker_id=user_id,
        worker_city=user_city
    )

    # Получаем заявки
    orders = await db.get_orders_for_search(
        worker_city=user_city,
        worker_id=user_id,
        customer_id=customer_id
    )

    if not orders:
        await event.message.answer(text=txt.no_orders_for_search(), parse_mode=ParseMode.HTML)
        return

    # Сортируем по дате и времени
    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    page = 0
    await context.update_data(page=page)

    rating = await get_rating(user_id=user_id)
    coefficient = get_rating_coefficient(rating=rating[:-1])
    withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user_id)
    await context.update_data(withholding=withholding)
    unit_price = Decimal(sorted_orders[page].amount.replace(',', '.'))
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = round(unit_price * coefficient, 2)

    job_fp = await db.get_job_fp_for_txt(worker_id=user_id)
    day = get_day_of_week_by_date(date=sorted_orders[page].date)

    # В Max можно редактировать только последнее сообщение
    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=await txt.show_order_search(
                job=sorted_orders[page].job_name,
                date=sorted_orders[page].date,
                day=day,
                day_shift=sorted_orders[page].day_shift,
                night_shift=sorted_orders[page].night_shift,
                city=sorted_orders[page].city,
                customer_id=sorted_orders[page].customer_id,
                amount=amount,
                job_fp=job_fp,
            ),
            attachments=[await kb.show_order_for_search(
                page=page + 1,
                order_id=sorted_orders[page].id,
                orders=sorted_orders
            )],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        # Если редактирование не удалось - отправляем новое сообщение
        await event.message.answer(
            text=await txt.show_order_search(
                job=sorted_orders[page].job_name,
                date=sorted_orders[page].date,
                day=day,
                day_shift=sorted_orders[page].day_shift,
                night_shift=sorted_orders[page].night_shift,
                city=sorted_orders[page].city,
                customer_id=sorted_orders[page].customer_id,
                amount=amount,
                job_fp=job_fp,
            ),
            attachments=[await kb.show_order_for_search(
                page=page + 1,
                order_id=sorted_orders[page].id,
                orders=sorted_orders
            )],
            parse_mode=ParseMode.HTML
        )


# ==================== НАВИГАЦИЯ ПО ЗАЯВКАМ ====================

@router.message_callback(F.callback.payload == 'SearchOrderForward')
async def search_orders_forward(event: MessageCallback, context: MemoryContext):
    """Следующая заявка"""

    data = await context.get_data()
    if data.get('page') is None or not data.get('worker_id'):
        await event.message.answer(
            text='⚠️ Сессия устарела. Откройте поиск заново.',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return

    page = data['page'] + 1

    orders = await db.get_orders_for_search(
        worker_city=data['worker_city'],
        worker_id=data['worker_id'],
        customer_id=data['customer_id_search']
    )

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    await open_order(event=event, context=context, orders=sorted_orders, page=page, withholding=data.get('withholding', 0))
    await context.update_data(page=page)


@router.message_callback(F.callback.payload == 'SearchOrderBack')
async def search_orders_back(event: MessageCallback, context: MemoryContext):
    """Предыдущая заявка"""

    data = await context.get_data()
    if data.get('page') is None or not data.get('worker_id'):
        await event.message.answer(
            text='⚠️ Сессия устарела. Откройте поиск заново.',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return

    page = data['page'] - 1

    orders = await db.get_orders_for_search(
        worker_city=data['worker_city'],
        worker_id=data['worker_id'],
        customer_id=data['customer_id_search']
    )

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    await open_order(event=event, context=context, orders=sorted_orders, page=page, withholding=data.get('withholding', 0))
    await context.update_data(page=page)


@router.message_callback(F.callback.payload == 'BackToSearchOrders')
async def back_to_search_orders(event: MessageCallback, context: MemoryContext):
    """Вернуться к текущей заявке"""

    data = await context.get_data()
    if data.get('page') is None or not data.get('worker_id'):
        await event.message.answer(
            text='⚠️ Сессия устарела. Откройте поиск заново.',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return

    orders = await db.get_orders_for_search(
        worker_city=data['worker_city'],
        worker_id=data['worker_id'],
        customer_id=data['customer_id_search']
    )

    sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    await open_order(event=event, context=context, orders=sorted_orders, page=data['page'], withholding=data.get('withholding', 0))


# ==================== ОТКЛИК НА ЗАЯВКУ ====================

@router.message_callback(F.callback.payload.startswith('RespondToOrder:'))
async def respond_to_order(event: MessageCallback, context: MemoryContext):
    """Обработка отклика на заявку"""

    order_id = int(event.callback.payload.split(':')[1])
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    # Проверка на совпадение даты с другими заявками
    order = await db.get_order(order_id=order_id)
    if not order:
        await event.message.answer(text="Заявка не найдена или уже закрыта.", parse_mode=ParseMode.HTML)
        return
    order_shift = f"{order.date} {'день' if order.day_shift else 'ночь'}"
    worker_dates = await db.get_worker_dates(worker_id=worker.id)

    if order_shift in worker_dates:
        await event.message.answer(text=txt.has_date(date_time=order_shift), parse_mode=ParseMode.HTML)
        return

    # Получаем рейтинг и показываем подтверждение
    rating = await get_rating(user_id=worker.id)
    total_orders, successful_orders, plus = await db.get_worker_stats(worker_id=worker.id)
    coefficient = get_rating_coefficient(rating=rating[:-1])

    # Разный текст в зависимости от рейтинга
    if float(rating[:-1]) < 93:
        data = await context.get_data()
        unit_price = Decimal(order.amount.replace(',', '.'))
        withholding = data.get('withholding', 0)
        if withholding > 0:
            display_amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
        else:
            display_amount = unit_price * coefficient
        confirmation_text = txt.confirmation_respond_low_rating(
            rating=rating,
            amount=display_amount,
            total_orders=total_orders,
            successful_orders=successful_orders,
            plus=plus,
        )
    else:
        confirmation_text = txt.confirmation_respond_high_rating()

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=confirmation_text,
            attachments=[kb.confirmation_respond_keyboard(order_id=order_id)],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=confirmation_text,
            attachments=[kb.confirmation_respond_keyboard(order_id=order_id)],
            parse_mode=ParseMode.HTML
        )


@router.message_callback(F.callback.payload.startswith('ConfirmRespond:'))
async def confirm_respond(event: MessageCallback, context: MemoryContext):
    """Подтверждение отклика на заявку"""

    order_id = int(event.callback.payload.split(':')[1])
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    data = await context.get_data()
    order_from_friend = data.get('SearchOrderFor') == 'friend'
    apply_worker_id = data['FriendID'] if order_from_friend else worker.id

    # Создаем отклик
    applied = await db.set_application(
        worker_id=apply_worker_id,
        order_id=order_id,
        order_from_friend=order_from_friend
    )

    if applied in ('ok', 'duplicate'):
        try:
            await event.bot.edit_message(message_id=event.message.body.mid,text=txt.send_respond(), parse_mode=ParseMode.HTML)
        except (AttributeError, Exception):
            await event.message.answer(text=txt.send_respond(), parse_mode=ParseMode.HTML)

        if applied == 'ok':
            # Уведомляем менеджеров если заявка набрала нужное количество откликов
            order = await db.get_order(order_id=order_id)
            applications_count = await db.get_applications_count_by_order_id(order_id=order_id)

            if applications_count == order.workers:
                managers = await db.get_managers_tg_id()
                directors = await db.get_directors_tg_id()
                recipients = list(managers) + list(directors)

                try:
                    from aiogram import Bot as TelegramBot
                    import texts.manager as txt_manager
                    from max_worker_bot.config_reader import config
                    telegram_bot = TelegramBot(token=config.bot_token.get_secret_value())
                    notification = await txt_manager.notification_by_order(
                        order_id=order_id,
                        customer_id=order.customer_id,
                        date=order.date,
                        day_shift=order.day_shift,
                        night_shift=order.night_shift,
                        workers_count=order.workers
                    )
                    for tg_id in recipients:
                        try:
                            await telegram_bot.send_message(
                                chat_id=tg_id,
                                text=notification,
                                parse_mode=ParseMode.HTML
                            )
                        except Exception:
                            pass
                    await telegram_bot.session.close()
                except Exception:
                    pass
    else:
        try:
            await event.bot.edit_message(message_id=event.message.body.mid,text=txt.no_respond_sent(), parse_mode=ParseMode.HTML)
        except (AttributeError, Exception):
            await event.message.answer(text=txt.no_respond_sent(), parse_mode=ParseMode.HTML)
