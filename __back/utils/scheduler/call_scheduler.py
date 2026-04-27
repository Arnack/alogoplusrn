import json
import logging
from datetime import datetime, timedelta
import pytz

from aiogram import Bot

from config_reader import config
import database as db
from utils.zvonok_client import make_call, get_call_status, get_call_status_by_phone, map_zvonok_status
from utils.scheduler.scheduler import scheduler

# Московский часовой пояс
MOSCOW_TZ = pytz.timezone('Europe/Moscow')


# Смещения в минутах от начала смены (отрицательные = до начала)
CALL_OFFSETS = {
    'day': [-75, -67],    # -1:15, затем -1:07 (через 8 минут)
    'night': [-100, -112]  # -2:00, затем -1:52 (через 8 минут)
}
# Через сколько минут после звонка опрашиваем статус
POLL_DELAY_MINUTES = 3


async def schedule_call_campaign(order_id: int) -> None:
    """
    Планирует кампанию прозвона для заявки.
    Вызывается при переводе заявки в статус in_progress.

    Новая логика: планируются ВРЕМЕНА прозвона (не конкретные работники).
    При наступлении времени звонка проверяется актуальный список работников из OrderWorker.
    """
    try:
        order = await db.get_order(order_id=order_id)
        shift_str = order.day_shift or order.night_shift
        shift_type = 'day' if order.day_shift else 'night'

        # Парсим время начала смены с московским часовым поясом
        start_time = MOSCOW_TZ.localize(
            datetime.strptime(
                f'{order.date} {shift_str.split("-")[0].strip()}',
                '%d.%m.%Y %H:%M'
            )
        )

        # Проверяем, не началась ли уже смена
        now = datetime.now(MOSCOW_TZ)
        if now >= start_time:
            logging.info(
                f'[call_scheduler] Прозвон для заявки {order_id} не планируется: '
                f'смена уже началась (начало: {start_time.strftime("%H:%M")}, сейчас: {now.strftime("%H:%M")})'
            )
            return

        # Проверяем, существует ли уже кампания для этой заявки и смены
        existing_campaign = await db.get_campaign_by_order_id(order_id=order_id, shift=shift_type)
        if existing_campaign:
            logging.info(
                f'[call_scheduler] Кампания для заявки {order_id} (смена={shift_type}) '
                f'уже существует (campaign_id={existing_campaign.id}), пропускаем создание'
            )
            return

        # Создаём запись кампании в БД
        campaign = await db.create_call_campaign(
            order_id=order_id,
            shift=shift_type,
            order_date=order.date
        )

        offsets = CALL_OFFSETS[shift_type]

        # Планируем обе попытки кампании (не привязываясь к конкретным работникам)
        for attempt_no, offset in enumerate(offsets, start=1):
            call_time = start_time + timedelta(minutes=offset)

            # Если время уже прошло — смещаем на ближайшее будущее
            if call_time <= now:
                call_time = now + timedelta(seconds=5)
                logging.warning(
                    f'[call_scheduler] Попытка {attempt_no} для кампании {campaign.id} '
                    f'в прошлом, переносим на {call_time}'
                )

            job_id = f'campaign_{campaign.id}_attempt_{attempt_no}'
            if not scheduler.get_job(job_id):
                scheduler.add_job(
                    execute_campaign_attempt,
                    args=[campaign.id, attempt_no],
                    trigger='date',
                    run_date=call_time,
                    id=job_id,
                    replace_existing=True
                )

        logging.info(
            f'[call_scheduler] Запланирован прозвон для заявки {order_id}, '
            f'campaign_id={campaign.id}, смена={shift_type} | '
            f'Начало смены: {start_time.strftime("%d.%m.%Y %H:%M:%S %Z")} | '
            f'Текущее время: {now.strftime("%d.%m.%Y %H:%M:%S %Z")} | '
            f'Попытки: {len(offsets)} (в {offsets[0]} и {offsets[1]} мин от начала смены)'
        )
    except Exception as e:
        logging.exception(f'[call_scheduler] Ошибка при планировании прозвона для заявки {order_id}: {e}')


async def execute_campaign_attempt(campaign_id: int, attempt_no: int) -> None:
    """
    Выполняет попытку прозвона для кампании.
    Получает актуальный список работников на момент звонка и звонит только тем, кто:
    1. В данный момент в списке OrderWorker
    2. Ещё не получил финальный статус
    3. Не был обзвонен в рамках этой попытки
    """
    logging.info(
        f'[call_scheduler] ▶️  НАЧАЛО execute_campaign_attempt: '
        f'campaign_id={campaign_id}, attempt={attempt_no}'
    )
    try:
        # Получаем кампанию и заказ
        campaign = await db.get_campaign(campaign_id=campaign_id)
        if not campaign:
            logging.error(f'[call_scheduler] Кампания {campaign_id} не найдена')
            return

        order = await db.get_order(order_id=campaign.order_id)
        if not order:
            logging.error(f'[call_scheduler] Заявка {campaign.order_id} не найден')
            return

        shift_type = 'day' if order.day_shift else 'night'

        # Получаем АКТУАЛЬНЫЙ список работников на момент звонка
        workers = await db.get_order_workers_with_phones(order_id=order.id)
        logging.info(
            f'[call_scheduler] campaign_id={campaign_id} attempt={attempt_no}: '
            f'текущих работников в OrderWorker={len(workers)}'
        )

        # Определяем campaign_id для zvonok.com
        campaign_id_val = (
            config.zvonok_campaign_id_day.get_secret_value()
            if shift_type == 'day'
            else config.zvonok_campaign_id_night.get_secret_value()
        )

        called_count = 0
        skipped_count = 0

        for worker in workers:
            # Получаем или создаём результат для этого работника
            result = await db.get_or_create_call_result(
                campaign_id=campaign.id,
                worker_id=worker.id,
                phone_number=worker.phone_number
            )

            # Пропускаем, если уже есть финальный статус
            if result.status in ('green', 'red', 'blue', 'yellow'):
                logging.debug(
                    f'[call_scheduler] worker={worker.id} пропущен: '
                    f'уже финальный статус {result.status}'
                )
                skipped_count += 1
                continue

            # Пропускаем, если уже звонили в этой попытке или позже
            if result.attempt_no >= attempt_no:
                logging.debug(
                    f'[call_scheduler] worker={worker.id} пропущен: '
                    f'уже звонили (attempt_no={result.attempt_no})'
                )
                skipped_count += 1
                continue

            # Делаем звонок
            try:
                logging.info(
                    f'[call_scheduler] Звоню worker={worker.id} phone={worker.phone_number} '
                    f'campaign_id={campaign_id_val} attempt={attempt_no}'
                )
                call_id = await make_call(phone=worker.phone_number, campaign_id=campaign_id_val)
                logging.info(f'[call_scheduler] Звонок выполнен: call_id={call_id}')

                await db.update_call_result_attempt(
                    result_id=result.id,
                    zvonok_call_id=call_id,
                    attempt_no=attempt_no
                )

                # Планируем поллинг статуса через POLL_DELAY_MINUTES минут
                poll_time = datetime.now(MOSCOW_TZ) + timedelta(minutes=POLL_DELAY_MINUTES)
                poll_job_id = f'poll_{result.id}_attempt_{attempt_no}'
                if not scheduler.get_job(poll_job_id):
                    scheduler.add_job(
                        poll_call_status,
                        args=[result.id, attempt_no],
                        trigger='date',
                        run_date=poll_time,
                        id=poll_job_id,
                        replace_existing=True
                    )

                called_count += 1
                logging.info(
                    f'[call_scheduler] worker={worker.id} call_id={call_id} '
                    f'поллинг запланирован на {poll_time}'
                )

            except Exception as e:
                logging.exception(
                    f'[call_scheduler] Ошибка звонка worker={worker.id}: {e}'
                )
                skipped_count += 1

        logging.info(
            f'[call_scheduler] ✅ execute_campaign_attempt завершён: '
            f'campaign_id={campaign_id} attempt={attempt_no} | '
            f'позвонили={called_count}, пропущено={skipped_count}'
        )

    except Exception as e:
        logging.exception(
            f'[call_scheduler] ❌ ОШИБКА execute_campaign_attempt '
            f'campaign_id={campaign_id} attempt={attempt_no}: {e}'
        )


async def poll_call_status(result_id: int, attempt_no: int) -> None:
    """
    Опрашивает статус звонка после попытки прозвона.
    Упрощённая версия: следующие попытки уже запланированы на уровне кампании,
    здесь только проверяем статус и применяем блокировки.
    """
    try:
        result = await db.get_call_result(result_id=result_id)
        if not result or result.status not in ('pending',):
            return  # Уже обработан

        # Получаем кампанию для определения типа смены
        campaign = await db.get_campaign(campaign_id=result.campaign_id)
        if not campaign:
            logging.error(f'[call_scheduler] Кампания для result_id={result_id} не найдена')
            return

        order = await db.get_order(order_id=campaign.order_id)
        shift_type = 'day' if order.day_shift else 'night'
        total_attempts = len(CALL_OFFSETS[shift_type])

        raw_data = None
        status = 'pending'

        if result.zvonok_call_id:
            call_data = await get_call_status(call_id=result.zvonok_call_id)

            # Делаем fallback на calls_by_phone если:
            # 1) call_by_id не вернул данных
            # 2) ИЛИ вернул данные без голосовых полей (recognize_word/user_choice)
            if not call_data or not (call_data.get('recognize_word') or call_data.get('user_choice')):
                campaign_id_val = (
                    config.zvonok_campaign_id_day.get_secret_value()
                    if shift_type == 'day'
                    else config.zvonok_campaign_id_night.get_secret_value()
                )
                fallback = await get_call_status_by_phone(
                    campaign_id=campaign_id_val,
                    phone=result.phone_number,
                    call_id=result.zvonok_call_id
                )
                if fallback:
                    # Заменяем данные полными из calls_by_phone
                    call_data = fallback
                    logging.info(
                        f'[call_scheduler] result_id={result_id} используем calls_by_phone '
                        f'(call_by_id {"пусто" if not call_data else "без голосовых полей"})'
                    )

            if call_data:
                raw_data = json.dumps(call_data, ensure_ascii=False)
                status = map_zvonok_status(
                    call_status=call_data.get('call_status'),
                    dial_status=call_data.get('dial_status'),
                    button=call_data.get('button'),
                    recognize_word=call_data.get('recognize_word'),
                    user_choice=call_data.get('user_choice')
                )
                logging.info(
                    f'[call_scheduler] result_id={result_id} attempt={attempt_no} '
                    f'call_status={call_data.get("call_status")} '
                    f'dial_status={call_data.get("dial_status")} '
                    f'button={call_data.get("button")} '
                    f'recognize_word={call_data.get("recognize_word")} '
                    f'user_choice={call_data.get("user_choice")} '
                    f'→ mapped_status={status}'
                )
            else:
                logging.warning(
                    f'[call_scheduler] result_id={result_id} attempt={attempt_no} '
                    f'не удалось получить call_data ни из call_by_id, ни из calls_by_phone'
                )

        # Если получен green или red — финальные статусы, сохраняем
        if status in ('green', 'red'):
            await db.set_call_result_status(result_id, status, raw_data)
            logging.info(f'[call_scheduler] result_id={result_id} финальный статус: {status}')
            return

        # Если получен blue или yellow — сохраняем статус
        if status in ('blue', 'yellow'):
            await db.set_call_result_status(result_id, status, raw_data)
            # Если это последняя попытка, применяем блокировку
            if attempt_no >= total_attempts:
                if result.worker_id:
                    await db.set_worker_call_block(result.worker_id, status)
                    await _notify_worker_phone_verify(result.worker_id, reason=status)
                logging.info(f'[call_scheduler] result_id={result_id} все попытки исчерпаны → {status} + блокировка')
            else:
                logging.info(
                    f'[call_scheduler] result_id={result_id} получен {status}, '
                    f'следующая попытка кампании уже запланирована'
                )
            return

        # Последняя попытка, но статус всё ещё pending → устанавливаем yellow + блокировка
        if attempt_no >= total_attempts and status == 'pending':
            # Если звонок так и не был создан (API недоступен) — не блокируем работника
            if not result.zvonok_call_id:
                logging.warning(
                    f'[call_scheduler] result_id={result_id} все попытки исчерпаны, '
                    f'но call_id=None (API звонилки недоступен) → блокировка НЕ применяется'
                )
                return
            await db.set_call_result_status(result_id, 'yellow', raw_data)
            if result.worker_id:
                await db.set_worker_call_block(result.worker_id, 'yellow')
                await _notify_worker_phone_verify(result.worker_id, reason='yellow')
            logging.info(f'[call_scheduler] result_id={result_id} все попытки исчерпаны, статус pending → yellow + блокировка')

    except Exception as e:
        logging.exception(
            f'[call_scheduler] Ошибка poll_call_status result_id={result_id} attempt={attempt_no}: {e}'
        )


async def _notify_worker_phone_verify(worker_id: int, reason: str) -> None:
    """
    Отправить исполнителю уведомление о необходимости актуализации телефона.
    reason: 'blue' (телефон недоступен) или 'yellow' (не отвечает).
    """
    try:
        user = await db.get_user_by_id(user_id=worker_id)
        if not user or not user.tg_id:
            return

        text = (
            "📲 <b>Подтверждение номера телефона</b>\n\n"
            "Чтобы взять заявку, введите <b>ваш действующий номер телефона, который сейчас у вас в руках.</b>\n"
            "На него придёт <b>SMS с кодом.</b>\n\n"
            "🔐 Введите код в чат — после этого доступ к заявкам автоматически восстановится.\n\n"
            "⚠️ Ограничение введено, так как мы не смогли с вами связаться (не ответили или телефон был недоступен).\n"
            "Проводим актуализацию номера для подтверждения связи и выплат.\n\n"
            "📌 Формат ввода любой:\n"
            "8903… / 903… / 7903… / +7903…\n\n"
            "Введите номер ниже 👇"
        )

        async with Bot(token=config.bot_token.get_secret_value()) as bot:
            await bot.send_message(
                chat_id=user.tg_id,
                text=text,
                parse_mode='HTML',
            )
            logging.info(
                f'[call_scheduler] Отправлено уведомление об актуализации телефона '
                f'worker_id={worker_id} reason={reason}'
            )
    except Exception as e:
        logging.exception(
            f'[call_scheduler] Ошибка отправки уведомления worker_id={worker_id}: {e}'
        )


async def cancel_calls_for_worker(order_id: int, worker_id: int) -> None:
    """
    Помечает результат звонка работника как отменённый.
    С новой схемой (динамическая проверка списка) звонки автоматически пропускаются
    для удалённых работников, но мы помечаем статус для истории.
    """
    try:
        order = await db.get_order(order_id=order_id)
        if not order:
            return

        shift_type = 'day' if order.day_shift else 'night'
        campaign = await db.get_campaign_by_order_id(order_id=order_id, shift=shift_type)
        if not campaign:
            return

        # Помечаем результат как cancelled (если существует)
        result = await db.get_call_result_by_campaign_and_worker(
            campaign_id=campaign.id,
            worker_id=worker_id
        )
        if result and result.status == 'pending':
            await db.set_call_result_status(result.id, 'cancelled', None)
            logging.info(
                f'[call_scheduler] Результат для worker={worker_id} помечен cancelled '
                f'(автоматически пропустится при следующей попытке кампании)'
            )

    except Exception as e:
        logging.exception(f'[call_scheduler] Ошибка при отмене для worker={worker_id}: {e}')


async def cancel_calls_for_order(order_id: int) -> None:
    """
    Отменить запланированные попытки кампании при удалении заказа.
    Отменяет джобы campaign_attempt и помечает все результаты как cancelled.
    """
    try:
        order = await db.get_order(order_id=order_id)
        if not order:
            logging.warning(f'[call_scheduler] Заявка {order_id} не найден при отмене звонков')
            return

        shift_type = 'day' if order.day_shift else 'night'
        campaign = await db.get_campaign_by_order_id(order_id=order_id, shift=shift_type)
        if not campaign:
            logging.info(f'[call_scheduler] Кампания для заявки {order_id} не найдена')
            return

        # Отменяем запланированные попытки кампании
        cancelled_jobs = []
        for attempt_no in range(1, len(CALL_OFFSETS[shift_type]) + 1):
            job_id = f'campaign_{campaign.id}_attempt_{attempt_no}'
            job = scheduler.get_job(job_id)
            if job:
                job.remove()
                cancelled_jobs.append(job_id)

        # Помечаем все результаты как cancelled
        results = await db.get_campaign_results(campaign_id=campaign.id)
        for result in results:
            if result.status == 'pending':
                await db.set_call_result_status(result.id, 'cancelled', None)

        logging.info(
            f'[call_scheduler] Отменена кампания для заказа {order_id}: '
            f'campaign_id={campaign.id}, отменено джобов={len(cancelled_jobs)}, '
            f'результатов помечено cancelled={len([r for r in results if r.status == "pending"])}'
        )

    except Exception as e:
        logging.exception(f'[call_scheduler] Ошибка отмены звонков для заказа {order_id}: {e}')


async def schedule_missing_campaigns() -> None:
    """
    Проверяет все активные заказы и планирует прозвоны для тех, у кого нет кампании.
    Вызывается при старте бота для обработки заказов, активированных до внедрения системы прозвонов.
    """
    try:
        logging.info('[call_scheduler] ========================================')
        logging.info('[call_scheduler] НАЧАЛО: Проверка активных заказов без прозвонов...')

        # Получаем все активные заказы
        orders = await db.get_orders_in_progress()

        logging.info(f'[call_scheduler] Найдено активных заказов: {len(orders) if orders else 0}')

        if not orders:
            logging.info('[call_scheduler] Нет активных заказов для планирования')
            logging.info('[call_scheduler] ========================================')
            return

        scheduled_count = 0
        skipped_count = 0
        
        for order in orders:
            try:
                logging.info(f'[call_scheduler] --- Обработка заказа {order.id} ---')
                shift_type = 'day' if order.day_shift else 'night'
                shift_str = order.day_shift or order.night_shift
                logging.info(
                    f'[call_scheduler] Заказ {order.id}: дата={order.date}, смена={shift_type}, время={shift_str}'
                )

                # Проверяем, есть ли уже кампания
                existing_campaign = await db.get_campaign_by_order_id(
                    order_id=order.id,
                    shift=shift_type
                )

                if existing_campaign:
                    logging.info(
                        f'[call_scheduler] Заказ {order.id} пропущен: кампания уже существует (campaign_id={existing_campaign.id})'
                    )
                    skipped_count += 1
                    continue

                # Проверяем, что время прозвона еще не прошло
                start_time = MOSCOW_TZ.localize(
                    datetime.strptime(
                        f'{order.date} {shift_str.split("-")[0].strip()}',
                        '%d.%m.%Y %H:%M'
                    )
                )

                now = datetime.now(MOSCOW_TZ)

                # Планируем только если начало смены ещё не наступило
                if now >= start_time:
                    logging.info(
                        f'[call_scheduler] Заказ {order.id} пропущен: смена уже началась '
                        f'(начало смены: {start_time.strftime("%d.%m.%Y %H:%M")}, сейчас: {now.strftime("%d.%m.%Y %H:%M")})'
                    )
                    skipped_count += 1
                    continue

                # Планируем прозвон
                logging.info(f'[call_scheduler] Заказ {order.id}: планирую прозвон...')
                await schedule_call_campaign(order_id=order.id)
                scheduled_count += 1
                logging.info(f'[call_scheduler] Заказ {order.id}: прозвон успешно запланирован')
                
            except Exception as e:
                logging.exception(
                    f'[call_scheduler] ❌ ОШИБКА планирования прозвона для заказа {order.id}: {e}'
                )
                skipped_count += 1

        logging.info('[call_scheduler] ========================================')
        logging.info(
            f'[call_scheduler] ЗАВЕРШЕНО: Проверка активных заказов | '
            f'Всего заказов: {len(orders)} | '
            f'Запланировано: {scheduled_count} | '
            f'Пропущено: {skipped_count}'
        )
        logging.info('[call_scheduler] ========================================')

    except Exception as e:
        logging.exception(f'[call_scheduler] ❌ КРИТИЧЕСКАЯ ОШИБКА при проверке активных заказов: {e}')
