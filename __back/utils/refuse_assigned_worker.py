"""Общая логика отказа от уже подтверждённой заявки (OrderWorker) — бот и web API."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions, Message

import database as db
import keyboards.inline as ikb
import texts as txt
from database.models import User
from utils import delete_reminder, get_day_of_week_by_date
from utils.scheduler import schedule_expire_no_show_buttons

if TYPE_CHECKING:
    from aiogram import Bot


def strip_html_plain(s: str) -> str:
    t = re.sub(r'<[^>]+>', '', s or '')
    return re.sub(r'\s+\n', '\n', t).strip()


@dataclass
class RefuseAssignedResult:
    blocked_by_time: bool = False
    """Сообщение для веба / ответа API (без HTML)."""
    message_plain: str = ''
    """Для Telegram: обновить сообщение чата (если передан tg_message)."""
    tg_edit: dict[str, Any] | None = None


async def refuse_assigned_order_worker(
    *,
    worker_app_id: int,
    actor_user: User,
    bot: Bot,
    tg_message: Message | None = None,
    skip_entry_checks: bool = False,
) -> RefuseAssignedResult:
    """
    Повторяет сценарий ConfirmRemoveWorker из handlers/user/menu/user_applications.py.
    tg_message: если задан — выполняется edit_text как в боте; иначе только рассылки и БД.
    skip_entry_checks: True — проверки владельца и времени уже выполнены (например, в хендлере бота перед callback.answer).
    """
    worker_app_data = await db.get_worker_app_data(worker_app_id=worker_app_id)
    if not skip_entry_checks:
        if not worker_app_data or worker_app_data.worker_id != actor_user.id:
            return RefuseAssignedResult(message_plain='Запись не найдена')
        if await db.check_time(order_id=worker_app_data.order_id):
            return RefuseAssignedResult(
                blocked_by_time=True,
                message_plain=strip_html_plain(txt.cant_delete_application()),
            )
    elif not worker_app_data:
        return RefuseAssignedResult(message_plain='Запись не найдена')

    order = await db.get_order(order_id=worker_app_data.order_id)
    if not order:
        return RefuseAssignedResult(message_plain='Заявка не найдена')
    user = actor_user

    order_worker = await db.get_order_worker(worker_id=user.id, order_id=order.id)
    if not order_worker:
        return RefuseAssignedResult(message_plain='Запись исполнителя по заявке не найдена')
    real_data = await db.get_user_real_data_by_id(user_id=user.id)
    if not real_data:
        logging.error('refuse_assigned: нет DataForSecurity для user_id=%s', user.id)
        return RefuseAssignedResult(message_plain='Не удалось загрузить данные профиля')

    await db.order_set_search_workers(order_id=worker_app_data.order_id)
    tg_id_for_reminder = int(user.tg_id or 0)
    if tg_id_for_reminder:
        try:
            await delete_reminder(tg_id=tg_id_for_reminder, order_id=worker_app_data.order_id)
        except Exception:
            pass

    is_late_cancellation = await db.check_time_less_than_12_hours(order_id=worker_app_data.order_id)

    if is_late_cancellation and not order_worker.added_by_manager:
        try:
            cycle = await db.get_or_create_debtor_cycle(worker_id=user.id)
            event = await db.create_no_show_event(
                cycle_id=cycle.id,
                order_archive_id=None,
                no_show_date=order.date,
                assigned_amount=3000,
            )
            accountants = await db.get_all_accountants()
            worker_full_name = f'{real_data.last_name} {real_data.first_name}'
            if real_data.middle_name:
                worker_full_name += f' {real_data.middle_name}'

            card_text = (
                f'⚠️ <b>{worker_full_name}</b>\n'
                f'отказался от заявки менее чем за 12 часов до начала смены.\n\n'
                f'💼 В соответствии с п. 8.10 Договора, Исполнитель обязан возместить организационные расходы в размере 3 000 ₽.\n\n'
                f'📅 Дата заказа: <b>{order.date}</b>\n'
                f'🆔 ID события: <code>{event.id}</code>\n'
                f'⏰ Поздний отказ от заявки\n\n'
                f'Подтвердите сумму или измените её при необходимости.'
            )
            keyboard = [
                [InlineKeyboardButton(text='✅ Подтвердить 3 000 ₽', callback_data=f'NoShowConfirm:{event.id}')],
                [InlineKeyboardButton(text='✏️ Изменить сумму', callback_data=f'NoShowChangeAmount:{event.id}')],
            ]
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            for accountant in accountants:
                try:
                    msg = await bot.send_message(
                        chat_id=accountant.tg_id,
                        text=card_text,
                        reply_markup=markup,
                        parse_mode='HTML',
                    )
                    await db.add_cashier_message(
                        event_id=event.id,
                        cashier_tg_id=accountant.tg_id,
                        message_id=msg.message_id,
                    )
                except Exception as e:
                    logging.error('Ошибка отправки карточки кассиру %s: %s', accountant.tg_id, e)

            await schedule_expire_no_show_buttons(event_id=event.id)
        except Exception:
            logging.exception('Ошибка при создании санкции за поздний отказ')

    tg_edit: dict[str, Any] | None = None
    message_plain = ''

    if not order_worker.added_by_manager:
        if user.rejections + 1 > 1:
            tg_edit = {
                'text': txt.not_first_rejection(),
                'reply_markup': ikb.support(),
                'link_preview_options': LinkPreviewOptions(is_disabled=True),
            }
            message_plain = strip_html_plain(txt.not_first_rejection())
            await db.set_block(worker_id=user.id)
        else:
            tg_edit = {'text': txt.first_rejection()}
            message_plain = strip_html_plain(txt.first_rejection())
    else:
        tg_edit = {'text': txt.order_worker_deleted_without_rejection()}
        message_plain = strip_html_plain(txt.order_worker_deleted_without_rejection())

    if tg_message and tg_edit:
        kwargs = dict(tg_edit)
        lp = kwargs.pop('link_preview_options', None)
        if lp is not None:
            await tg_message.edit_text(**kwargs, link_preview_options=lp)
        else:
            await tg_message.edit_text(**kwargs)

    skip_users = await db.skip_users(order_id=worker_app_data.order_id)
    actor_tg = int(user.tg_id or 0)
    if actor_tg:
        skip_users.append(actor_tg)

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

    users_in_city = await db.get_users_by_city(city=order.city)
    for recipient in users_in_city:
        if recipient.tg_id in skip_users:
            continue

        job_fp = await db.get_job_fp_for_txt(worker_id=recipient.id)
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
        if recipient.tg_id:
            try:
                await bot.send_message(
                    chat_id=recipient.tg_id,
                    text=order_text,
                    reply_markup=ikb.respond_to_an_order(order_id=order.id),
                )
            except Exception:
                pass
        if max_bot and recipient.max_id:
            try:
                await max_bot.send_message(
                    user_id=recipient.max_id,
                    text=order_text,
                    attachments=[max_kb.respond_to_an_order(order_id=order.id)],
                    parse_mode=MaxParseMode.HTML,
                )
            except Exception:
                pass

    if max_bot:
        try:
            await max_bot.close_session()
        except Exception:
            pass

    managers = await db.get_managers_tg_id()
    directors = await db.get_directors_tg_id()
    recipients2 = list(managers) + list(directors)
    full_name = f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}'
    organization = await db.get_customer_organization(order.customer_id)

    for rid in recipients2:
        try:
            await bot.send_message(
                chat_id=rid,
                text=txt.cancelled_order_card(
                    city=order.city,
                    customer=organization,
                    job_name=order.job_name,
                    date=order.date,
                    day_shift=order.day_shift,
                    night_shift=order.night_shift,
                ),
            )
            await bot.send_message(
                chat_id=rid,
                text=txt.manager_delete_order_worker_notification(
                    worker_full_name=full_name,
                    city=order.city,
                    customer=organization,
                    job_name=order.job_name,
                    date=order.date,
                    day_shift=order.day_shift,
                    night_shift=order.night_shift,
                ),
            )
        except Exception:
            pass

    foremen = await db.get_foremen_by_customer_id(customer_id=order.customer_id)
    for foreman in foremen:
        if foreman.tg_id in skip_users:
            try:
                await bot.send_message(
                    chat_id=foreman.tg_id,
                    text=txt.foreman_delete_order_worker_notification(
                        worker_full_name=full_name,
                        phone_number=real_data.phone_number,
                        city=order.city,
                        customer=organization,
                        job_name=order.job_name,
                        date=order.date,
                        day_shift=order.day_shift,
                        night_shift=order.night_shift,
                    ),
                )
            except Exception:
                pass

    await db.delete_order_worker_by_id(worker_app_id=worker_app_id)
    if worker_app_data.order_from_friend:
        await db.delete_order_for_friend_log(order_id=order.id, worker_id=worker_app_data.worker_id)
    if not order_worker.added_by_manager:
        await db.update_rejections(worker_id=worker_app_data.worker_id)
        await db.update_rating_total_orders(user_id=worker_app_data.worker_id)

    return RefuseAssignedResult(blocked_by_time=False, message_plain=message_plain, tg_edit=tg_edit)
