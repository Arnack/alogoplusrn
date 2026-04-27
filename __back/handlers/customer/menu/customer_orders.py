from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f
from datetime import datetime
from decimal import Decimal
import decimal
import logging
import asyncio

from utils import (
    delete_customer_order_notifications,
    PdfGenerator, get_day_of_week_by_date,
    validate_number, get_rating_coefficient,
    get_rating,
    schedule_expire_no_show_buttons,
    cancel_calls_for_order
)
from utils.debtor_pricing import calculate_reduced_unit_price
from filters import Customer, Manager, Admin, Director
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


def classify_workers_by_completion_status(
    order,
    workers: dict,
    workers_hours: dict,
    workers_statuses: dict
) -> tuple[list, list, list]:
    """
    Классифицирует исполнителей по статусам
    Returns: (reserve_workers, no_show_workers, extra_workers)
    """
    reserve_workers = []
    no_show_workers = []
    extra_workers = []

    for worker_id in workers:
        status = workers_statuses.get(worker_id, 'WORKED')
        hours = workers_hours.get(worker_id, '0')

        if status == 'NOT_OUT':
            # Не вышел - добавляем в no_show
            no_show_workers.append(worker_id)
        elif status == 'EXTRA':
            # Лишний - добавляем в extra
            extra_workers.append(worker_id)
        elif hours != 'Л' and hours != '0':
            # WORKED с нормальными единицами
            try:
                if Decimal(hours.replace(',', '.')) < Decimal('0.5'):
                    no_show_workers.append(worker_id)
            except:
                pass

    return reserve_workers, no_show_workers, extra_workers


async def open_customer_order(
        callback: CallbackQuery,
        state: FSMContext,
        page: int,
        admin_id: int = None
) -> None:
    user_id = admin_id if admin_id is not None else callback.from_user.id

    orders = await db.get_customer_orders(
        admin=user_id
    )
    try:
        sorted_orders = sorted(
            orders,
            key=lambda order: datetime.strptime(
                f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
                '%d.%m.%Y %H:%M'
            )
        )
        workers_count = await db.get_order_workers_count_by_order_id(order_id=sorted_orders[page].id)
        applications_count = await db.get_applications_count_by_order_id(order_id=sorted_orders[page].id)

        await callback.message.edit_text(
            text=txt.show_customer_order(
                order_id=sorted_orders[page].id,
                job=sorted_orders[page].job_name,
                date=sorted_orders[page].date,
                day_shift=sorted_orders[page].day_shift,
                night_shift=sorted_orders[page].night_shift,
                workers=sorted_orders[page].workers,
                city=sorted_orders[page].city,
                moderation=sorted_orders[page].moderation,
                in_progress=sorted_orders[page].in_progress,
                workers_count=workers_count,
                applications_count=applications_count),
            reply_markup=await ikb.show_order(
                page=page + 1,
                admin=user_id,
                order_id=sorted_orders[page].id,
                workers_count=workers_count)
        )
    except Exception as e:
        await state.clear()
        await state.update_data(page=0)
        if orders:
            await open_customer_order(
                callback=callback,
                state=state,
                page=0,
                admin_id=admin_id
            )
        logging.exception(f'\n\n{e}')


async def show_orders_list(
        callback: CallbackQuery,
        state: FSMContext
) -> None:
    await callback.answer()
    data = await state.get_data()
    all_orders = await db.get_orders_count_for_customer(admin=callback.from_user.id)

    if all_orders > 0:
        try:
            page = data['page']
        except KeyError:
            await state.update_data(page=0)
            page = 0

        await open_customer_order(
            callback=callback,
            state=state,
            page=page
        )
    else:
        await callback.message.edit_text(
            text=txt.no_orders_customer(),
            reply_markup=ikb.back_to_customer_menu()
        )


@router.callback_query(Customer(), F.data == 'AllCustomerOrders')
async def open_orders_list(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await show_orders_list(
        callback=callback,
        state=state
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data == 'CustomerOrderForward')
async def orders_forward(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data['page'] + 1
    admin_id = data.get('admin_as_customer_id')  # Get admin_id from state if admin working as customer
    await open_customer_order(
        callback=callback,
        state=state,
        page=page,
        admin_id=admin_id
    )
    await state.update_data(page=page)


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data == 'CustomerOrderBack')
async def orders_back(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    page = data['page'] - 1
    admin_id = data.get('admin_as_customer_id')  # Get admin_id from state if admin working as customer
    await open_customer_order(
        callback=callback,
        state=state,
        page=page,
        admin_id=admin_id
    )
    await state.update_data(page=page)


@router.callback_query(Manager(), F.data.startswith('CustomerGetPdf:'))
@router.callback_query(Customer(), F.data.startswith('CustomerGetPdf:'))
@router.callback_query(Admin(), F.data.startswith('CustomerGetPdf:'))
@router.callback_query(Director(), F.data.startswith('CustomerGetPdf:'))
async def create_pdf(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer(
        text=txt.order_pdf(),
        show_alert=True
    )
    await callback.message.delete()

    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(order_id=order_id)
    customer = await db.get_customer_info(customer_id=order.customer_id)

    # Проверяем, работает ли админ от имени заказчика
    state_data = await state.get_data()
    admin_mode = state_data.get('admin_as_customer', False)

    # Пытаемся получить менеджера по текущему пользователю (тот кто формирует документ)
    # Если это не менеджер, используем order.manager (назначенного менеджера)
    current_manager = await db.get_manager(manager_tg_id=callback.from_user.id)
    if current_manager:
        manager = current_manager
    else:
        manager = await db.get_manager(manager_tg_id=order.manager)

    workers = await db.get_workers_for_pdf(order_id=order_id)

    generator = PdfGenerator()
    shift = order.day_shift if order.day_shift else order.night_shift
    pdf_data = {
        'order_id': order.id,
        'city': order.city,
        'organization': customer.organization,
        'date': order.date,
        'start_shift': shift.split('-')[0],
        'end_shift': shift.split('-')[1],
        'manager': 'Платформа «Алгоритм плюс»' if admin_mode else (manager.manager_full_name if manager else 'Не назначен'),
        'manager_tg_id': manager.manager_id if manager else 0,
        'workers': [
            {'last_name': workers[worker_id]['last_name'],
             'first_name': workers[worker_id]['first_name'],
             'middle_name': workers[worker_id]['middle_name'],
             'position': order.job_name}
            for worker_id in workers
        ]
    }

    pdf_bytes = await generator.generate_pdf_start_shift(data=pdf_data)

    shift_name = 'Д' if order.day_shift else 'Н'
    pdf_date = datetime.strptime(order.date, '%d.%m.%Y')
    pdf_name = f"{customer.organization} {datetime.strftime(pdf_date, '%d_%m_%y')}_{shift_name}.pdf"

    await callback.message.answer_document(
        document=BufferedInputFile(
            file=pdf_bytes,
            filename=pdf_name
        ),
        caption=txt.order_pdf_info()
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('CustomerOrderFinish:'))
async def order_finish(
        callback: CallbackQuery
):
    order_id = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=txt.confirmation_order_finish(),
        reply_markup=ikb.confirmation_order_finish(
            order_id=order_id
        )
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('ConfirmOrderFinish:'))
async def confirm_order_finish(
        callback: CallbackQuery
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])

    # Автоматическое удаление дублей исполнителей
    duplicates_count = await db.remove_duplicate_workers(order_id=order_id)

    if duplicates_count > 0:
        logging.info(f'Удалено {duplicates_count} дубликатов исполнителей для заявки {order_id}')

    await callback.message.edit_text(
        text=txt.confirmation_common_hours(),
        reply_markup=ikb.confirmation_common_hours(
            order_id=order_id
        )
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('ConfirmCommonHours:'))
async def confirm_common_hours(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_common_hours()
    )
    await state.update_data(
        order_id=int(callback.data.split(':')[1])
    )
    await state.set_state('GetCommonHours')


@router.message(or_f(Customer(), Admin(), Director()), F.text, StateFilter('GetCommonHours'))
async def get_common_hours(
        message: Message,
        state: FSMContext
):
    if validate_number(message.text):
        data = await state.get_data()
        await state.update_data(
            CommonHours=message.text.replace(',', '.')
        )
        workers_count = await db.get_order_workers_count_by_order_id(
            order_id=data['order_id']
        )
        await message.answer(
            text=txt.confirmation_set_common_hours(
                order_workers_count=workers_count,
                common_hours=message.text
            ),
            reply_markup=ikb.confirmation_set_common_hours(
                order_id=data['order_id']
            )
        )
        await state.set_state(None)
    else:
        await message.answer(
            text=txt.validate_number_error()
        )


async def set_hours_to_order_workers(
        event: Message | CallbackQuery,
        state: FSMContext,
        data: dict,
        workers: dict,
        workers_hours: dict
) -> None:
    await event.message.edit_text(
        txt.order_end(
            order_id=data['order_id']
        )
    )

    order = await db.get_order(order_id=data['order_id'])
    customer = await db.get_customer_info(customer_id=order.customer_id)

    # Получаем статусы исполнителей
    workers_statuses = data.get('workers_statuses', {})

    # Классифицировать исполнителей
    reserve_workers, no_show_workers, extra_workers = classify_workers_by_completion_status(
        order=order,
        workers=workers,
        workers_hours=workers_hours,
        workers_statuses=workers_statuses
    )

    # Получить сумму компенсации для заказчика
    travel_compensation = await db.get_travel_compensation(customer_id=order.customer_id)

    # Проверяем, работает ли админ от имени заказчика
    state_data = await state.get_data()
    admin_mode = state_data.get('admin_as_customer', False)

    # Определяем кто сформировал документ (менеджер/директор, одобривший заявку)
    end_shift_manager_name = None
    end_shift_manager_position = None
    end_shift_manager_tg_id = order.manager
    if end_shift_manager_tg_id:
        director = await db.get_director_by_tg_id(end_shift_manager_tg_id)
        if director:
            end_shift_manager_position = "Директор"
            end_shift_manager_name = director.full_name
        else:
            manager = await db.get_manager(end_shift_manager_tg_id)
            if manager:
                end_shift_manager_position = "Менеджер"
                end_shift_manager_name = manager.manager_full_name

    customer_admin = await db.get_customer_admin(
        admin_tg_id=event.from_user.id,
    )

    generator = PdfGenerator()
    shift = order.day_shift if order.day_shift else order.night_shift
    end_shift_pdf_data = {
        'order_id': order.id,
        'city': order.city,
        'organization': customer.organization,
        'date': order.date,
        'start_shift': shift.split('-')[0],
        'end_shift': shift.split('-')[1],
        'customer_admin': f'{customer_admin.admin_full_name} Telegram ID {customer_admin.admin}' if customer_admin else 'Платформа «Алгоритм Плюс»',
        'manager_position': end_shift_manager_position,
        'manager_name': end_shift_manager_name,
        'manager_tg_id': end_shift_manager_tg_id,
        'workers': [
            {'last_name': workers[worker_id]['last_name'],
             'first_name': workers[worker_id]['first_name'],
             'middle_name': workers[worker_id]['middle_name'],
             'position': order.job_name,
             'hours': workers_hours[worker_id]}
            for worker_id in workers
            if worker_id not in extra_workers and worker_id not in no_show_workers
            and workers_hours.get(worker_id, '0').replace(',', '.').replace('Л', '0')
            and Decimal(workers_hours.get(worker_id, '0').replace(',', '.').replace('Л', '0')) > Decimal('0')
        ],
        'bad_workers': [
            f"{workers[worker_id]['last_name']} {workers[worker_id]['first_name']} {workers[worker_id]['middle_name']}"
            for worker_id in no_show_workers
        ],
        'extra_workers': [
            f"{workers[worker_id]['last_name']} {workers[worker_id]['first_name']} {workers[worker_id]['middle_name']}"
            for worker_id in extra_workers
        ]
    }

    for worker_id in workers:
        # Резервных исполнителей, лишних и не вышедших пропускаем полностью
        if worker_id in reserve_workers or worker_id in extra_workers or worker_id in no_show_workers:
            continue

        # Phase 6.4: для РР-работников локальный рейтинг не обновляем
        _ow = await db.get_order_worker(worker_id=int(worker_id), order_id=data['order_id'])
        if getattr(_ow, 'is_rr_worker', False):
            continue

        user_rating = await db.get_user_rating(
            user_id=int(worker_id)
        )
        if not user_rating:
            await db.set_rating(user_id=int(worker_id))

        try:
            hours_value = Decimal(workers_hours.get(worker_id, '0').replace(',', '.'))
            if hours_value > Decimal('0'):
                await db.update_rating_successful_orders(user_id=int(worker_id))
        except (ValueError, decimal.InvalidOperation):
            # Если не удалось преобразовать часы в число, пропускаем
            logging.warning(f"Не удалось преобразовать часы для worker_id={worker_id}: {workers_hours.get(worker_id)}")

        # Увеличиваем total_orders только для НЕ резервных
        await db.update_rating_total_orders(user_id=int(worker_id))

    end_shift_pdf_bytes = await generator.generate_pdf_end_shift(
        data=end_shift_pdf_data
    )

    shift_name = 'Д' if order.day_shift else 'Н'
    pdf_date = datetime.strptime(order.date, '%d.%m.%Y')
    end_shift_pdf_name = f"{customer.organization} {datetime.strftime(pdf_date, '%d_%m_%y')}_{shift_name}.pdf"

    managers = await db.get_managers_tg_id()
    directors = await db.get_directors_tg_id()
    recipients = list(managers) + list(directors)
    for manager in recipients:
        try:
            await event.bot.send_document(
                chat_id=manager,
                document=BufferedInputFile(
                    file=end_shift_pdf_bytes,
                    filename=end_shift_pdf_name
                ),
                caption=txt.pdf_order_end_shift(
                    order_id=order.id
                )
            )
        except:
            pass

    total_sum_amount = Decimal('0')
    saving_sum_amount = Decimal('0')
    for worker_id in workers:
        # Пропускаем EXTRA и NO_SHOW исполнителей
        if worker_id in extra_workers or worker_id in no_show_workers:
            continue

        # Phase 6.4: РР-работники получают оплату через CRM, не через локальный реестр
        _ow_pay = await db.get_order_worker(worker_id=int(worker_id), order_id=data['order_id'])
        if getattr(_ow_pay, 'is_rr_worker', False):
            continue

        try:
            hours = Decimal(workers_hours.get(worker_id, '0').replace(',', '.'))
        except (ValueError, decimal.InvalidOperation):
            logging.warning(f"Не удалось преобразовать часы для worker_id={worker_id}: {workers_hours.get(worker_id)}")
            continue

        if hours > Decimal('0'):
            rating = await get_rating(
                user_id=int(worker_id)
            )
            coefficient = get_rating_coefficient(
                rating=rating[:-1]
            )
            unit_price = Decimal(order.amount.replace(',', '.'))
            # Проверить наличие активного цикла должника
            max_commission = await db.get_max_assigned_amount_for_active_cycle(worker_id=int(worker_id))

            if max_commission > 0:
                # Новая формула: удержание уже внутри сниженной цены
                reduced_unit = calculate_reduced_unit_price(unit_price, coefficient, max_commission)
                amount = reduced_unit * hours
            else:
                amount = (unit_price * coefficient) * hours

            # Расчёт дополнительного вознаграждения
            # Вычислить процент исполнения Заявки (исключаем EXTRA и NO_SHOW)
            completed_workers = sum(
                1 for wid in workers
                if wid not in extra_workers and wid not in no_show_workers
                and workers_hours.get(wid, '0').replace(',', '.').replace('Л', '0')
                and Decimal(workers_hours.get(wid, '0').replace(',', '.').replace('Л', '0')) >= Decimal('0.5')
            )
            completion_percent = (Decimal(completed_workers) / Decimal(order.workers)) * Decimal('100')
            # Округлить до двух знаков после запятой
            completion_percent = completion_percent.quantize(Decimal('0.01'))

            # Рассчитать дополнительное вознаграждение
            premium_bonus = await db.calculate_bonus_for_worker(
                customer_id=order.customer_id,
                worker_id=int(worker_id),
                completion_percent=completion_percent
            )

            # Сохранить данные о доп. вознаграждении для уведомления
            if premium_bonus > Decimal('0'):
                # Получить тип премии для уведомления
                premium_worker = await db.get_premium_worker(
                    customer_id=order.customer_id,
                    worker_id=int(worker_id)
                )
                await state.update_data(**{
                    f'premium_bonus_{worker_id}': {
                        'bonus': str(premium_bonus),
                        'completion_percent': str(completion_percent),
                        'bonus_type': premium_worker.bonus_type if premium_worker else 'unconditional'
                    }
                })

            final_amount = amount + premium_bonus

            total_sum_amount = total_sum_amount + (unit_price * hours)
            saving_sum_amount = saving_sum_amount + final_amount

            if final_amount > Decimal('0'):
                payment_id = await db.set_payment(
                    worker_id=int(worker_id),
                    order_id=order.id,
                    amount=str(int(final_amount))
                )

                # После выплаты должнику — автоматически закрываем цикл
                if max_commission > 0:
                    active_cycle = await db.get_active_cycle_for_worker(worker_id=int(worker_id))
                    if active_cycle:
                        await db.close_cycle_as_deducted(
                            cycle_id=active_cycle.id,
                            deducted_amount=max_commission,
                        )

                # Если начислено меньше 2600 рублей, деньги будут отправлены на баланс, а не на карту через РР
                if final_amount < Decimal('2600') and max_commission == 0:
                    await db.update_worker_balance_op(
                        worker_id=int(worker_id),
                        payment_id=payment_id,
                    )
    
    asyncio.create_task(
        db.set_or_update_saving(
            customer_id=order.customer_id,
            saving_amount=str(saving_sum_amount),
            total_amount=str(total_sum_amount),
            date=order.date
        )
    )

    accountants = await db.get_accountants_tg_id()
    for tg_id in accountants:
        try:
            await event.bot.send_document(
                chat_id=tg_id,
                document=BufferedInputFile(
                    file=end_shift_pdf_bytes,
                    filename=end_shift_pdf_name
                )
            )
        except Exception as e:
            logging.exception(f'Не удалось отправить смену кассиру {tg_id}: {e}')

    customer_admins = await db.get_customer_admins(
        customer_id=order.customer_id
    )
    for customer_admin in customer_admins:
        try:
            await event.bot.send_document(
                chat_id=customer_admin.admin,
                document=BufferedInputFile(
                    file=end_shift_pdf_bytes,
                    filename=end_shift_pdf_name
                ),
                caption=txt.pdf_order_end_shift(
                    order_id=order.id
                )
            )
        except Exception as e:
            logging.error(f'Не удалось отправить PDF представителю заказчика {customer_admin.admin}: {e}')

    customer_groups = await db.get_customer_groups(
        customer_id=order.customer_id
    )
    for group in customer_groups:
        try:
            await event.bot.send_document(
                chat_id=group.chat_id,
                document=BufferedInputFile(
                    file=end_shift_pdf_bytes,
                    filename=end_shift_pdf_name
                ),
                caption=txt.pdf_order_end_shift(
                    order_id=order.id
                )
            )
        except Exception as e:
            logging.error(f'Не удалось отправить PDF в группу {group.chat_id} ({group.group_name}): {e}')

    # Обработка EXTRA исполнителей (Лишних)
    for worker_id in extra_workers:
        # Создать или получить рейтинг
        user_rating = await db.get_user_rating(user_id=int(worker_id))
        if not user_rating:
            await db.set_rating(user_id=int(worker_id))

        # Увеличить plus на 1 (+1% к рейтингу)
        await db.update_rating_plus(user_id=int(worker_id), plus_value=1)

        # Получить tg_id исполнителя из БД
        try:
            worker = await db.get_user_by_id(user_id=int(worker_id))
            worker_tg_id = worker.tg_id
        except Exception as e:
            logging.error(f'Не удалось получить данные EXTRA исполнителя {worker_id}: {e}')
            continue

        # Отправить уведомление
        try:
            if travel_compensation and travel_compensation > 0:
                # С компенсацией
                await event.bot.send_message(
                    chat_id=worker_tg_id,
                    text=txt.extra_worker_notification_with_compensation(
                        amount=travel_compensation
                    )
                )
            else:
                # Без компенсации
                await event.bot.send_message(
                    chat_id=worker_tg_id,
                    text=txt.extra_worker_notification_without_compensation()
                )
        except Exception as e:
            logging.error(f'Не удалось отправить уведомление EXTRA исполнителю {worker_id}: {e}')

    for worker_id in workers:
        # Пропускаем резервных, лишних и не вышедших исполнителей
        if worker_id in reserve_workers or worker_id in extra_workers or worker_id in no_show_workers:
            continue

        # Отправка уведомления о дополнительном вознаграждении
        state_data = await state.get_data()
        premium_info = state_data.get(f'premium_bonus_{worker_id}')

        try:
            hours_value = Decimal(workers_hours.get(worker_id, '0').replace(',', '.'))
            has_worked = hours_value > Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logging.warning(f"Не удалось преобразовать часы для worker_id={worker_id}: {workers_hours.get(worker_id)}")
            continue

        if premium_info and has_worked:
            premium_worker = await db.get_premium_worker(
                customer_id=order.customer_id,
                worker_id=int(worker_id)
            )

            if premium_worker:
                try:
                    worker_tg_id = workers[worker_id]['tg_id']

                    if premium_worker.bonus_type == 'unconditional':
                        notification = txt.premium_unconditional_notification(
                            bonus_amount=premium_info['bonus']
                        )
                    else:
                        notification = txt.premium_conditional_notification(
                            completion_percent=premium_info['completion_percent'],
                            bonus_amount=premium_info['bonus']
                        )

                    await event.bot.send_message(
                        chat_id=worker_tg_id,
                        text=notification
                    )
                except Exception as e:
                    logging.error(f'Не удалось отправить уведомление о премии исполнителю {worker_id}: {e}')

        is_ref = await db.is_referral(worker_id=int(worker_id))

        if is_ref:
            ref_settings = await db.get_settings()
            ref_info = await db.get_referral(worker_id=int(worker_id))
            if not ref_info.bonus:
                await db.update_shifts_for_referral(worker_id=int(worker_id))
                if ref_info.shifts_referral + 1 >= ref_settings.shifts:
                    user = await db.get_user(tg_id=ref_info.user)
                    user_data = await db.get_user_real_data_by_id(user_id=user.id)

                    try:
                        await event.bot.send_message(
                            chat_id=managers[0],
                            text=txt.ref_notification(
                                last_name=user_data.last_name,
                                first_name=user_data.first_name,
                                middle_name=user_data.middle_name,
                                amount=ref_settings.bonus
                            )
                        )
                    except Exception as e:
                        logging.error(f'Не удалось отправить реферальное уведомление менеджеру {managers[0]}: {e}')
                    await event.bot.send_message(
                        chat_id=ref_info.user,
                        text=txt.user_ref_notification(
                            last_name=workers[worker_id]['last_name'],
                            first_name=workers[worker_id]['first_name'],
                            middle_name=workers[worker_id]['middle_name'],
                            amount=ref_settings.bonus
                        )
                    )

    await db.set_archive_order(
        order_id=order.id,
        customer_id=order.customer_id,
        job_name=order.job_name,
        date=order.date,
        day_shift=order.day_shift if order.day_shift else None,
        night_shift=order.night_shift if order.night_shift else None,
        workers_count=order.workers,
        city=order.city,
        manager_tg_id=order.manager,
        amount=order.amount,
        workers_hours=workers_hours,
        workers_statuses=workers_statuses,
        travel_compensation=travel_compensation
    )

    # Обработка прогресса по акциям для каждого исполнителя
    try:
        from sqlalchemy import select as _sa_select
        from database.models import OrderWorkerArchive as _OWA, async_session as _sess
        _archived = await db.get_archived_order_by_ord_id(order_id=order.id)
        if _archived:
            async with _sess() as _s:
                _owa_list = (await _s.scalars(
                    _sa_select(_OWA).where(_OWA.archive_order_id == _archived.id)
                )).all()
            for _owa in _owa_list:
                import asyncio as _asyncio
                _asyncio.create_task(
                    db.check_and_process_promotion_progress(
                        worker_id=_owa.worker_id,
                        customer_id=order.customer_id,
                        archive_order_worker=_owa,
                        bot=event.bot,
                    )
                )
    except Exception as _promo_exc:
        logging.warning('[promo] Ошибка при обработке прогресса акций: %s', _promo_exc)

    # Phase 6.1/6.2: Передать рабочее время и бонусы в CRM РР, закрыть смену
    if getattr(order, 'rr_shift_id', None):
        from API.shift_gateway import save_worker_time, save_worker_additional_price, close_shift
        _rr_state_data = await state.get_data()
        for worker_id in workers:
            if worker_id in no_show_workers:
                continue
            worker_user = await db.get_user_by_id(user_id=int(worker_id))
            if worker_user and worker_user.api_id:
                hours_raw = workers_hours.get(worker_id, '0').replace(',', '.').replace('Л', '0')
                try:
                    hours_float = float(hours_raw) if hours_raw else 0.0
                except (ValueError, TypeError):
                    hours_float = 0.0
                if hours_float > 0:
                    try:
                        await save_worker_time(
                            shift_id=order.rr_shift_id,
                            worker_id=worker_user.api_id,
                            hours=hours_float,
                        )
                    except Exception as rr_exc:
                        logging.warning(f'[Phase6.1] save_worker_time failed worker={worker_id}: {rr_exc}')
                # Phase 6.2: Передать бонус в CRM РР (если есть premium_bonus)
                premium_info = _rr_state_data.get(f'premium_bonus_{worker_id}')
                if premium_info:
                    try:
                        bonus_amount = int(Decimal(premium_info.get('bonus', '0')))
                        if bonus_amount > 0:
                            await save_worker_additional_price(
                                shift_id=order.rr_shift_id,
                                worker_id=worker_user.api_id,
                                price=float(bonus_amount),
                                mass=False,
                            )
                    except Exception as rr_exc:
                        logging.warning(f'[Phase6.2] save_worker_additional_price failed worker={worker_id}: {rr_exc}')
        try:
            await close_shift(shift_id=order.rr_shift_id)
        except Exception as rr_exc:
            logging.warning(f'[Phase6.1] close_shift failed shift={order.rr_shift_id}: {rr_exc}')

    # Создание событий невыхода для no_show_workers
    if no_show_workers:
        archive_order = await db.get_latest_archive_order_for_order(order_id=order.id)

        for worker_id in no_show_workers:
            # Получить или создать активный цикл должника
            active_cycle = await db.get_active_cycle_for_worker(worker_id=int(worker_id))
            if not active_cycle:
                active_cycle = await db.create_debtor_cycle(worker_id=int(worker_id))

            # Создать событие невыхода
            no_show_event = await db.create_no_show_event(
                cycle_id=active_cycle.id,
                order_archive_id=archive_order.id if archive_order else None,
                no_show_date=order.date,
                assigned_amount=3000
            )

            # Получить реальные данные исполнителя для карточки
            worker_real = await db.get_user_real_data_by_id(user_id=int(worker_id))
            full_name = f"{worker_real.last_name} {worker_real.first_name} {worker_real.middle_name}"

            # Отправить карточки всем кассирам
            accountants_full = await db.get_accountants()
            for acc in accountants_full:
                try:
                    card_text = (
                        f"⚠️ <b>Договорная комиссия</b>\n\n"
                        f"Самозанятый: <b>{full_name}</b>\n"
                        f"Дата заявки: <b>{order.date}</b> (Заявка №{order.id})\n"
                        f"Назначено: <b>3 000 ₽</b>\n\n"
                        f"⚠️ Подтвердите сумму или измените её (от 1 до 3 000 ₽).\n"
                        f"Кнопки будут активны 24 часа."
                    )

                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="✅ Подтвердить 3 000 ₽",
                                    callback_data=f"NoShowConfirm:{no_show_event.id}"
                                ),
                                InlineKeyboardButton(
                                    text="✏️ Изменить сумму",
                                    callback_data=f"NoShowChangeAmount:{no_show_event.id}"
                                )
                            ]
                        ]
                    )

                    sent_msg = await event.bot.send_message(
                        chat_id=acc.tg_id,
                        text=card_text,
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )

                    await db.add_cashier_message(
                        event_id=no_show_event.id,
                        cashier_tg_id=acc.tg_id,
                        message_id=sent_msg.message_id
                    )
                except Exception as e:
                    logging.error(f'Ошибка отправки карточки неявки кассиру {acc.tg_id}: {e}')

            # Запланировать истечение кнопок через 24 часа
            await schedule_expire_no_show_buttons(event_id=no_show_event.id)

    await cancel_calls_for_order(order_id=order.id)
    await db.f_delete_order(order_id=order.id)
    await delete_customer_order_notifications(
        customer_id=order.customer_id,
        order_id=order.id
    )
    await state.clear()

    for tg_id in accountants:
        try:
            await event.bot.send_message(
                chat_id=tg_id,
                text=txt.order_finish_accountant_notification(),
            )
        except Exception as e:
            logging.exception(e)


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('ConfirmSetCommonHours:'))
async def confirm_set_common_hours(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    workers = await db.get_workers_for_pdf(
        order_id=int(callback.data.split(':')[1])
    )
    sorted_workers = dict(sorted(
        workers.items(),
        key=lambda item: item[1]['last_name']
    ))
    workers_hours = {}
    for key in sorted_workers:
        workers_hours[key] = data['CommonHours']

    await set_hours_to_order_workers(
        event=callback,
        state=state,
        data=data,
        workers=sorted_workers,
        workers_hours=workers_hours
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('CancelCommonHours:'))
async def cancel_common_hours(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    workers = await db.get_workers_for_pdf(order_id=order_id)
    # Сортируем самозанятых в алфавитном порядке по Фамилии
    sorted_workers = dict(sorted(
        workers.items(),
        key=lambda item: item[1]['last_name']
    ))

    worker_id = next(iter(sorted_workers))
    try:
        await callback.message.edit_text(
            text=txt.worker_hours(
                last_name=sorted_workers[worker_id]['last_name'],
                first_name=sorted_workers[worker_id]['first_name'],
                middle_name=sorted_workers[worker_id]['middle_name']
            ),
            reply_markup=ikb.worker_status_selector(
                worker_id=worker_id,
                order_id=order_id,
                current_status=None
            )
        )
    except Exception:
        # Игнорируем ошибку, если сообщение не изменилось
        pass

    await state.update_data(
        workers=sorted_workers,
        workers_hours={},
        workers_statuses={},  # Новое поле для хранения статусов
        worker_page=0,
        order_id=order_id
    )
    await state.set_state("WorkerHours")


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('WorkerStatus:'))
async def set_worker_status(
        callback: CallbackQuery,
        state: FSMContext
):
    """Обработка нажатия на чекбокс статуса исполнителя"""
    await callback.answer()

    # Парсинг данных: WorkerStatus:NOT_OUT:worker_id:order_id
    parts = callback.data.split(':')
    status = parts[1]  # NOT_OUT или EXTRA
    worker_id = parts[2]
    order_id = int(parts[3])

    data = await state.get_data()
    workers = data.get('workers', {})
    workers_hours = data.get('workers_hours', {})
    workers_statuses = data.get('workers_statuses', {})
    keys = list(workers.keys())
    current_page = data.get('worker_page', 0)

    # Устанавливаем статус и значение для этого исполнителя
    workers_statuses[worker_id] = status

    # Для NOT_OUT ставим 0, для EXTRA ставим 'Л'
    if status == 'NOT_OUT':
        workers_hours[worker_id] = '0'
    elif status == 'EXTRA':
        workers_hours[worker_id] = 'Л'

    await state.update_data(
        workers_hours=workers_hours,
        workers_statuses=workers_statuses
    )

    # Переход к следующему исполнителю
    new_page = current_page + 1

    if new_page >= len(workers):
        # Все исполнители обработаны - показываем подтверждение
        try:
            await callback.message.edit_text(
                text=txt.confirmation_set_hours(
                    order_workers=workers,
                    workers_hours=workers_hours
                ),
                reply_markup=ikb.confirmation_set_hours()
            )
        except Exception:
            pass
        await state.update_data(
            workers=workers,
            workers_hours=workers_hours,
            workers_statuses=workers_statuses
        )
        await state.set_state(None)
    else:
        # Показываем следующего исполнителя
        await state.update_data(worker_page=new_page)
        next_worker_id = keys[new_page]
        try:
            await callback.message.edit_text(
                text=txt.worker_hours(
                    last_name=workers[next_worker_id]['last_name'],
                    first_name=workers[next_worker_id]['first_name'],
                    middle_name=workers[next_worker_id]['middle_name']
            ),
            reply_markup=ikb.worker_status_selector(
                worker_id=next_worker_id,
                order_id=order_id,
                current_status=None
            )
        )
        except Exception:
            pass


@router.message(or_f(Customer(), Admin(), Director()), F.text, StateFilter('WorkerHours'))
async def get_worker_hours(
        message: Message,
        state: FSMContext
):
    """Обработка текстового ввода единиц"""
    if validate_number(message.text):
        data = await state.get_data()
        workers_hours = data.get('workers_hours', {})
        workers_statuses = data.get('workers_statuses', {})
        workers: dict = data.get('workers', {})
        keys = list(workers.keys())
        current_page = data.get('worker_page', 0)
        current_worker_id = keys[current_page]

        # Сохраняем введённое значение
        workers_hours[current_worker_id] = message.text.replace(',', '.')
        # Статус WORKED (по умолчанию, если не выбран чекбокс)
        workers_statuses[current_worker_id] = 'WORKED'

        await state.update_data(
            workers_hours=workers_hours,
            workers_statuses=workers_statuses
        )

        new_page = current_page + 1

        if new_page >= len(workers):
            # Все исполнители обработаны
            await message.answer(
                txt.confirmation_set_hours(
                    order_workers=workers,
                    workers_hours=workers_hours
                ),
                reply_markup=ikb.confirmation_set_hours()
            )
            await state.update_data(
                workers=workers,
                workers_hours=workers_hours,
                workers_statuses=workers_statuses
            )
            await state.set_state(None)
        else:
            # Переход к следующему исполнителю
            await state.update_data(worker_page=new_page)
            next_worker_id = keys[new_page]
            await message.answer(
                text=txt.worker_hours(
                    last_name=workers[next_worker_id]['last_name'],
                    first_name=workers[next_worker_id]['first_name'],
                    middle_name=workers[next_worker_id]['middle_name']
                ),
                reply_markup=ikb.worker_status_selector(
                    worker_id=next_worker_id,
                    order_id=data['order_id'],
                    current_status=None
                )
            )
    else:
        await message.answer(
            text=txt.validate_number_error()
        )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('ConfirmSetHours'))
async def confirm_set_hours(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await set_hours_to_order_workers(
        event=callback,
        state=state,
        data=data,
        workers=data['workers'],
        workers_hours=data['workers_hours']
    )


@router.callback_query(Manager(), F.data.startswith('CustomerUpdateWorkers:'))
@router.callback_query(Customer(), F.data.startswith('CustomerUpdateWorkers:'))
@router.callback_query(Admin(), F.data.startswith('CustomerUpdateWorkers:'))
@router.callback_query(Director(), F.data.startswith('CustomerUpdateWorkers:'))
async def confirmation_update_workers(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    data = await state.get_data()
    # Если админ работает от имени заказчика, используем ID представителя заказчика
    tg_id = data.get('admin_as_customer_id', callback.from_user.id)
    await callback.message.edit_text(
        text=txt.accept_update_workers_count(),
        reply_markup=await ikb.accept_update_workers_count(
            order_id=order_id,
            tg_id=tg_id
        )
    )


@router.callback_query(Manager(), F.data.startswith('ApproveUpdateWorkersCount:'))
@router.callback_query(Customer(), F.data.startswith('ApproveUpdateWorkersCount:'))
@router.callback_query(Admin(), F.data.startswith('ApproveUpdateWorkersCount:'))
@router.callback_query(Director(), F.data.startswith('ApproveUpdateWorkersCount:'))
async def update_workers(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(text=txt.enter_workers_count())
    await state.update_data(order_id_for_update=order_id)
    await state.set_state("UpdateWorkers")


@router.message(Manager(), F.text, StateFilter("UpdateWorkers"))
@router.message(Customer(), F.text, StateFilter("UpdateWorkers"))
@router.message(Admin(), F.text, StateFilter("UpdateWorkers"))
@router.message(Director(), F.text, StateFilter("UpdateWorkers"))
async def save_workers_count(
        message: Message,
        state: FSMContext
):
    try:
        data = await state.get_data()
        result = await db.update_order_workers(
            order_id=data['order_id_for_update'],
            workers_count=int(message.text)
        )
        workers = await db.get_order_workers_tg_id(order_id=data['order_id_for_update'])
        order = await db.get_order(order_id=data['order_id_for_update'])
        await message.answer(text=txt.workers_count_updated())

        if result:
            users = await db.get_users_by_city(city=order.city)
            day = get_day_of_week_by_date(date=order.date)

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
                    city=order.city,
                    customer_id=order.customer_id,
                    job=order.job_name,
                    date=order.date,
                    day=day,
                    day_shift=order.day_shift,
                    night_shift=order.night_shift,
                    amount=order.amount,
                    job_fp=job_fp,
                )
                if user.tg_id:
                    try:
                        await message.bot.send_message(
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
    except ValueError:
        await message.answer(text=txt.add_id_error())
    finally:
        await state.clear()
