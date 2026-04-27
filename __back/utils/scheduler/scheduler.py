import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import asyncio

from API import (
    change_current_organization,
    create_payment,
    get_registry_updated_date,
    send_registry_for_payment,
    get_registry_transactions,
    get_registry_status,
    get_unsigned_document,
    sign_worker_document,
)
from utils.checking import check_run_date
from utils.max_delivery import send_max_message
from utils.time_converter import extract_and_subtract_hour
from utils.loggers.payments import  write_accountant_op_log, write_worker_op_log
from config_reader import config
import database as db
import texts as txt


scheduler = AsyncIOScheduler(
    jobstores={
        'default': SQLAlchemyJobStore(
            url='sqlite:///scheduler_db/jobs.sqlite3'
        )
    },
    job_defaults={
        'misfire_grace_time': 3600  # не пропускать задания опоздавшие до 1 часа
    }
)


async def send_reminder(tg_id, order_id):
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        await bot.send_message(
            chat_id=tg_id,
            text=await txt.reminder(
                order_id=order_id
            ),
            parse_mode='HTML',
        )


async def set_reminder(tg_id, order_id, date, order_time):
    order_time = datetime.strptime(await extract_and_subtract_hour(order_time), "%H:%M").time()
    date = datetime.strptime(date.strip(), "%d.%m.%Y").date()
    full_event_dt = datetime.combine(date, order_time)

    try:
        scheduler.add_job(send_reminder,
                          args=[tg_id, order_id],
                          trigger='date',
                          run_date=full_event_dt,
                          id=f'{tg_id}_{order_id}')
    except:
        pass


async def delete_reminder(tg_id, order_id):
    try:
        scheduler.remove_job(f'{tg_id}_{order_id}')
    except:
        pass


async def schedule_delete_verification_code(
        code_id: int
) -> None:
    date = datetime.now() + timedelta(minutes=5)
    try:
        scheduler.add_job(
            db.delete_verification_code,
            args=[code_id],
            trigger='date',
            run_date=date,
            id=f'delete_code_{code_id}'
        )
    except:
        pass


async def schedule_delete_registration_code(
        code_id: int
) -> None:
    date = datetime.now() + timedelta(minutes=10)
    try:
        scheduler.add_job(
            db.delete_registration_code,
            args=[code_id],
            trigger='date',
            run_date=date,
            id=f'delete_code_{code_id}')
    except:
        pass


async def schedule_delete_code_for_order(
        code_id: int
) -> None:
    date = datetime.now() + timedelta(minutes=30)
    try:
        scheduler.add_job(
            db.delete_code_for_order,
            args=[code_id],
            trigger='date',
            run_date=date,
            id=f'delete_code_for_order_{code_id}')
    except:
        pass


async def delete_shout_message(chat_id, message_id):
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )


async def schedule_delete_shout_message(chat_id, message_id):
    date = datetime.now() + timedelta(minutes=5)
    try:
        scheduler.add_job(
            delete_shout_message,
            args=[chat_id, message_id],
            trigger='date',
            run_date=date,
            id=f'delete_message_{message_id}')
    except:
        pass


async def _check_streak_skips_yesterday():
    """Ежедневная проверка пропусков по streak-акциям за вчерашний день."""
    from datetime import timedelta
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        try:
            await db.check_streak_skips_for_date(order_date=yesterday, bot=bot)
        except Exception as e:
            logging.exception(f'[promo] Ошибка проверки пропусков акций: {e}')


async def schedule_streak_skip_check():
    """Запланировать ежедневную проверку пропусков в 03:00."""
    try:
        existing = scheduler.get_job(job_id='daily_streak_skip_check')
        if not existing:
            scheduler.add_job(
                _check_streak_skips_yesterday,
                trigger='cron',
                hour=3,
                minute=0,
                id='daily_streak_skip_check',
            )
    except Exception as e:
        logging.exception(f'[promo] Ошибка планирования проверки пропусков: {e}')


async def schedule_delete_inactive_users():
    try:
        in_progress = scheduler.get_job(
            job_id='delete_inactive_users'
        )
        if not in_progress:
            scheduler.add_job(
                db.delete_inactive_users,
                trigger='cron',
                day_of_week='sun',
                hour=23,
                minute=0,
                id='delete_inactive_users'
            )
    except Exception as e:
        logging.exception(f'\n\n{e}')


async def schedule_auto_order_build(
        customer_id: int
) -> None:
    job = scheduler.get_job(
        job_id=f'auto_build_{customer_id}'
    )
    if not job:
        scheduler.add_job(
            db.create_schedule_order,
            args=[customer_id],
            trigger='cron',
            hour=20,
            id=f'auto_build_{customer_id}'
        )


async def delete_auto_order_build(
        customer_id: int
) -> None:
    job = scheduler.get_job(
        job_id=f'auto_build_{customer_id}'
    )
    if job:
        scheduler.remove_job(
            job_id=f'auto_build_{customer_id}'
        )


async def check_auto_order_builder(
        customer_id: int
) -> bool:
    return bool(
        scheduler.get_job(
            job_id=f'auto_build_{customer_id}'
        )
    )


""" Payments """
async def send_payment_report(
        order_id: int,
        accountant_tg_id: int,
        registry_id_in_db: int,
        name: str,
        accountants: list[int],
) -> None:
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        successful_payments_count, total_payments_count = await db.get_payment_counts(
            order_id=order_id,
        )
        for tg_id in accountants:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text=txt.registry_report(
                        payment_name=name,
                        successful_payments_count=successful_payments_count,
                        total_payments_count=total_payments_count,
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')
                write_accountant_op_log(
                    message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Не удалось отправить отчет кассиру {tg_id} по выплате: Всего - {total_payments_count}, Успешно - {successful_payments_count}',
                    level='ERROR'
                )


async def payment_check(
        api_registry_id: int,
        registry_id_in_db: int,
        order_id: int,
        accountant_tg_id: int,
        name: str,
        accountants: list[int],
) -> None:
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        transactions = await get_registry_transactions(registry_id=api_registry_id)

        if transactions is None:
            return

        for tr in transactions:
            api_worker_id = tr['worker']['id']
            transaction_status = tr['status']['codename']
            worker = await db.get_user_by_api_id(api_id=api_worker_id)

            if worker is None:
                write_worker_op_log(
                    message=f'Заказ №{order_id} | Выплата №{registry_id_in_db} | Исполнитель (api_id) {api_worker_id} | Не найден в БД, статус транзакции: {transaction_status}',
                    level='ERROR'
                )
                continue

            if transaction_status == 'paid':
                write_worker_op_log(
                    message=f'Заказ №{order_id} | Выплата №{registry_id_in_db} | Исполнитель (api_id) {api_worker_id} | Успешная выплата. Статус: {transaction_status}',
                )
                asyncio.create_task(
                    db.set_payment_paid_true(worker_id=worker.id, order_id=order_id)
                )
                notified = False
                try:
                    await bot.send_message(chat_id=worker.tg_id, text=txt.payment_paid())
                    notified = True
                except Exception as e:
                    logging.exception(f'\n\n{e}')
                if worker.max_id:
                    try:
                        from maxapi import Bot as MaxBot
                        from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                        if config.max_bot_token:
                            max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
                            await send_max_message(
                                max_bot,
                                user_id=worker.max_id,
                                chat_id=getattr(worker, 'max_chat_id', 0) or None,
                                text=txt.payment_paid(),
                                parse_mode=MaxParseMode.HTML,
                            )
                            await max_bot.close_session()
                            notified = True
                    except Exception as e:
                        logging.exception(f'[max] payment_check paid: {e}')
                if not notified:
                    full_name = f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip()
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.worker_chat_not_found(full_name=full_name, inn=worker.inn),
                                parse_mode='HTML',
                            )
                        except Exception:
                            pass
            else:
                write_worker_op_log(
                    message=f'Заказ №{order_id} | Выплата №{registry_id_in_db} | Исполнитель (api_id) {api_worker_id} | Ошибка выплаты. Статус: {transaction_status}',
                    level='ERROR'
                )
                asyncio.create_task(
                    db.move_payment_to_wallet(worker_id=worker.id, order_id=order_id)
                )
                notified = False
                try:
                    await bot.send_message(
                        chat_id=worker.tg_id,
                        text=txt.payment_stopped_no_card(),
                    )
                    notified = True
                except Exception as e:
                    logging.exception(f'\n\n{e}')
                if worker.max_id:
                    try:
                        from maxapi import Bot as MaxBot
                        from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                        if config.max_bot_token:
                            max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
                            await send_max_message(
                                max_bot,
                                user_id=worker.max_id,
                                chat_id=getattr(worker, 'max_chat_id', 0) or None,
                                text=txt.payment_stopped_no_card(),
                                parse_mode=MaxParseMode.HTML,
                            )
                            await max_bot.close_session()
                            notified = True
                    except Exception as e:
                        logging.exception(f'[max] payment_check error: {e}')
                if not notified:
                    full_name = f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip()
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.worker_chat_not_found(full_name=full_name, inn=worker.inn),
                                parse_mode='HTML',
                            )
                        except Exception:
                            pass

        api_registry_status = await get_registry_status(registry_id=api_registry_id)
        status = api_registry_status if api_registry_status else 'ERROR'

        asyncio.create_task(
            db.update_registry_status_by_id(registry_id=registry_id_in_db, status=status)
        )
        asyncio.create_task(
            send_payment_report(
                order_id=order_id,
                accountant_tg_id=accountant_tg_id,
                registry_id_in_db=registry_id_in_db,
                name=name,
                accountants=accountants,
            )
        )



async def schedule_payment_check(
        api_registry_id: int,
        registry_id_in_db: int,
        order_id: int,
        accountant_tg_id: int,
        name: str,
        accountants: list[int],
) -> None:
    date = datetime.now() + timedelta(minutes=20)
    try:
        scheduler.add_job(
            payment_check,
            args=[
                api_registry_id,
                registry_id_in_db,
                order_id,
                accountant_tg_id,
                name,
                accountants,
            ],
            trigger='date',
            run_date=date,
            id=f'check_payment_order_{order_id}',
        )
        write_accountant_op_log(
            message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Проверка выплаты запланирована',
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        write_accountant_op_log(
            message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Не удалось запланировать проверку выплаты',
            level='ERROR'
        )


async def sign_workers_acts(
        api_registry_id: int,
        order_id: int,
) -> None:
    transactions = await get_registry_transactions(registry_id=api_registry_id)
    if transactions:
        for transaction in transactions:
            document_id, document_type, is_contract = await get_unsigned_document(
                transaction_id=transaction['id'],
            )
            if document_id:
                signed = await sign_worker_document(
                    document_id=document_id,
                    document_type=document_type,
                )
                if signed:
                    write_accountant_op_log(
                        message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Транзакция №{transaction["id"]} | Документ (ID: {document_id}. Type: {document_type}) успешно подписан',
                    )
                    if is_contract:
                        await schedule_sign_workers_acts(
                            api_registry_id=api_registry_id,
                            order_id=order_id,
                        )
                else:
                    write_accountant_op_log(
                        message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Транзакция №{transaction["id"]} | Не удалось подписать документ (ID: {document_id}. Type: {document_type})',
                        level='ERROR',
                    )
            else:
                write_accountant_op_log(
                    message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Транзакция №{transaction["id"]} | Документ не найден',
                    level='ERROR',
                )
    else:
        write_accountant_op_log(
            message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Транзакции отсутствуют',
            level='ERROR',
        )


async def schedule_sign_workers_acts(
        api_registry_id: int,
        order_id: int,
) -> None:
    date = datetime.now() + timedelta(minutes=10)
    try:
        scheduler.add_job(
            sign_workers_acts,
            args=[
                api_registry_id,
                order_id,
            ],
            trigger='date',
            run_date=date,
            id=f'sign_acts_for_order_{order_id}',
        )
        write_accountant_op_log(
            message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Подписание актов запланировано',
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        write_accountant_op_log(
            message=f'Заказ №{order_id} | Реестр №{api_registry_id} | Не удалось запланировать подписание актов',
            level='ERROR'
        )


async def create_new_registry(
        registry_id_in_db: int,
        order_id: int,
        accountant_tg_id: int,
        org_id: int,
        name: str,
) -> None:
    try:
        result = await db.get_workers_for_payment(order_id=order_id)

        async with Bot(token=config.bot_token.get_secret_value()) as bot:
            accountants = await db.get_accountants_tg_id()
            archived_order = await db.get_archived_order_by_ord_id(order_id=order_id)
            organization = await db.get_customer_organization(
                customer_id=archived_order.customer_id,
            ) if archived_order else name

            if result is None:
                workers, skipped = [], []
            else:
                workers, skipped = result

            # Переводим в начисления и уведомляем исполнителей с конфликтом/отсутствием способа выплаты
            if skipped:
                conflict_skipped = [w for w in skipped if w.get('reason') == 'conflict']
                rr_unavailable_skipped = [w for w in skipped if w.get('reason') == 'rr_unavailable']
                no_card_skipped = [w for w in skipped if w.get('reason') in ('missing_rr', 'missing_platform')]
                for w in skipped:
                    await db.move_payment_to_wallet(
                        worker_id=w['user_id'],
                        order_id=order_id,
                    )
                    try:
                        await bot.send_message(
                            chat_id=w['tg_id'],
                            text=(
                                txt.payment_stopped_conflict()
                                if w.get('reason') == 'conflict'
                                else txt.payment_stopped_rr_unavailable()
                                if w.get('reason') == 'rr_unavailable'
                                else txt.payment_stopped_no_card()
                            ),
                        )
                    except Exception as e:
                        logging.exception(f'\n\n{e}')
                    if w.get('max_id'):
                        try:
                            from maxapi import Bot as MaxBot
                            from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                            if config.max_bot_token:
                                max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
                                await max_bot.send_message(
                                    user_id=w['max_id'],
                                    text=(
                                        txt.payment_stopped_conflict()
                                        if w.get('reason') == 'conflict'
                                        else txt.payment_stopped_rr_unavailable()
                                        if w.get('reason') == 'rr_unavailable'
                                        else txt.payment_stopped_no_card()
                                    ),
                                    parse_mode=MaxParseMode.HTML,
                                )
                                await max_bot.close_session()
                        except Exception as e:
                            logging.exception(f'[max] skipped worker notification: {e}')

                if archived_order:
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.payment_order_card(
                                    city=archived_order.city,
                                    customer=organization,
                                    job_name=archived_order.job_name,
                                    date=archived_order.date,
                                    day_shift=archived_order.day_shift,
                                    night_shift=archived_order.night_shift,
                                ),
                                parse_mode='HTML',
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')

                if no_card_skipped:
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.workers_skipped_no_card(
                                    payment_name=name,
                                    skipped=no_card_skipped,
                                ),
                                parse_mode='HTML',
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')
                if rr_unavailable_skipped:
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.workers_skipped_rr_unavailable(
                                    payment_name=name,
                                    skipped=rr_unavailable_skipped,
                                ),
                                parse_mode='HTML',
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')
                if conflict_skipped:
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.workers_skipped_conflict(
                                    payment_name=name,
                                    skipped=conflict_skipped,
                                ),
                                parse_mode='HTML',
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')
                write_accountant_op_log(
                    message=(
                        f'Кассир {accountant_tg_id} | Заказ №{order_id} | '
                        f'Пропущены {len(skipped)} исполнителей: '
                        + ', '.join(w["inn"] for w in skipped)
                    ),
                    level='ERROR',
                )

            if not workers:
                # Нет работников для отправки: либо пустой заказ, либо все ушли в начисления
                for tg_id in accountants:
                    try:
                        await bot.send_message(
                            chat_id=tg_id,
                            text=txt.create_registry_no_workers_error(payment_name=name),
                        )
                    except Exception as e:
                        logging.exception(f'\n\n{e}')
                asyncio.create_task(
                    db.update_registry_status_by_id(
                        registry_id=registry_id_in_db,
                        status='ERROR',
                    )
                )
                return

            if workers:
                await change_current_organization(org_id=org_id)
                api_registry_id, registry_status = await create_payment(
                    workers=workers,
                    payment_id=registry_id_in_db,
                    org_id=org_id,
                    name=name,
                )
                if api_registry_id:
                    await db.update_registry(
                        registry_id=registry_id_in_db,
                        api_registry_id=api_registry_id,
                        status=f'rr:{registry_status}',
                    )
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.api_registry_created(payment_name=name),
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')

                    write_accountant_op_log(
                        message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Платежный реестр создан',
                    )

                    updated_date = await get_registry_updated_date(registry_id=api_registry_id)
                    if updated_date:
                        result = await send_registry_for_payment(
                            registry_id=api_registry_id,
                            updated_date=updated_date,
                        )
                        if result:
                            for tg_id in accountants:
                                try:
                                    await bot.send_message(
                                        chat_id=tg_id,
                                        text=txt.registry_sent_for_payment(payment_name=name),
                                    )
                                except Exception as e:
                                    logging.exception(f'\n\n{e}')

                            await schedule_sign_workers_acts(
                                api_registry_id=api_registry_id,
                                order_id=order_id,
                            )
                            await schedule_payment_check(
                                api_registry_id=api_registry_id,
                                registry_id_in_db=registry_id_in_db,
                                order_id=order_id,
                                accountant_tg_id=accountant_tg_id,
                                name=name,
                                accountants=accountants,
                            )
                            asyncio.create_task(
                                db.update_registry_status_by_id(
                                    registry_id=registry_id_in_db,
                                    status='inPayment',
                                )
                            )
                            write_accountant_op_log(
                                message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Реестр №{api_registry_id} отправлен в оплату',
                            )
                        else:
                            for tg_id in accountants:
                                try:
                                    await bot.send_message(
                                        chat_id=tg_id,
                                        text=txt.create_registry_send_for_payment_error(payment_name=name),
                                    )
                                except Exception as e:
                                    logging.exception(f'\n\n{e}')
                            asyncio.create_task(
                                db.update_registry_status_by_id(
                                    registry_id=registry_id_in_db,
                                    status='ERROR',
                                )
                            )
                            write_accountant_op_log(
                                message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Не удалось отправить реестр №{api_registry_id} в оплату',
                                level='ERROR'
                            )
                    else:
                        for tg_id in accountants:
                            try:
                                await bot.send_message(
                                    chat_id=tg_id,
                                    text=txt.create_registry_no_date_error(payment_name=name),
                                )
                            except Exception as e:
                                logging.exception(f'\n\n{e}')
                        asyncio.create_task(
                            db.update_registry_status_by_id(
                                registry_id=registry_id_in_db,
                                status='ERROR',
                            )
                        )
                        write_accountant_op_log(
                            message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Не удалось получить дату реестра',
                            level='ERROR'
                        )
                else:
                    for tg_id in accountants:
                        try:
                            await bot.send_message(
                                chat_id=tg_id,
                                text=txt.create_registry_api_error(payment_name=name),
                            )
                        except Exception as e:
                            logging.exception(f'\n\n{e}')

                    asyncio.create_task(
                        db.update_registry_status_by_id(
                            registry_id=registry_id_in_db,
                            status='ERROR',
                        )
                    )
                    write_accountant_op_log(
                        message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Выплата №{registry_id_in_db} | Не удалось создать платежный реестр',
                        level='ERROR'
                    )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        asyncio.create_task(
            db.update_registry_status_by_id(
                registry_id=registry_id_in_db,
                status='ERROR',
            )
        )


async def schedule_payment(
        registry_id_in_db: int,
        order_id: int,
        accountant_tg_id: int,
        org_id: int,
        name: str,
) -> None:
    date = datetime.now() + timedelta(minutes=10)
    try:
        scheduler.add_job(
            create_new_registry,
            args=[
                registry_id_in_db,
                order_id,
                accountant_tg_id,
                org_id,
                name,
            ],
            trigger='date',
            run_date=date,
            id=f'payment_order_{order_id}',
        )
        write_accountant_op_log(
            message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Создание платежного реестра на стороне РР запланировано'
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        write_accountant_op_log(
            message=f'Кассир {accountant_tg_id} | Заказ №{order_id} | Не удалось запланировать создание платежного реестра',
            level='ERROR'
        )


async def order_notification_before_the_end(
        chat_id: str,
        order_id: int,
        order_status: str,
        order_job: str,
        order_city: str,
        order_date: str,
        order_time: str
) -> None:
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        await bot.send_message(
            chat_id=chat_id,
            text=txt.order_notification_before_the_end(
                order_id=order_id,
                order_status=order_status,
                order_job=order_job,
                order_city=order_city,
                order_date=order_date,
                order_time=order_time
            ),
            parse_mode='HTML'
        )


async def order_notification_after_the_end(
        chat_id: str,
        order_id: int,
        order_status: str,
        order_job: str,
        order_city: str,
        order_date: str,
        order_time: str
) -> None:
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        await bot.send_message(
            chat_id=chat_id,
            text=txt.order_notification_after_the_end(
                order_id=order_id,
                order_status=order_status,
                order_job=order_job,
                order_city=order_city,
                order_date=order_date,
                order_time=order_time
            ),
            parse_mode='HTML'
        )


async def schedule_customer_order_notifications(
        customer_id: int,
        order_id: int
) -> None:
    groups = await db.get_customer_groups(
        customer_id=customer_id
    )
    order = await db.get_order(
        order_id=order_id
    )

    status = 'В работе' if order.in_progress else 'Поиск исполнителей'
    order_time = order.day_shift if order.day_shift else order.night_shift
    order_date = check_run_date(
        date=order.date,
        start_time=order_time.split("-")[0].strip(),
        end_time=order_time.split("-")[1].strip(),
    )
    # Если check_run_date вернула None (дневная смена), используем оригинальную дату
    if order_date is None:
        order_date = order.date
    run_date = datetime.strptime(f'{order_date} {order_time.split("-")[1].strip()}', '%d.%m.%Y %H:%M')

    for group in groups:
        before_1 = scheduler.get_job(
            job_id=f'group_{group.id}_order_{order_id}_before_1'
        )
        if not before_1:
            scheduler.add_job(
                order_notification_before_the_end,
                args=[
                    group.chat_id,
                    order.id,
                    status,
                    order.job_name,
                    order.city,
                    order.date,
                    order_time
                ],
                trigger='date',
                run_date=run_date - timedelta(minutes=1),
                id=f'group_{group.id}_order_{order_id}_before_1'
            )

        after_10 = scheduler.get_job(
            job_id=f'group_{group.id}_order_{order_id}_after_10'
        )
        if not after_10:
            scheduler.add_job(
                order_notification_after_the_end,
                args=[
                    group.chat_id,
                    order.id,
                    status,
                    order.job_name,
                    order.city,
                    order.date,
                    order_time
                ],
                trigger='date',
                run_date=run_date + timedelta(minutes=10),
                id=f'group_{group.id}_order_{order_id}_after_10'
            )


async def delete_customer_order_notifications(
        customer_id: int,
        order_id: int
) -> None:
    groups = await db.get_customer_groups(
        customer_id=customer_id
    )

    for group in groups:
        before_1 = scheduler.get_job(
            job_id=f'group_{group.id}_order_{order_id}_before_1'
        )
        if before_1:
            scheduler.remove_job(
                job_id=f'group_{group.id}_order_{order_id}_before_1'
            )

        after_10 = scheduler.get_job(
            job_id=f'group_{group.id}_order_{order_id}_after_10'
        )
        if after_10:
            scheduler.remove_job(
                job_id=f'group_{group.id}_order_{order_id}_after_10'
            )


async def _expire_no_show_buttons(event_id: int):
    """Убирает кнопки с карточек кассиров через 24 часа."""
    messages = await db.get_cashier_messages_for_event(event_id=event_id)
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for msg in messages:
            try:
                await bot.edit_message_reply_markup(
                    chat_id=msg.cashier_tg_id,
                    message_id=msg.message_id,
                    reply_markup=None
                )
            except TelegramBadRequest as e:
                error_text = str(e).lower()
                if 'message is not modified' in error_text:
                    logging.info(f'Кнопки у кассира {msg.cashier_tg_id} уже сняты')
                    continue
                logging.error(f'Ошибка снятия кнопок у кассира {msg.cashier_tg_id}: {e}')
            except Exception as e:
                logging.error(f'Ошибка снятия кнопок у кассира {msg.cashier_tg_id}: {e}')


async def schedule_expire_no_show_buttons(event_id: int) -> None:
    """Запланировать истечение кнопок для события невыхода через 24 часа."""
    run_date = datetime.now() + timedelta(hours=24)
    try:
        scheduler.add_job(
            _expire_no_show_buttons,
            args=[event_id],
            trigger='date',
            run_date=run_date,
            id=f'expire_no_show_{event_id}'
        )
    except Exception as e:
        logging.error(f'Ошибка планирования истечения кнопок для события {event_id}: {e}')


# ── Акты: авто-подписание через 10 минут ──────────────────────────────────────

async def auto_sign_worker_act(
        act_id: int,
        worker_tg_id: int | None = None,
        worker_max_id: int | None = None,
) -> None:
    """Авто-подписывает акт если работник не ответил в течение 10 минут."""
    act = await db.get_worker_act(act_id=act_id)
    if not act or act.status not in ('pending', 'sent'):
        return  # уже подписан или отклонён

    await db.update_worker_act_status(act_id=act_id, status='auto_signed')
    from utils.payout_flow import ensure_act_pdf, send_receipt_instruction_max, send_receipt_instruction_tg
    await ensure_act_pdf(act_id=act_id)

    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        if worker_tg_id:
            try:
                await bot.send_message(
                    chat_id=worker_tg_id,
                    text=txt.act_auto_signed(),
                )
                await send_receipt_instruction_tg(bot=bot, worker_tg_id=worker_tg_id, act_id=act_id)
            except Exception as e:
                logging.exception(f'\n\n{e}')
    if worker_max_id and config.max_bot_token:
        try:
            from maxapi import Bot as MaxBot
            from maxapi.enums.parse_mode import ParseMode as MaxParseMode
            max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
            await max_bot.send_message(
                user_id=worker_max_id,
                text=txt.act_auto_signed(),
                parse_mode=MaxParseMode.HTML,
            )
            await max_bot.close_session()
            await send_receipt_instruction_max(worker_max_id=worker_max_id, act_id=act_id)
        except Exception as e:
            logging.exception(f'[max] auto_sign_worker_act: {e}')


async def schedule_act_auto_sign(
        act_id: int,
        worker_tg_id: int | None = None,
        worker_max_id: int | None = None,
) -> None:
    """Планирует авто-подписание акта через 10 минут."""
    run_date = datetime.now() + timedelta(minutes=10)
    try:
        scheduler.add_job(
            auto_sign_worker_act,
            args=[act_id, worker_tg_id, worker_max_id],
            trigger='date',
            run_date=run_date,
            id=f'auto_sign_act_{act_id}',
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')


def cancel_act_auto_sign(act_id: int) -> None:
    """Отменяет запланированное авто-подписание акта."""
    job_id = f'auto_sign_act_{act_id}'
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
