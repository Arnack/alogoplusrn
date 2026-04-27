from datetime import datetime, timedelta
from pydantic import SecretStr
from aiogram import Bot
import asyncio
import logging

from utils.loggers import write_accountant_wp_log
from utils.scheduler.scheduler import scheduler
from config_reader import config
import database as db
import texts as txt
from API.fin.registry import get_registry_transactions


async def wallet_payment_check(
        api_registry_id: int,
        wp_id: int,
        accountant_tg_id: int,
        worker_full_name: str,
        date_api: str,
) -> None:
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        wallet_payment = await db.get_wallet_payment(wp_id=wp_id)
        worker_db = await db.get_user_by_id(user_id=wallet_payment.worker.user_id)

        transactions = await get_registry_transactions(registry_id=api_registry_id)
        if not transactions:
            write_accountant_wp_log(
                message=f'Кассир {accountant_tg_id} | Выплата из кошелька №{wp_id} | Нет данных по транзакциям',
                level='ERROR',
            )
            return

        worker_inn = getattr(worker_db, 'inn', None)
        paid = False
        for tr in transactions:
            tr_worker = tr.get('worker') or {}
            tr_inn = tr_worker.get('inn')
            status_code = (tr.get('status') or {}).get('codename')
            if tr_inn and worker_inn and str(tr_inn) == str(worker_inn) and status_code == 'paid':
                paid = True
                break

        if paid:
            asyncio.create_task(
                db.set_wallet_payment_paid_true(wp_id=wp_id)
            )
            try:
                await bot.send_message(
                    chat_id=worker_db.tg_id,
                    text=txt.payment_paid()
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            try:
                await bot.send_message(
                    chat_id=accountant_tg_id,
                    text=txt.wallet_payment_successful_report(
                        worker_full_name=worker_full_name,
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            write_accountant_wp_log(
                message=f'Кассир {accountant_tg_id} | Выплата из кошелька №{wp_id} | Выплата успешно проведена',
            )
        else:
            asyncio.create_task(
                db.update_wallet_payment_status(wp_id=wp_id, status='rr:not_paid')
            )
            try:
                await bot.send_message(
                    chat_id=worker_db.tg_id,
                    text=txt.payment_not_paid_critical_error(
                        payment_id=wp_id,
                        is_wallet_payment=True,
                    )
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            try:
                await bot.send_message(
                    chat_id=accountant_tg_id,
                    text=txt.wallet_payment_error_report(wp_id=wp_id),
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            write_accountant_wp_log(
                message=f'Кассир {accountant_tg_id} | Выплата из кошелька №{wp_id} | Не удалось совершить выплату',
                level='ERROR',
            )


async def schedule_wallet_payment_check(
        api_registry_id: int,
        wp_id: int,
        accountant_tg_id: int,
        worker_full_name: str,
        date_api: str,
) -> None:
    date = datetime.now() + timedelta(minutes=20)
    try:
        scheduler.add_job(
            wallet_payment_check,
            args=[
                api_registry_id,
                wp_id,
                accountant_tg_id,
                worker_full_name,
                date_api,
            ],
            trigger='date',
            run_date=date,
            id=f'check_wallet_payment_{wp_id}',
        )
        write_accountant_wp_log(
            message=f'Кассир {accountant_tg_id} | Выплата из кошелька №{wp_id} | Проверка выплаты запланирована',
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        write_accountant_wp_log(
            message=f'Кассир {accountant_tg_id} | Выплата из кошелька №{wp_id} | Не удалось запланировать проверку выплаты',
            level='ERROR',
        )
