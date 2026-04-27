import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from utils import write_worker_op_log
import texts as txt
import database as db


router = Router()


@router.callback_query(F.data.startswith('WorkCancelPayment:'))
async def worker_canceled_payment(
        callback: CallbackQuery,
):
    order_id = int(callback.data.split(':')[1])
    result = await db.update_worker_balance_by_tg_id_op(
        tg_id=callback.from_user.id,
        order_id=order_id,
    )
    if result['success']:
        if result['payment_error']:
            await callback.message.edit_text(
                text=result['reason']
            )
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {callback.from_user.id} | Заказ №{order_id} | При получении выплату на кошелек произошла ошибка: {result["reason"]}',
                level='ERROR'
            )
        else:
            await callback.message.edit_text(
                text=txt.payment_sent_to_balance()
            )
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {callback.from_user.id} | Заказ №{order_id} | Выплата отправлена в кошелек',
            )
    else:
        await callback.message.edit_text(
            text=txt.update_worker_balance_error()
        )
        write_worker_op_log(
            message=f'Исполнитель (tg_id) {callback.from_user.id} | Заказ №{order_id} | При получении выплату на кошелек произошла неизвестная ошибка',
            level='ERROR'
        )


@router.callback_query(F.data.startswith('WorkConfirmPayment:'))
async def worker_confirmed_payment(
        callback: CallbackQuery,
        state: FSMContext,
):
    order_id = int(callback.data.split(':')[1])
    await callback.message.edit_text(
        text=txt.request_worker_pin_code()
    )
    await state.set_state('PaymentGetINNPin')
    await state.update_data(
        OrderIDForPayment=order_id,
    )
    write_worker_op_log(
        message=f'Исполнитель (tg_id) {callback.from_user.id} | Заказ №{order_id} | Подтверждает получение выплаты',
    )


@router.message(F.text, StateFilter('PaymentGetINNPin'))
async def payment_get_pin(
        message: Message,
        state: FSMContext,
):
    worker = await db.get_user(
        tg_id=message.from_user.id,
    )
    data = await state.get_data()
    if worker.inn[-4:] == message.text:
        await state.set_state(None)
        try:
            await db.payment_set_notification_confirmed(
                tg_id=message.from_user.id,
                order_id=data['OrderIDForPayment'],
            )
            await message.answer(
                text=txt.wait_payment()
            )
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {message.from_user.id} | Заказ №{data["OrderIDForPayment"]} | Введен верный пин-код',
            )
        except Exception as e:
            logging.exception(f'\n\n{e}')
            await message.answer(
                text=txt.update_worker_balance_error()
            )
            write_worker_op_log(
                message=f'Исполнитель (tg_id) {message.from_user.id} | Заказ №{data["OrderIDForPayment"]} | Произошла неизвестная ошибка при подтверждении выплаты',
                level='ERROR'
            )
    else:
        await message.answer(
            text=txt.contract_inn_error()
        )
        write_worker_op_log(
            message=f'Исполнитель (tg_id) {message.from_user.id} | Заказ №{data["OrderIDForPayment"]} | Введен неправильный пин-код',
        )
