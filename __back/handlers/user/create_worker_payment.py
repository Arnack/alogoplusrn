from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal
from datetime import datetime
import logging

from utils.loggers import write_worker_wp_log
from utils import is_number, truncate_decimal
from utils.payout_flow import create_contract_documents
import database as db
from filters import Worker
import texts as txt


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())


@router.callback_query(F.data == 'CreateWorkerPayment')
async def create_payment(
        callback: CallbackQuery,
        state: FSMContext,
):
    balance = await db.get_worker_balance_by_tg_id(
        tg_id=callback.from_user.id,
    )
    if balance >= Decimal('2600'):
        await callback.answer()
        await callback.message.edit_text(
            text=txt.request_amount_for_payment(),
        )
        await state.update_data(
            WorkerBalance=str(balance),
        )
        await state.set_state('RequestWorkerAmountFP')
    else:
        await callback.answer(
            text=txt.low_balance_error(),
            show_alert=True,
        )


@router.message(F.text, StateFilter('RequestWorkerAmountFP'))
async def get_amount_fp(
        message: Message,
        state: FSMContext,
):
    amount = truncate_decimal(
        number=message.text.replace(',', '.')
    )
    if is_number(amount):
        if Decimal(amount) < Decimal('2600'):
            await message.answer(
                text='❗Минимальная сумма 2600₽. Введите ее еще раз:'
            )
        else:
            data = await state.get_data()
            if Decimal(amount) > Decimal(data['WorkerBalance']):
                await message.answer(
                    text='❗Сумма не может быть больше вашего баланса. Введите ее еще раз:'
                )
            else:
                await state.set_state(None)
                wp_id = await db.set_wallet_payment(
                    tg_id=message.from_user.id,
                    amount=amount,
                )

                if wp_id:
                    is_updated = await db.update_worker_balance(
                        tg_id=message.from_user.id,
                        new_balance=str(
                            Decimal(data['WorkerBalance']) - Decimal(amount)
                        ),
                    )
                    if is_updated:
                        await message.answer(
                            text=f'Выплата №{wp_id} создана. Вам будут приходить уведомления'
                        )
                        write_worker_wp_log(
                            message=f'Исполнитель {message.from_user.id} | Создал выплату из кошелька №{wp_id} на сумму {amount} рублей',
                        )

                        # Формируем 3 договора и отправляем запрос кассиру
                        worker = await db.get_user(tg_id=message.from_user.id)
                        act_date = datetime.strftime(datetime.now(), "%d.%m.%Y")
                        contracts = await create_contract_documents(
                            user_id=worker.id,
                            wallet_payment_id=wp_id,
                            act_date=act_date,
                        )

                        accountants = await db.get_accountants_tg_id()
                        for tg_id in accountants:
                            try:
                                await message.bot.send_message(
                                    chat_id=tg_id,
                                    text=txt.new_wallet_payment_notification(
                                        date=datetime.strftime(datetime.now(), "%d.%m.%Y"),
                                    ),
                                )
                            except Exception as e:
                                logging.exception(e)

                        await message.answer(
                            text=f'Договоры сформированы: {len(contracts)}. После выбора ИП кассиром вам придёт акт на подпись.'
                        )
                        return
                    else:
                        await db.update_wallet_payment_status(
                            wp_id=wp_id,
                            status='ERROR',
                        )

                await message.answer(
                    text=txt.create_payment_error()
                )
    else:
        await message.answer(
            text='❗Введите сумму еще раз:'
        )
