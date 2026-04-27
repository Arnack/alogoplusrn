from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from decimal import Decimal

from handlers.admin.menu.update_customer.cities.city_way.show_way import show_customer_city_way
import database as db
import texts as txt
from filters import Worker
import keyboards.inline as ikb
from utils import (
    get_day_of_week_by_date,
    get_rating_coefficient, get_rating
)
from utils.debtor_pricing import calculate_reduced_unit_price
from utils.refuse_assigned_worker import refuse_assigned_order_worker


router = Router()


async def open_order(
        callback: CallbackQuery,
        state: FSMContext,
        page: int
) -> None:
    user = await db.get_user(
        tg_id=callback.from_user.id
    )
    orders = await db.get_orders_by_worker_id(
        worker_id=user.id
    )

    # Проверка bounds для page
    if not orders or page >= len(orders) or page < 0:
        await callback.answer("Заявки не найдены", show_alert=True)
        return

    day = get_day_of_week_by_date(
        date=orders[page].date
    )
    rating = await get_rating(
        user_id=user.id
    )
    coefficient = get_rating_coefficient(
        rating=rating[:-1]
    )
    unit_price = Decimal(orders[page].amount.replace(',', '.'))
    withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user.id)
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = unit_price * coefficient

    await callback.message.edit_text(
        text=await txt.user_applications(
            worker_id=user.id,
            customer_id=orders[page].customer_id,
            order_id=orders[page].id,
            city=orders[page].city,
            job=orders[page].job_name,
            date=orders[page].date,
            day_shift=orders[page].day_shift,
            night_shift=orders[page].night_shift,
            amount=amount,
            day=day
        ),
        reply_markup=await ikb.remove_application(
            order_id=orders[page].id,
            tg_id=callback.from_user.id,
            worker_id=user.id,
            page=page + 1,
            count=len(orders),
            state=state
        )
    )


@router.callback_query(Worker(), F.data == 'Reject')
@router.message(Worker(), F.text == '📝 Управление заявкой')
async def open_applications_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    user = await db.get_user(tg_id=event.from_user.id)
    orders = await db.get_orders_by_worker_id(worker_id=user.id)
    if orders:
        if isinstance(event, Message):
            await state.update_data(applications_page=0)
            page = 0
            day = get_day_of_week_by_date(date=orders[page].date)

            rating = await get_rating(
                user_id=user.id
            )
            coefficient = get_rating_coefficient(
                rating=rating[:-1]
            )
            unit_price = Decimal(orders[page].amount.replace(',', '.'))
            withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user.id)
            if withholding > 0:
                amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
            else:
                amount = unit_price * coefficient

            await event.answer(
                text=await txt.user_applications(
                    worker_id=user.id,
                    customer_id=orders[page].customer_id,
                    order_id=orders[page].id,
                    city=orders[page].city,
                    job=orders[page].job_name,
                    date=orders[page].date,
                    day_shift=orders[page].day_shift,
                    night_shift=orders[page].night_shift,
                    amount=amount,
                    day=day
                ),
                reply_markup=await ikb.remove_application(
                    order_id=orders[page].id,
                    tg_id=event.from_user.id,
                    worker_id=user.id,
                    page=page + 1,
                    count=len(orders),
                    state=state
                ),
                protect_content=True
            )
        else:
            await event.answer()
            data = await state.get_data()
            await open_order(
                callback=event,
                state=state,
                page=data['applications_page']
            )
    else:
        if isinstance(event, Message):
            await event.answer(
                text=txt.application_none(),
                protect_content=True
            )
        else:
            await event.answer()
            await event.message.edit_text(text=txt.application_none())


@router.callback_query(Worker(), F.data == 'UserApplicationsForward')
async def user_applications_forward(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data.get('applications_page', 0) + 1
    await open_order(
        callback=callback,
        state=state,
        page=page
    )
    await state.update_data(applications_page=page)


@router.callback_query(Worker(), F.data == 'UserApplicationsBack')
async def user_applications_back(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data.get('applications_page', 0) - 1
    await open_order(
        callback=callback,
        state=state,
        page=page)
    await state.update_data(applications_page=page)


@router.callback_query(Worker(), F.data.startswith('RemoveApplication:'))
async def confirmation_remove_application(
        callback: CallbackQuery
):
    await callback.answer()
    application_id = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=txt.remove_application(),
        reply_markup=ikb.accept_remove_application(
            application_id=application_id
        )
    )


@router.callback_query(Worker(), F.data.startswith('RemoveWorker:'))
async def confirmation_remove_worker(
        callback: CallbackQuery
):
    await callback.answer()
    worker_app_id = int(callback.data.split(':')[1])
    order_worker = await db.get_worker_app_data(
        worker_app_id=worker_app_id
    )

    if not order_worker.added_by_manager:
        await callback.message.edit_text(
            text=txt.remove_worker(),
            reply_markup=ikb.confirmation_remove_worker(
                worker_id=worker_app_id
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.remove_worker_manager_app(),
            reply_markup=ikb.confirmation_remove_worker(
                worker_id=worker_app_id
            )
        )


@router.callback_query(Worker(), F.data.startswith('ConfirmRemoveApplication:'))
async def confirm_remove_application(
        callback: CallbackQuery
):
    await callback.answer()
    application_id = int(callback.data.split(':')[1])

    await db.delete_application(application_id=application_id)
    await callback.message.edit_text(text=txt.application_removed())


@router.callback_query(Worker(), F.data.startswith('ConfirmRemoveWorker:'))
async def confirm_remove_worker(
        callback: CallbackQuery
):
    worker_app_id = int(callback.data.split(':')[1])
    worker_app_data = await db.get_worker_app_data(worker_app_id=worker_app_id)
    user = await db.get_user(tg_id=callback.from_user.id)
    if not worker_app_data or worker_app_data.worker_id != user.id:
        await callback.answer('Ошибка', show_alert=True)
        return
    if await db.check_time(order_id=worker_app_data.order_id):
        await callback.answer(
            text=txt.cant_delete_application(),
            show_alert=True
        )
        return
    await callback.answer()
    await refuse_assigned_order_worker(
        worker_app_id=worker_app_id,
        actor_user=user,
        bot=callback.bot,
        tg_message=callback.message,
        skip_entry_checks=True,
    )


@router.callback_query(Worker(), F.data.startswith('WorkerShowCityWay:'))
async def worker_show_city_way(
        callback: CallbackQuery,
):
    await show_customer_city_way(
        callback=callback
    )
