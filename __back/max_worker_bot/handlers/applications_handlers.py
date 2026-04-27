"""
Обработчики управления заявками для Max бота
Адаптировано из Telegram бота
"""
from decimal import Decimal
from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
import logging

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from max_worker_bot.keyboards import worker_keyboards as kb
from max_worker_bot.states import ApplicationsStates
from utils import (
    delete_reminder,
    get_day_of_week_by_date,
    get_rating_coefficient,
    get_rating
)
from utils.max_delivery import remember_dialog_from_event
from utils.debtor_pricing import calculate_reduced_unit_price
import database as db
import texts.worker as txt
import texts.admin as txt_admin


router = Router()
logger = logging.getLogger(__name__)


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def open_application(event: MessageCallback, context: MemoryContext, page: int):
    """Открыть конкретную заявку исполнителя"""

    user = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    orders = await db.get_orders_by_worker_id(worker_id=user.id)

    if not orders or page >= len(orders) or page < 0:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    day = get_day_of_week_by_date(date=orders[page].date)
    rating = await get_rating(user_id=user.id)
    coefficient = get_rating_coefficient(rating=rating[:-1])
    unit_price = Decimal(orders[page].amount.replace(',', '.'))
    withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user.id)
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = unit_price * coefficient

    text = await txt.user_applications(
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
    )

    keyboard = await kb.remove_application(
        order_id=orders[page].id,
        worker_id=user.id,
        page=page + 1,
        count=len(orders),
        state=context
    )

    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=text,
            attachments=[keyboard],
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await event.message.answer(
            text=text,
            attachments=[keyboard],
            parse_mode=ParseMode.HTML
        )


# ==================== УПРАВЛЕНИЕ ЗАЯВКАМИ ====================

@router.message_callback(F.callback.payload == 'Reject')
@router.message_callback(F.callback.payload == 'manage_applications')
@router.message_created(F.message.body.text == '📝 Управление заявкой')
async def manage_applications(event: MessageCreated | MessageCallback, context: MemoryContext):
    """Открыть меню управления заявками"""
    remember_dialog_from_event(event)

    # Очищаем состояние при входе
    await context.clear()

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        if isinstance(event, MessageCreated):
            await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        else:
            await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    orders = await db.get_orders_by_worker_id(worker_id=worker.id)

    if not orders:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    page = 0
    await context.update_data(applications_page=page)

    day = get_day_of_week_by_date(date=orders[page].date)
    rating = await get_rating(user_id=worker.id)
    coefficient = get_rating_coefficient(rating=rating[:-1])
    unit_price = Decimal(orders[page].amount.replace(',', '.'))
    withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=worker.id)
    if withholding > 0:
        amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
    else:
        amount = unit_price * coefficient

    text = await txt.user_applications(
        worker_id=worker.id,
        customer_id=orders[page].customer_id,
        order_id=orders[page].id,
        city=orders[page].city,
        job=orders[page].job_name,
        date=orders[page].date,
        day_shift=orders[page].day_shift,
        night_shift=orders[page].night_shift,
        amount=amount,
        day=day
    )

    keyboard = await kb.remove_application(
        order_id=orders[page].id,
        worker_id=worker.id,
        page=page + 1,
        count=len(orders),
        state=context
    )

    if isinstance(event, MessageCreated):
        await event.message.answer(text=text, attachments=[keyboard], parse_mode=ParseMode.HTML)
    else:
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=text,
                attachments=[keyboard],
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await event.message.answer(text=text, attachments=[keyboard], parse_mode=ParseMode.HTML)


# ==================== НАВИГАЦИЯ ====================

@router.message_callback(F.callback.payload == 'UserApplicationsForward')
async def applications_forward(event: MessageCallback, context: MemoryContext):
    """Следующая заявка"""

    data = await context.get_data()
    page = data.get('applications_page', 0) + 1

    await open_application(event=event, context=context, page=page)
    await context.update_data(applications_page=page)


@router.message_callback(F.callback.payload == 'UserApplicationsBack')
async def applications_back(event: MessageCallback, context: MemoryContext):
    """Предыдущая заявка"""

    data = await context.get_data()
    page = data.get('applications_page', 0) - 1

    await open_application(event=event, context=context, page=page)
    await context.update_data(applications_page=page)


# ==================== УДАЛЕНИЕ ОТКЛИКА ====================

@router.message_callback(F.callback.payload.startswith('RemoveApplication:'))
async def remove_application(event: MessageCallback):
    """Подтверждение удаления отклика"""

    application_id = event.callback.payload.split(':')[1]

    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=txt.remove_application(),
            attachments=[kb.accept_remove_application(application_id=application_id)],
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await event.message.answer(
            text=txt.remove_application(),
            attachments=[kb.accept_remove_application(application_id=application_id)],
            parse_mode=ParseMode.HTML
        )


@router.message_callback(F.callback.payload.startswith('ConfirmRemoveApplication:'))
async def confirm_remove_application(event: MessageCallback):
    """Удаление отклика"""

    application_id = int(event.callback.payload.split(':')[1])

    await db.delete_application(application_id=application_id)

    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=txt.application_removed(),
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await event.message.answer(text=txt.application_removed(), parse_mode=ParseMode.HTML)


# ==================== ОТКАЗ ОТ ЗАЯВКИ ====================

@router.message_callback(F.callback.payload.startswith('RemoveWorker:'))
async def remove_worker(event: MessageCallback):
    """Подтверждение отказа от заявки"""

    worker_app_id = int(event.callback.payload.split(':')[1])
    order_worker = await db.get_worker_app_data(worker_app_id=worker_app_id)
    if not order_worker:
        await event.message.answer(
            text=txt.application_none(),
            parse_mode=ParseMode.HTML
        )
        return

    if not order_worker.added_by_manager:
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=txt.remove_worker(),
                attachments=[kb.confirmation_remove_worker(worker_id=worker_app_id)],
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await event.message.answer(
                text=txt.remove_worker(),
                attachments=[kb.confirmation_remove_worker(worker_id=worker_app_id)],
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=txt.remove_worker_manager_app(),
                attachments=[kb.confirmation_remove_worker(worker_id=worker_app_id)],
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await event.message.answer(
                text=txt.remove_worker_manager_app(),
                attachments=[kb.confirmation_remove_worker(worker_id=worker_app_id)],
                parse_mode=ParseMode.HTML
            )


@router.message_callback(F.callback.payload.startswith('ConfirmRemoveWorker:'))
async def confirm_remove_worker(event: MessageCallback):
    """Подтверждение и обработка отказа от заявки"""

    worker_app_id = int(event.callback.payload.split(':')[1])
    worker_app_data = await db.get_worker_app_data(worker_app_id=worker_app_id)
    if not worker_app_data:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    check_time = await db.check_time(order_id=worker_app_data.order_id)

    if check_time:
        await event.message.answer(text=txt.cant_delete_application(), parse_mode=ParseMode.HTML)
        return

    order = await db.get_order(order_id=worker_app_data.order_id)
    user = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not order or not user:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    await db.order_set_search_workers(order_id=worker_app_data.order_id)

    # Удаляем напоминание
    try:
        await delete_reminder(
            max_id=event.from_user.user_id,
            order_id=worker_app_data.order_id
        )
    except Exception as e:
        logger.error(f"Ошибка удаления напоминания: {e}")

    order_worker = await db.get_order_worker(
        worker_id=user.id,
        order_id=order.id
    )
    if not order_worker:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    real_data = await db.get_user_real_data_by_id(user_id=user.id)
    if not real_data:
        await event.message.answer(text=txt.application_none(), parse_mode=ParseMode.HTML)
        return

    # Проверяем, отказ менее чем за 12 часов
    is_late_cancellation = await db.check_time_less_than_12_hours(order_id=worker_app_data.order_id)

    # Если отказ поздний и не добавлен менеджером - создаем санкцию
    if is_late_cancellation and not order_worker.added_by_manager:
        try:
            cycle = await db.get_or_create_debtor_cycle(worker_id=user.id)
            await db.create_no_show_event(
                cycle_id=cycle.id,
                order_archive_id=None,
                no_show_date=order.date,
                assigned_amount=3000
            )

            # Уведомляем кассиров (если есть в Max - адаптировать под вашу систему)
            accountants = await db.get_all_accountants()
            worker_full_name = f"{real_data.last_name} {real_data.first_name}"
            if real_data.middle_name:
                worker_full_name += f" {real_data.middle_name}"

            notification_text = (
                f"⚠️ {worker_full_name} отказался от заявки менее чем за 12 часов.\n"
                f"Дата заказа: {order.date}\n"
                f"Назначена санкция: 3000 ₽"
            )

            for accountant in accountants:
                if not accountant.max_id:
                    continue
                try:
                    await event.bot.send_message(
                        chat_id=accountant.max_id,
                        text=notification_text,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления кассира: {e}")

        except Exception as e:
            logger.exception(f"Ошибка создания санкции: {e}")

    # Обработка отказа в зависимости от количества отказов
    if not order_worker.added_by_manager:
        mid = event.message.body.mid
        if user.rejections + 1 > 1:
            try:
                await event.bot.edit_message(
                    message_id=mid,
                    text=txt.not_first_rejection(),
                    attachments=[kb.support_keyboard()],
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                await event.message.answer(
                    text=txt.not_first_rejection(),
                    attachments=[kb.support_keyboard()],
                    parse_mode=ParseMode.HTML
                )
            await db.set_block(worker_id=user.id)
        else:
            # Уведомляем менеджеров
            managers = await db.get_managers_tg_id()
            directors = await db.get_directors_tg_id()
            recipients = list(managers) + list(directors)

            try:
                from aiogram import Bot as TelegramBot
                from max_worker_bot.config_reader import config as _cfg
                _tg_bot = TelegramBot(token=_cfg.bot_token.get_secret_value())
                for tg_id in recipients:
                    try:
                        await _tg_bot.send_message(
                            chat_id=tg_id,
                            text=txt.rejection_notification(
                                last_name=real_data.last_name,
                                first_name=real_data.first_name,
                                middle_name=real_data.middle_name
                            ),
                        )
                    except Exception:
                        pass
                await _tg_bot.session.close()
            except Exception:
                pass

            try:
                await event.bot.edit_message(message_id=mid, text=txt.first_rejection(), parse_mode=ParseMode.HTML)
            except Exception:
                await event.message.answer(text=txt.first_rejection(), parse_mode=ParseMode.HTML)
    else:
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text=txt.order_worker_deleted_without_rejection(),
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await event.message.answer(text=txt.order_worker_deleted_without_rejection(), parse_mode=ParseMode.HTML)

    # Рассылаем заявку другим исполнителям
    users = await db.get_users_by_city(city=order.city)
    skip_users = await db.skip_users(order_id=worker_app_data.order_id)
    skip_users.append(event.from_user.user_id)

    day = get_day_of_week_by_date(date=order.date)
    for city_user in users:
        if not city_user.max_id or city_user.max_id in skip_users:
            continue

        try:
            job_fp = await db.get_job_fp_for_txt(worker_id=city_user.id)
            await event.bot.send_message(
                chat_id=city_user.max_id,
                text=await txt.sending_order_to_users(
                    city=order.city,
                    customer_id=order.customer_id,
                    job=order.job_name,
                    date=order.date,
                    day=day,
                    day_shift=order.day_shift,
                    night_shift=order.night_shift,
                    amount=order.amount,
                    job_fp=job_fp,
                ),
                attachments=[kb.respond_to_an_order(order_id=order.id)],
                parse_mode=ParseMode.HTML
            )
        except:
            pass

    # Уведомляем менеджеров об отказе
    managers = await db.get_managers_tg_id()
    directors = await db.get_directors_tg_id()
    recipients = list(managers) + list(directors)
    full_name = f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}'
    organization = await db.get_customer_organization(order.customer_id)

    try:
        from aiogram import Bot as TelegramBot
        from max_worker_bot.config_reader import config as _cfg
        _tg_bot = TelegramBot(token=_cfg.bot_token.get_secret_value())
        for tg_id in recipients:
            try:
                await _tg_bot.send_message(
                    chat_id=tg_id,
                    text=txt.manager_delete_order_worker_notification(
                        worker_full_name=full_name,
                        city=order.city,
                        customer=organization,
                        job_name=order.job_name,
                        date=order.date,
                        day_shift=order.day_shift,
                        night_shift=order.night_shift
                    ),
                )
            except Exception:
                pass
        await _tg_bot.session.close()
    except Exception:
        pass

    # Удаляем запись о работнике
    await db.delete_order_worker_by_id(worker_app_id=worker_app_id)

    if worker_app_data.order_from_friend:
        await db.delete_order_for_friend_log(
            order_id=order.id,
            worker_id=worker_app_data.worker_id
        )

    if not order_worker.added_by_manager:
        await db.update_rejections(worker_id=worker_app_data.worker_id)
        await db.update_rating_total_orders(user_id=worker_app_data.worker_id)


# ==================== КАК ДОБРАТЬСЯ ====================

@router.message_callback(F.callback.payload.startswith('WorkerShowCityWay:'))
async def worker_show_city_way(event: MessageCallback):
    """Показать маршрут к месту работы"""
    parts = event.callback.payload.split(':')
    customer_id = int(parts[1])
    city = parts[2]

    city_id = await db.get_customer_city_id(customer_id=customer_id, city=city)
    if not city_id:
        await event.message.answer(
            text="ℹ️ Информация о маршруте не найдена.",
            parse_mode=ParseMode.HTML
        )
        return

    city_way = await db.get_customer_city_way(city_id=city_id)
    if not city_way:
        await event.message.answer(
            text="ℹ️ Информация о маршруте не найдена.",
            parse_mode=ParseMode.HTML
        )
        return

    caption = txt_admin.admin_city_way_caption(description=city_way.way_to_job)
    photos = [item.photo for item in city_way.city_photos]

    if photos:
        try:
            from aiogram import Bot as TgBot
            from maxapi.enums.upload_type import UploadType
            from max_worker_bot.upload_utils import upload_buffer
            from config_reader import config as cfg

            tg_bot = TgBot(token=cfg.bot_token.get_secret_value())
            attachments = []
            for file_id in photos:
                try:
                    tg_file = await tg_bot.get_file(file_id)
                    file_bytes = await tg_bot.download_file(tg_file.file_path)
                    att = await upload_buffer(
                        bot=event.bot,
                        buffer=file_bytes.read(),
                        upload_type=UploadType.IMAGE,
                    )
                    if att:
                        attachments.append(att)
                except Exception as e:
                    logger.error(f"Ошибка загрузки фото {file_id}: {e}")
            await tg_bot.session.close()

            if attachments:
                await event.message.answer(
                    text=caption,
                    attachments=attachments,
                    parse_mode=ParseMode.HTML
                )
                return
        except Exception as e:
            logger.error(f"Ошибка отправки фото маршрута: {e}")

    await event.message.answer(
        text=caption,
        parse_mode=ParseMode.HTML
    )
