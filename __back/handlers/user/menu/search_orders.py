from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime
from decimal import Decimal

import keyboards.inline as ikb
from utils import (
    get_day_of_week_by_date,
    get_rating_coefficient,
    get_rating
)
from utils.debtor_pricing import calculate_reduced_unit_price
from filters import Worker
import database as db
import texts as txt


router = Router()


async def open_order(
        callback: CallbackQuery,
        orders,
        page: int,
        withholding: int = 0,
) -> None:
    # Проверка bounds для page
    if not orders or page >= len(orders) or page < 0:
        await callback.answer("Заявки не найдены", show_alert=True)
        return

    day = get_day_of_week_by_date(date=orders[page].date)
    user = await db.get_user(
        tg_id=callback.from_user.id
    )
    job_fp = await db.get_job_fp_for_txt(
        worker_id=user.id
    )
    rating = await get_rating(
        user_id=user.id
    )
    coefficient = get_rating_coefficient(
        rating=rating[:-1]
    )
    unit_price = Decimal(orders[page].amount.replace(',', '.'))
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = round(unit_price * coefficient, 2)

    await callback.message.edit_text(
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
        reply_markup=await ikb.show_order_for_search(
            page=page + 1,
            orders=orders,
            order_id=orders[page].id,
        )
    )


async def open_customer_search_menu(
        event: CallbackQuery | Message,
        state: FSMContext
) -> None:
    data = await state.get_data()
    if data['SearchOrderFor'] == 'myself':
        user = await db.get_user(
            tg_id=event.from_user.id
        )
        user_id = user.id
        user_city = user.city
    else:
        user_id = data['FriendID']
        user_city = data['FriendCity']

    customers = []
    customers_id = await db.get_customers_id_by_city(city=user_city)
    for customer_id in customers_id:
        orders = await db.get_orders_for_search(
            worker_city=user_city,
            worker_id=user_id,
            customer_id=customer_id
        )
        if orders:
            customers.append(
                customer_id
            )

    if isinstance(event, CallbackQuery):
        try:
            page = data['CustomerSearchPage']
            items = data['CustomerSearchItems']
        except KeyError:
            page = 1
            items = 5

    else:
        page = 1
        items = 5

    await state.update_data(
        CustomerSearchPage=page,
        CustomerSearchItems=items
    )

    if isinstance(event, Message):
        await event.answer(
            text=txt.customer_search_orders(),
            reply_markup=await ikb.customer_search_orders(
                customers=customers,
                items=items,
                page=page
            ),
            protect_content=True
        )
    elif isinstance(event, CallbackQuery):
        await event.message.edit_text(
            text=txt.customer_search_orders(),
            reply_markup=await ikb.customer_search_orders(
                customers=customers,
                items=items,
                page=page
            )
        )


@router.callback_query(Worker(), F.data == 'BackToCustomerSearchOrders')
@router.message(Worker(), F.text == '🔍 Поиск заявок')
async def search_orders(
        event: Message | CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    await state.update_data(
        SearchOrderFor=order_for
    )
    await open_customer_search_menu(
        event=event,
        state=state
    )


@router.callback_query(Worker(), F.data == 'ForwardCustomerSearchOrders')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        CustomerSearchPage=data['CustomerSearchPage'] + 1,
        CustomerSearchItems=data['CustomerSearchItems'] + 5
    )
    await open_customer_search_menu(
        event=callback,
        state=state
    )


@router.callback_query(Worker(), F.data == 'BackCustomerSearchOrders')
async def moderation_applications(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(
        CustomerSearchPage=data['CustomerSearchPage'] - 1,
        CustomerSearchItems=data['CustomerSearchItems'] - 5
    )
    await open_customer_search_menu(
        event=callback,
        state=state
    )


@router.callback_query(Worker(), F.data.startswith('CustomerSearchOrders:'))
async def show_customer_orders(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    order_for = data.get('SearchOrderFor', 'myself')
    if order_for == 'myself':
        user = await db.get_user(
            tg_id=callback.from_user.id
        )
        user_id = user.id
        user_city = user.city
    else:
        user_id = data['FriendID']
        user_city = data['FriendCity']

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(
        customer_id_search=customer_id,
        worker_id=user_id,
        worker_city=user_city
    )

    orders = await db.get_orders_for_search(
        worker_city=user_city,
        worker_id=user_id,
        customer_id=customer_id
    )

    if orders:
        sorted_orders = sorted(
            orders,
            key=lambda order: datetime.strptime(
                f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
                '%d.%m.%Y %H:%M'
            )
        )

        await state.update_data(page=0)
        page = 0

        rating = await get_rating(
            user_id=user_id
        )
        coefficient = get_rating_coefficient(
            rating=rating[:-1]
        )
        withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user_id)
        await state.update_data(withholding=withholding)
        unit_price = Decimal(sorted_orders[page].amount.replace(',', '.'))
        if withholding > 0:
            amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
        else:
            amount = round(unit_price * coefficient, 2)
        job_fp = await db.get_job_fp_for_txt(
            worker_id=user_id,
        )

        day = get_day_of_week_by_date(date=sorted_orders[page].date)
        await callback.message.edit_text(
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
            reply_markup=await ikb.show_order_for_search(
                page=page + 1,
                order_id=sorted_orders[page].id,
                orders=sorted_orders
            )
        )
    else:
        await callback.answer(
            text=txt.no_orders_for_search(),
            show_alert=True
        )


@router.callback_query(Worker(), F.data == 'SearchOrderForward')
async def search_orders_forward(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
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
    await open_order(
        callback=callback,
        page=page,
        orders=sorted_orders,
        withholding=data.get('withholding', 0),
    )
    await state.update_data(page=page)


@router.callback_query(Worker(), F.data == 'SearchOrderBack')
async def search_orders_back(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
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
    await open_order(
        callback=callback,
        page=page,
        orders=sorted_orders,
        withholding=data.get('withholding', 0),
    )
    await state.update_data(page=page)


@router.callback_query(Worker(), F.data == 'BackToSearchOrders')
async def back_to_search_orders(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
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
    await open_order(
        callback=callback,
        page=data['page'],
        orders=sorted_orders,
        withholding=data.get('withholding', 0),
    )
