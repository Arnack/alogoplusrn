from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal
import asyncio
import logging

from utils.organizations import orgs_id, orgs_dict
from API import get_organization_balance
import keyboards.inline as ikb
from utils import validate_date, schedule_payment, write_accountant_op_log
from utils.max_delivery import send_max_message, is_dialog_unavailable_error
import database as db
import texts as txt
from Schemas import WorkerChangeAmountSchema


router = Router()


async def open_payment_menu(
        event: Message | CallbackQuery,
        menu_page: int,
        date: str
) -> None:
    orders = await db.get_orders_for_payment(
        date=date
    )
    if orders:
        if isinstance(event, Message):
            await event.answer(
                text=txt.payment_orders_info(),
                reply_markup=await ikb.orders_for_payments(
                    archive_orders=orders,
                    menu_page=menu_page,
                    date=date,
                )
            )
        else:
            await event.message.edit_text(
                text=txt.payment_orders_info(),
                reply_markup=await ikb.orders_for_payments(
                    archive_orders=orders,
                    menu_page=menu_page,
                    date=date,
                )
            )

        write_accountant_op_log(
            message=f'Кассир {event.from_user.id} | Заказы для выплаты найдены',
        )
    else:
        if isinstance(event, Message):
            await event.answer(
                text=txt.no_payments()
            )
        else:
            await event.message.edit_text(
                text=txt.no_payments()
            )

        write_accountant_op_log(
            message=f'Кассир {event.from_user.id} | Заказы для выплаты не найдены',
        )


async def create_registry_fp(
        callback: CallbackQuery,
        order_id: int,
        registry_id_in_db: int,
        archived_order: db.OrderArchive,
        org_id: int,
        organization: str,
        name: str,
) -> None:
    payments = await db.get_payments_by_order_id(
        order_id=order_id,
    )

    accountants = await db.get_accountants_tg_id()

    for payment in payments:
        notification_text = txt.payment_notification(
            order_date=archived_order.date,
            order_shift='Д' if archived_order.day_shift else 'Н',
            order_amount=payment.amount,
            customer=organization,
        )
        tg_sent = False
        try:
            await callback.bot.send_message(
                chat_id=payment.user.tg_id,
                text=notification_text,
                reply_markup=ikb.confirmation_payment_notification(
                    order_id=order_id,
                )
            )
            await db.payment_notification_sent(
                payment_id=payment.id
            )
            tg_sent = True
        except TelegramBadRequest:
            full_name = (
                f'{payment.user.last_name} '
                f'{payment.user.first_name} '
                f'{payment.user.middle_name}'
            ).strip()
            write_accountant_op_log(
                message=(
                    f'Кассир {callback.from_user.id} | Заказ №{order_id} | '
                    f'Чат не найден: {full_name} (ИНН {payment.user.inn})'
                ),
                level='ERROR',
            )
            for tg_id in accountants:
                try:
                    await callback.bot.send_message(
                        chat_id=tg_id,
                        text=txt.worker_chat_not_found(
                            full_name=full_name,
                            inn=payment.user.inn,
                        ),
                        parse_mode='HTML',
                    )
                except Exception:
                    pass
        except Exception as e:
            logging.exception(f'\n\n{e}')

        # Если у исполнителя есть Max ID — дублируем уведомление в Max
        if payment.user.max_id:
            max_bot = None
            try:
                from maxapi import Bot as MaxBot
                from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                from max_worker_bot.keyboards.worker_keyboards import confirmation_payment_keyboard
                from config_reader import config as cfg
                if cfg.max_bot_token:
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                    await send_max_message(
                        max_bot,
                        user_id=payment.user.max_id,
                        chat_id=getattr(payment.user, 'max_chat_id', 0) or None,
                        text=notification_text,
                        attachments=[confirmation_payment_keyboard(order_id=order_id)],
                        parse_mode=MaxParseMode.HTML,
                    )
                    if not tg_sent:
                        await db.payment_notification_sent(payment_id=payment.id)
            except Exception as e:
                if is_dialog_unavailable_error(e):
                    logging.warning(f'[max] Не удалось отправить уведомление о выплате пользователю {payment.user.max_id}: чат недоступен')
                else:
                    logging.exception(f'[max] Ошибка отправки уведомления о выплате: {e}')
            finally:
                if max_bot is not None:
                    try:
                        await max_bot.close_session()
                    except Exception:
                        pass

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Выполнена рассылка по исполнителям с подтверждением выплаты'
    )

    await schedule_payment(
        registry_id_in_db=registry_id_in_db,
        order_id=order_id,
        accountant_tg_id=callback.from_user.id,
        org_id=org_id,
        name=name,
    )


@router.message(F.text == 'Выплаты')
async def payment_request_date(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_date_all_formats()
    )
    await state.set_state('AccRequestDateForPayments')
    write_accountant_op_log(
        message=f'Кассир {message.from_user.id} | Открыл раздел выплаты',
    )


@router.message(F.text, StateFilter('AccRequestDateForPayments'))
async def payment_get_date(
        message: Message,
        state: FSMContext
):
    is_valid, formatted_date = validate_date(
        date_str=message.text
    )
    if is_valid:
        await state.set_state(None)
        await open_payment_menu(
            event=message,
            menu_page=1,
            date=formatted_date
        )
    else:
        await message.answer(
            text=txt.all_format_date_error()
        )
        write_accountant_op_log(
            message=f'Кассир {message.from_user.id} | Ввел дату неверно',
        )


@router.callback_query(ikb.ShowPaymentOrderCallbackData.filter(F.action == 'ForwardPayment'))
async def forward_payment_orders(
        callback: CallbackQuery,
        callback_data: ikb.ShowPaymentOrderCallbackData
):
    await callback.answer()
    await open_payment_menu(
        event=callback,
        menu_page=callback_data.menu_page + 1,
        date=callback_data.date
    )


@router.callback_query(ikb.ShowPaymentOrderCallbackData.filter(F.action == 'BackPayment'))
async def back_payment_orders(
        callback: CallbackQuery,
        callback_data: ikb.ShowPaymentOrderCallbackData
):
    await callback.answer()
    await open_payment_menu(
        event=callback,
        menu_page=callback_data.menu_page - 1,
        date=callback_data.date
    )


@router.callback_query(ikb.ShowPaymentOrderCallbackData.filter(F.action == 'OpenPayment'))
async def open_payment(
        callback: CallbackQuery,
        callback_data: ikb.ShowPaymentOrderCallbackData
):
    await callback.answer()
    payment_orders = await db.get_payments(
        order_id=callback_data.order_id,
    )

    total_amount = Decimal('0')
    for worker in payment_orders:
        total_amount += Decimal(worker['amount'])

    await callback.message.edit_text(
        text=txt.show_payment(
            workers=payment_orders,
            total_amount=str(total_amount),
        ),
        reply_markup=ikb.confirmation_payment_order(
            order_id=callback_data.order_id,
            total_amount=str(total_amount),
        )
    )

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Открыл заказ №{callback_data.order_id}',
    )


@router.callback_query(F.data.startswith('PaymentChangeAmounts:'))
async def confirmation_change_payment_amounts(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])

    workers = await db.workers_for_change_payment_amounts(
        order_id=order_id,
    )

    await callback.message.edit_text(
        text=txt.change_payment_amount(
            worker=workers[0],
        )
    )

    await state.update_data(
        WorkersForChangeAmounts=[
            worker.model_dump() for worker in workers
        ],
        CurrentWorkerChA=0,
        OrderIDChA=order_id,
    )
    await state.set_state('AccountantChangeAmounts')

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Нажал на кнопку [Изменить суммы]',
    )


async def update_amounts(
        workers: list[WorkerChangeAmountSchema],
        order_id: int,
        msg: Message,
) -> None:
    result = await db.update_payment_amounts(
        workers=workers,
    )
    if result:
        write_accountant_op_log(
            message=f'Кассир {msg.from_user.id} | Заказ №{order_id} | Суммы успешно обновлены',
        )

        payment_orders = await db.get_payments(
            order_id=order_id,
        )

        total_amount = Decimal('0')
        for worker in workers:
            total_amount += Decimal(worker.new_amount)

        await msg.edit_text(
            text=txt.show_payment(
                workers=payment_orders,
                total_amount=str(total_amount),
            ),
            reply_markup=ikb.confirmation_payment_order(
                order_id=order_id,
                total_amount=str(total_amount),
            )
        )
    else:
        info = ''
        for worker in workers:
            info += f'{worker.payment_id} | {worker.full_name} | {worker.old_amount} | {worker.new_amount}\n'
        write_accountant_op_log(
            message=f'Кассир {msg.from_user.id} | Заказ №{order_id} | Не удалось обновить суммы\n{info}',
            level='ERROR',
        )

        await msg.edit_text(
            text=txt.update_payment_amounts_error()
        )


@router.message(F.text, StateFilter('AccountantChangeAmounts'))
async def get_new_amount(
        message: Message,
        state: FSMContext,
):
    if message.text.isdigit():
        new_amount = Decimal(message.text)
        if new_amount < Decimal('0'):
            await message.answer(
                text=txt.new_amount_little_error(),
            )
        elif new_amount <= Decimal('9999'):
            data = await state.get_data()
            workers: list[WorkerChangeAmountSchema] = [
                WorkerChangeAmountSchema(**worker) for worker in data.get('WorkersForChangeAmounts')
            ]

            if workers:
                current_worker = data['CurrentWorkerChA']
                workers[current_worker].new_amount = str(new_amount)

                await state.update_data(
                    WorkersForChangeAmounts=[
                        worker.model_dump() for worker in workers
                    ],
                )

                if current_worker + 2 > len(workers):
                    await state.set_state(None)

                    msg = await message.answer(
                        text=txt.updating_payment_amounts()
                    )
                    asyncio.create_task(
                        update_amounts(
                            workers=workers,
                            order_id=data['OrderIDChA'],
                            msg=msg,
                        )
                    )
                else:
                    new_current_worker = current_worker + 1
                    await state.update_data(
                        CurrentWorkerChA=new_current_worker,
                    )
                    await message.answer(
                        text=txt.change_payment_amount(
                            worker=workers[new_current_worker],
                        )
                    )
            else:
                await message.answer(
                    text=txt.change_amounts_no_workers_error(),
                )
        else:
            await message.answer(
                text=txt.new_amount_big_error()
            )
    else:
        await message.answer(
            text=txt.num_error()
        )


@router.callback_query(F.data.startswith('PaymentNotChangeAmounts:'))
async def def_choose_ip(
        callback: CallbackQuery,
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    total_amount = Decimal(callback.data.split(':')[2])

    checked_orgs = []
    for org_id in orgs_id:
        org_balance = await get_organization_balance(org_id)

        if org_balance and Decimal(org_balance) >= total_amount:
            checked_orgs.append(
                {'id': org_id, 'balance': org_balance}
            )

    if checked_orgs:
        await callback.message.edit_text(
            text=txt.choose_ip_for_payment(),
            reply_markup=ikb.choose_org_for_payment(
                order_id=order_id,
                orgs=checked_orgs,
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_suitable_org()
        )

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Оставил суммы',
    )


@router.callback_query(F.data.startswith('ConfirmationCreatePayment:'))
async def create_payment(
        callback: CallbackQuery,
):
    await callback.answer()
    org_id = int(callback.data.split(':')[2])
    order_id = int(callback.data.split(':')[1])

    payment_orders = await db.get_payments(
        order_id=order_id,
    )

    total_amount = Decimal('0')
    for worker in payment_orders:
        total_amount += Decimal(worker['amount'])

    await callback.message.edit_text(
        text=txt.confirmation_create_payment(
            workers=payment_orders,
            total_amount=total_amount,
            org_name=orgs_dict[org_id],
        ),
        reply_markup=ikb.confirmation_create_payment(
            order_id=order_id,
            org_id=org_id,
        )
    )

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Выбрал {orgs_dict[org_id]}',
    )


@router.callback_query(F.data.startswith('CancelCreatePayment:'))
async def cancel_create_payment(
        callback: CallbackQuery,
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.create_payment_canceled()
    )

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{callback.data.split(":")[1]} | Отменил создание выплаты',
    )


@router.callback_query(F.data.startswith('ConfirmCreatePayment:'))
async def confirm_create_payment(
        callback: CallbackQuery,
):
    await callback.answer()
    order_id = int(callback.data.split(':')[1])
    order = await db.get_archived_order_by_ord_id(
        order_id=order_id,
    )
    check_jobs_fp = await db.has_jobs_for_payment()

    if check_jobs_fp:
        registry_id_in_db = await db.set_registry(
            order_id=order_id,
        )
        if registry_id_in_db:
            organization = await db.get_customer_organization(
                customer_id=order.customer_id,
            )
            name = f'{organization} {order.date.replace(".", "_")}_{"Д" if order.day_shift else "Н"}'
            await db.update_registry_status_by_id(registry_id=registry_id_in_db, status='ACTS')
            await callback.message.edit_text(
                text=txt.payment_created(
                    payment_name=name,
                )
            )
            asyncio.create_task(
                create_registry_fp(
                    registry_id_in_db=registry_id_in_db,
                    callback=callback,
                    order_id=order_id,
                    archived_order=order,
                    org_id=int(callback.data.split(':')[2]),
                    organization=organization,
                    name=name,
                )
            )
        else:
            await callback.message.edit_text(
                text=txt.create_payment_error()
            )
            write_accountant_op_log(
                message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Не удалось создать выплату в бд',
                level='ERROR'
            )
    else:
        await callback.message.edit_text(
            text=txt.no_jobs_fp_error()
        )
        write_accountant_op_log(
            message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | У заказчика отсутствуют услуги для выплат',
            level='ERROR'
        )

    write_accountant_op_log(
        message=f'Кассир {callback.from_user.id} | Заказ №{order_id} | Подтвердил создание заказа',
    )
