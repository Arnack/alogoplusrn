"""
Обработчики профиля и дополнительных функций для Max бота
Включает: просмотр профиля, смену города, реферальную систему
Адаптировано из Telegram бота
"""
import asyncio
from decimal import Decimal
from datetime import datetime

from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from max_worker_bot.keyboards import worker_keyboards as kb
from max_worker_bot.states import ChangeCityStates, ReferralStates, ShoutStates, ProfileStates
from utils import get_rating, luhn_check, truncate_decimal, is_number, write_worker_wp_log
from utils.max_delivery import send_max_message, remember_dialog_from_event
from utils.organizations import orgs_dict
import database as db
import texts as txt
import keyboards.inline as ikb
from API import update_worker_bank_card, create_all_contracts_for_worker, sign_all_worker_contracts
from API.fin.contracts import fin_get_worker_contracts_all_orgs, fin_get_worker_contracts_with_pdfs

ORG_IDS = [392, 393, 480]


router = Router()


# ==================== ПРОФИЛЬ ====================

@router.message_created(F.message.body.text == '👤 Обо мне')
@router.message_callback(F.callback.payload == 'about_me')
async def show_profile(event, context: MemoryContext):
    """Показать информацию о профиле исполнителя"""
    remember_dialog_from_event(event)

    # Очищаем состояние
    await context.clear()

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    # Получаем рейтинг и формируем текст профиля
    rating = await get_rating(user_id=worker.id)

    await event.message.answer(
        text=await txt.about_worker(user_id=worker.id, rating=rating),
        attachments=[await kb.about_worker_keyboard(worker_id=worker.id, api_worker_id=worker.api_id)],
        parse_mode=ParseMode.HTML
    )


@router.message_callback(F.callback.payload == 'BackToAboutMe')
async def back_to_profile(event: MessageCallback):
    """Вернуться к профилю"""
    remember_dialog_from_event(event)

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    rating = await get_rating(user_id=worker.id)

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=await txt.about_worker(user_id=worker.id, rating=rating),
            attachments=[await kb.about_worker_keyboard(worker_id=worker.id, api_worker_id=worker.api_id)],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=await txt.about_worker(user_id=worker.id, rating=rating),
            attachments=[await kb.about_worker_keyboard(worker_id=worker.id, api_worker_id=worker.api_id)],
            parse_mode=ParseMode.HTML
        )


# ==================== СМЕНА ГОРОДА ====================

@router.message_callback(F.callback.payload == 'UpdateWorkerCity')
async def start_change_city(event: MessageCallback, context: MemoryContext):
    """Начало процесса смены города"""
    remember_dialog_from_event(event)

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    # В Max можно редактировать только последнее сообщение
    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.accept_change_city(current_city=worker.city),
            attachments=[kb.accept_change_city_keyboard()],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        # Если редактирование не удалось - отправляем новое сообщение
        await event.message.answer(
            text=txt.accept_change_city(current_city=worker.city),
            attachments=[kb.accept_change_city_keyboard()],
            parse_mode=ParseMode.HTML
        )

    await context.set_state(ChangeCityStates.confirming_change)


@router.message_callback(ChangeCityStates.confirming_change, F.callback.payload == 'AcceptChangeCity')
async def accept_change_city(event: MessageCallback, context: MemoryContext):
    """Подтверждение желания сменить город"""
    remember_dialog_from_event(event)

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.choose_city(),
            attachments=[await kb.choose_city_keyboard(current_city=worker.city)],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=txt.choose_city(),
            attachments=[await kb.choose_city_keyboard(current_city=worker.city)],
            parse_mode=ParseMode.HTML
        )

    await context.set_state(ChangeCityStates.choosing_city)


@router.message_callback(ChangeCityStates.confirming_change, F.callback.payload == 'RejectChangeCity')
async def reject_change_city(event: MessageCallback, context: MemoryContext):
    """Отмена смены города"""
    remember_dialog_from_event(event)

    await back_to_profile(event=event)
    await context.clear()


@router.message_callback(ChangeCityStates.choosing_city, F.callback.payload.startswith('ChooseCity:'))
async def choose_new_city(event: MessageCallback, context: MemoryContext):
    """Выбор нового города"""
    remember_dialog_from_event(event)

    new_city = event.callback.payload.split(':')[1]
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.confirmation_update_city(
                old_city=worker.city,
                new_city=new_city
            ),
            attachments=[kb.confirmation_change_city_keyboard(new_city=new_city)],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=txt.confirmation_update_city(
                old_city=worker.city,
                new_city=new_city
            ),
            attachments=[kb.confirmation_change_city_keyboard(new_city=new_city)],
            parse_mode=ParseMode.HTML
        )

    await context.update_data(new_city=new_city)
    await context.set_state(ChangeCityStates.final_confirmation)


@router.message_callback(ChangeCityStates.final_confirmation, F.callback.payload.startswith('ConfirmChangeCity:'))
async def confirm_change_city(event: MessageCallback, context: MemoryContext):
    """Финальное подтверждение смены города"""
    remember_dialog_from_event(event)

    new_city = event.callback.payload.split(':')[1]
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    # Создаем запрос на смену города менеджеру
    request_id = await db.set_change_city_request(
        worker_id=worker.id
    )

    if request_id:
        try:
            await event.bot.edit_message(message_id=event.message.body.mid,text=txt.request_to_change_city_sent(), parse_mode=ParseMode.HTML)
        except (AttributeError, Exception):
            await event.message.answer(text=txt.request_to_change_city_sent(), parse_mode=ParseMode.HTML)

        # Уведомляем менеджеров в Telegram
        managers = await db.get_managers_tg_id()
        real_data = await db.get_user_real_data_by_id(user_id=worker.id)
        city_obj = await db.get_city_by_name(city_name=new_city)

        if not city_obj:
            import logging
            logging.error(f'[Max] confirm_change_city: город не найден в БД: {new_city!r}')
            await context.clear()
            return

        full_name = f"{real_data.last_name} {real_data.first_name}"
        if real_data.middle_name:
            full_name += f" {real_data.middle_name}"

        notification_text = txt.request_to_change_city_for_manager(
            worker_full_name=full_name,
            old_city=worker.city,
            new_city=new_city
        )

        try:
            from aiogram import Bot as TelegramBot
            from max_worker_bot.config_reader import config
            telegram_bot = TelegramBot(token=config.bot_token.get_secret_value())
            for manager_id in managers:
                try:
                    await telegram_bot.send_message(
                        chat_id=manager_id,
                        text=notification_text,
                        parse_mode="HTML",
                        reply_markup=ikb.confirmation_update_city_manager(
                            request_id=request_id,
                            new_city_id=city_obj.id,
                            worker_id=worker.id
                        )
                    )
                except Exception:
                    pass
            await telegram_bot.session.close()
        except Exception as e:
            import logging
            logging.exception(f'[Max] Ошибка отправки уведомления менеджерам о смене города: {e}')
    else:
        try:
            await event.bot.edit_message(message_id=event.message.body.mid,text=txt.request_to_change_city_error(), parse_mode=ParseMode.HTML)
        except (AttributeError, Exception):
            await event.message.answer(text=txt.request_to_change_city_error(), parse_mode=ParseMode.HTML)

    await context.clear()


# ==================== РЕФЕРАЛЬНАЯ СИСТЕМА ====================

@router.message_callback(F.callback.payload == 'ReferralSystem')
async def show_referral_info(event: MessageCallback, context: MemoryContext):
    """Показать информацию о реферальной системе"""
    remember_dialog_from_event(event)

    # Получаем настройки реферальной системы и данные пользователя
    settings = await db.get_settings()
    ref_info = await db.get_referral_info(tg_id=event.from_user.user_id)

    # Формируем реферальную ссылку
    # Примечание: адаптируйте под ваш домен Max бота
    referral_link = f"https://max.ru/bot?start=ref_{event.from_user.user_id}"

    # В Max можно редактировать только последнее сообщение
    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.referral(
                link=referral_link,
                bonus=settings.bonus,
                shifts=settings.shifts,
                friends=ref_info[0],
                completed=ref_info[1]
            ),
            attachments=[kb.referral_keyboard()],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        # Если редактирование не удалось - отправляем новое сообщение
        await event.message.answer(
            text=txt.referral(
                link=referral_link,
                bonus=settings.bonus,
                shifts=settings.shifts,
                friends=ref_info[0],
                completed=ref_info[1]
            ),
            attachments=[kb.referral_keyboard()],
            parse_mode=ParseMode.HTML
        )

    await context.set_state(ReferralStates.viewing_referral)


# ==================== ОПОВЕЩЕНИЕ НА ОБЪЕКТЕ ====================

@router.message_created(F.message.body.text == '📣 Оповещение на объекте')
@router.message_callback(F.callback.payload == 'shout_on_site')
async def show_shout_menu(event, context: MemoryContext):
    """Показать меню оповещения на объекте (для представителей)"""
    remember_dialog_from_event(event)

    # Очищаем состояние
    await context.clear()

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    # Проверяем, является ли работник представителем
    is_foreman = await db.is_foreman(worker_id=worker.id)

    if not is_foreman:
        await event.message.answer(text="❗ Эта функция доступна только представителям исполнителей", parse_mode=ParseMode.HTML)
        return

    # Получаем данные представителя
    foreman = await db.get_foreman_by_max_id(foreman_max_id=event.from_user.user_id)

    if not foreman:
        await event.message.answer(text="❗ Вы не зарегистрированы как представитель", parse_mode=ParseMode.HTML)
        return

    # Сохраняем данные для последующих обработчиков
    await context.update_data(foreman_full_name=foreman.full_name)

    # Проверяем наличие активного заказа
    check_order = await db.check_foreman_order_progress(
        customer_id=foreman.customer_id,
        foreman_tg_id=foreman.tg_id if foreman.tg_id else 0
    )

    if check_order:
        workers = await db.get_workers_from_order_workers(order_id=check_order.id)
        if len(workers) > 1:
            await context.update_data(order_id=check_order.id)
            await event.message.answer(
                text=txt.request_shout_message(),
                parse_mode=ParseMode.HTML
            )
            await context.set_state(ShoutStates.enter_message)
        else:
            await event.message.answer(
                text="❗ Недостаточно работников на объекте для отправки оповещения (минимум 2)",
                parse_mode=ParseMode.HTML
            )
    else:
        organization = await db.get_customer_organization(customer_id=foreman.customer_id)
        await event.message.answer(
            text=f"❗ У вас нет активного заказа на объекте {organization}",
            parse_mode=ParseMode.HTML
        )


@router.message_created(ShoutStates.enter_message, F.message.body.text)
async def send_shout_message(event: MessageCreated, context: MemoryContext):
    """Отправка оповещения всем исполнителям в Max и Telegram"""
    remember_dialog_from_event(event)

    # Исключаем текст кнопок главного меню
    menu_buttons = [
        '👤 Обо мне',
        '🔍 Поиск заявок',
        '🆘 СВЯЗЬ С РУКОВОДСТВОМ',
        '📝 Управление заявкой',
        '💼 Заявка для друга',
        '📣 Оповещение на объекте'
    ]

    if event.message.body.text in menu_buttons:
        # Это нажатие на кнопку меню - игнорируем и очищаем состояние
        await context.clear()
        return

    try:
        data = await context.get_data()

        # Проверяем наличие order_id в данных
        if 'order_id' not in data:
            await context.clear()
            return

        order_id = data['order_id']
        message_text = event.message.body.text
        sender_name = data.get('foreman_full_name', 'Представитель')

        # Создаем запись статистики
        shout_id = await db.set_shout_stat(
            sender_tg_id=event.from_user.user_id,  # Используем max_id как идентификатор
            order_id=order_id
        )

        # Получаем список всех работников на заказе
        workers = await db.get_workers_for_shout(order_id=order_id)

        # Создаем aiogram Bot для отправки в Telegram
        from aiogram import Bot as TelegramBot
        from max_worker_bot.config_reader import config
        telegram_bot = TelegramBot(token=config.bot_token.get_secret_value())

        sent_to_max = 0
        sent_to_telegram = 0

        for worker in workers:
            # Пропускаем отправителя
            if worker.max_id == event.from_user.user_id:
                continue

            # Формируем текст оповещения
            shout_text = f"📣 Оповещение от {sender_name}:\n\n{message_text}"

            # Отправка в Max (если есть max_id)
            if worker.max_id and worker.max_id != 0:
                try:
                    await send_max_message(
                        event.bot,
                        user_id=worker.max_id,
                        text=shout_text,
                        parse_mode=ParseMode.HTML
                    )
                    sent_to_max += 1
                except Exception:
                    pass

            # Отправка в Telegram (если есть tg_id)
            if worker.tg_id and worker.tg_id != 0:
                try:
                    await telegram_bot.send_message(
                        chat_id=worker.tg_id,
                        text=shout_text
                    )
                    sent_to_telegram += 1
                except Exception:
                    pass

        # Закрываем сессию Telegram бота
        await telegram_bot.session.close()

        # Обновляем количество отправленных сообщений
        total_sent = sent_to_max + sent_to_telegram
        await db.update_shout_workers(
            shout_id=shout_id,
            workers_count=total_sent
        )

        # Отправляем результат
        await event.message.answer(
            text=f"✅ Оповещение отправлено:\n"
                 f"📱 Max: {sent_to_max}\n"
                 f"✈️ Telegram: {sent_to_telegram}\n"
                 f"Всего: {total_sent} исполнителям",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        import logging
        logging.exception(f"Ошибка при отправке оповещения: {e}")
        await event.message.answer(
            text="❗ Ошибка при отправке оповещения. Попробуйте позже.",
            parse_mode=ParseMode.HTML
        )
    finally:
        await context.clear()


# Старый обработчик статистики закомментирован, так как использует несуществующие функции
# Функциональность статистики будет реализована позже


# ==================== ПРАВИЛА, БОНУСЫ, ОБНОВЛЕНИЕ/УДАЛЕНИЕ ДАННЫХ ====================

@router.message_callback(F.callback.payload == 'BotRules')
async def show_worker_rules(event: MessageCallback):
    """Показать правила для исполнителей"""
    rules = await db.get_rules(rules_for='workers')
    if rules:
        # Max API имеет лимит 4000 символов, разделяем на два сообщения если нужно
        rules_text = txt.show_rules_text(text=rules.rules, date=rules.date)

        if len(rules_text) > 3900:
            # Находим середину текста и ближайший перенос строки
            mid_point = len(rules_text) // 2
            split_point = rules_text.rfind('\n\n', mid_point - 500, mid_point + 500)
            if split_point == -1:
                split_point = rules_text.rfind('\n', mid_point - 500, mid_point + 500)
            if split_point == -1:
                split_point = mid_point

            # Разделяем на две части
            first_part = rules_text[:split_point].strip()
            second_part = f"<blockquote>{rules_text[split_point:].strip()}</blockquote>"

            # Отправляем первую часть
            await event.message.answer(
                text=first_part,
                parse_mode=ParseMode.HTML
            )

            # Отправляем вторую часть с клавиатурой
            await event.message.answer(
                text=second_part,
                attachments=[kb.back_to_menu_keyboard()],
                parse_mode=ParseMode.HTML
            )
        else:
            # Текст помещается в одно сообщение
            try:
                await event.bot.edit_message(message_id=event.message.body.mid,
                    text=rules_text,
                    attachments=[kb.back_to_menu_keyboard()],
                    parse_mode=ParseMode.HTML
                )
            except (AttributeError, Exception):
                await event.message.answer(
                    text=rules_text,
                    attachments=[kb.back_to_menu_keyboard()],
                    parse_mode=ParseMode.HTML
                )
    else:
        await event.message.answer(text=txt.no_rules(), parse_mode=ParseMode.HTML)


@router.message_callback(F.callback.payload == 'GetBonus')
async def show_get_bonus(event: MessageCallback, context: MemoryContext):
    """Показать реферальную систему (получить бонус)"""
    # Перенаправляем на реферальную систему
    await show_referral_info(event, context)


@router.message_callback(F.callback.payload == 'UpdateWorkerInfo')
async def update_worker_info_menu(event: MessageCallback):
    """Меню обновления данных исполнителя"""
    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.update_worker_info(),
            attachments=[await kb.choose_update_keyboard()],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=txt.update_worker_info(),
            attachments=[await kb.choose_update_keyboard()],
            parse_mode=ParseMode.HTML
        )


@router.message_callback(F.callback.payload == 'EraseWorkerInfo')
async def erase_worker_info(event: MessageCallback):
    """Удаление данных исполнителя"""
    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.erase_worker_info_warning(),
            attachments=[await kb.erase_worker_info_keyboard()],
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=txt.erase_worker_info_warning(),
            attachments=[await kb.erase_worker_info_keyboard()],
            parse_mode=ParseMode.HTML
        )


@router.message_callback(F.callback.payload == 'ConfirmEraseWorkerData')
async def confirm_erase_worker_data(event: MessageCallback):
    """Подтверждение удаления данных исполнителя"""

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    await db.erase_worker_data(user_id=worker.id)

    try:
        await event.bot.edit_message(message_id=event.message.body.mid,
            text=txt.worker_data_erased(),
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(
            text=txt.worker_data_erased(),
            parse_mode=ParseMode.HTML
        )


# ==================== ОБНОВЛЕНИЕ КАРТЫ ====================

@router.message_callback(F.callback.payload == 'UpdateWorkerBankCard')
async def request_new_card(event: MessageCallback, context: MemoryContext):
    """Запрос нового номера карты"""
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return
    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=txt.request_new_card(),
            parse_mode=ParseMode.HTML
        )
    except (AttributeError, Exception):
        await event.message.answer(text=txt.request_new_card(), parse_mode=ParseMode.HTML)
    await context.update_data(
        CurrentCard=worker.card,
        WorkerINN=worker.inn,
        ApiWorkerID=worker.api_id,
        WorkerID=worker.id,
    )
    await context.set_state(ProfileStates.card_to_update)


@router.message_created(ProfileStates.card_to_update, F.message.body.text)
async def get_card_number(event: MessageCreated, context: MemoryContext):
    """Обработка нового номера карты"""
    card = event.message.body.text.replace(' ', '')
    if not card.isdigit():
        await event.message.answer(text=txt.card_number_error(), parse_mode=ParseMode.HTML)
        return
    if not luhn_check(card):
        await event.message.answer(text=txt.luhn_check_error(), parse_mode=ParseMode.HTML)
        return
    if await db.card_unique(card):
        await event.message.answer(text=txt.card_not_unique_error(), parse_mode=ParseMode.HTML)
        return
    data = await context.get_data()
    if card == data.get('CurrentCard'):
        await event.message.answer(text=txt.same_card_error(), parse_mode=ParseMode.HTML)
        return
    await context.update_data(NewCard=card)
    await event.message.answer(text=txt.change_card_request_sign_contracts(), parse_mode=ParseMode.HTML)
    await context.set_state(ProfileStates.sign_contract_code_update_card)


@router.message_created(ProfileStates.sign_contract_code_update_card, F.message.body.text)
async def get_sign_contract_code_for_update_card(event: MessageCreated, context: MemoryContext):
    """Проверка кода подписания (4 последних цифры ИНН) при обновлении карты"""
    import asyncio as _asyncio
    import logging as _logging
    data = await context.get_data()
    inn = data.get('WorkerINN', '')
    if inn[-4:] != event.message.body.text.strip():
        await event.message.answer(text=txt.contract_inn_error(), parse_mode=ParseMode.HTML)
        return

    await context.set_state(None)
    wait_msg = await event.message.answer(text=txt.sign_contracts_for_card_wait(), parse_mode=ParseMode.HTML)

    api_worker_id = data.get('ApiWorkerID')
    new_card = data['NewCard']
    if not api_worker_id:
        _logging.warning(f'[max][card-update] отсутствует ApiWorkerID для user={event.from_user.user_id}')
        await event.bot.edit_message(
            message_id=wait_msg.message.body.mid,
            text=txt.update_card_error(),
            parse_mode=ParseMode.HTML
        )
        await context.clear()
        return

    card_updated = await update_worker_bank_card(api_worker_id=api_worker_id, bank_card=new_card)
    _logging.info(f'[max][card-update] worker={api_worker_id} карта обновлена в fin API: {card_updated}')

    if not card_updated:
        await event.bot.edit_message(message_id=wait_msg.message.body.mid, text=txt.update_card_error(), parse_mode=ParseMode.HTML)
        return

    contracts = await create_all_contracts_for_worker(worker_id=api_worker_id)
    _logging.info(f'[max][card-update] worker={api_worker_id} создано договоров: {len(contracts)}')
    if not contracts:
        await event.bot.edit_message(message_id=wait_msg.message.body.mid, text=txt.sign_contract_error(), parse_mode=ParseMode.HTML)
        return

    signed = await sign_all_worker_contracts(contracts)
    _logging.info(f'[max][card-update] worker={api_worker_id} подписание: {signed}')
    if not signed:
        await event.bot.edit_message(message_id=wait_msg.message.body.mid, text=txt.sign_contract_error(), parse_mode=ParseMode.HTML)
        return

    _asyncio.create_task(db.update_worker_bank_card(worker_id=data['WorkerID'], card=new_card))
    await event.bot.edit_message(message_id=wait_msg.message.body.mid, text=txt.bank_card_updated(), parse_mode=ParseMode.HTML)
    await context.clear()


# ==================== ПОЛУЧИТЬ ВОЗНАГРАЖДЕНИЕ ====================

@router.message_callback(F.callback.payload == 'CreateWorkerPayment')
async def create_worker_payment(event: MessageCallback, context: MemoryContext):
    """Запрос суммы выплаты из начислений"""
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return
    balance = await db.get_worker_balance_by_tg_id(tg_id=worker.tg_id)
    if balance >= Decimal('2600'):
        await event.message.answer(text=txt.request_amount_for_payment(), parse_mode=ParseMode.HTML)
        await context.update_data(WorkerBalance=str(balance), WorkerTgId=worker.tg_id, WorkerID=worker.id)
        await context.set_state(ProfileStates.request_payment_amount)
    else:
        await event.message.answer(text=txt.low_balance_error(), parse_mode=ParseMode.HTML)


@router.message_created(ProfileStates.request_payment_amount, F.message.body.text)
async def get_payment_amount(event: MessageCreated, context: MemoryContext):
    """Обработка введённой суммы выплаты"""
    import logging as _logging
    import asyncio as _asyncio
    from utils.payout_flow import create_contract_documents

    data = await context.get_data()
    amount = truncate_decimal(event.message.body.text.replace(',', '.'))

    if not is_number(amount):
        await event.message.answer(text='❗Введите сумму ещё раз:', parse_mode=ParseMode.HTML)
        return
    if Decimal(amount) < Decimal('2600'):
        await event.message.answer(text='❗Минимальная сумма 2600₽. Введите ещё раз:', parse_mode=ParseMode.HTML)
        return
    if Decimal(amount) > Decimal(data['WorkerBalance']):
        await event.message.answer(text='❗Сумма не может быть больше вашего баланса. Введите ещё раз:', parse_mode=ParseMode.HTML)
        return

    await context.set_state(None)
    tg_id = data['WorkerTgId']
    worker_id = data['WorkerID']

    wp_id = await db.set_wallet_payment(tg_id=tg_id, amount=amount)
    if wp_id:
        is_updated = await db.update_worker_balance(
            tg_id=tg_id,
            new_balance=str(Decimal(data['WorkerBalance']) - Decimal(amount)),
        )
        if is_updated:
            await event.message.answer(text=f'Выплата №{wp_id} создана. Вам придут уведомления', parse_mode=ParseMode.HTML)
            write_worker_wp_log(
                message=f'Исполнитель (max_id) {event.from_user.user_id} | Создал выплату №{wp_id} на {amount} руб.',
            )
            worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
            act_date = datetime.strftime(datetime.now(), '%d.%m.%Y')
            contracts = await create_contract_documents(
                user_id=worker_id,
                wallet_payment_id=wp_id,
                act_date=act_date,
            )

            accountants = await db.get_accountants_tg_id()
            from aiogram import Bot as TelegramBot
            from max_worker_bot.config_reader import config
            try:
                tg_bot = TelegramBot(token=config.bot_token.get_secret_value())
                for acc_tg_id in accountants:
                    try:
                        await tg_bot.send_message(
                            chat_id=acc_tg_id,
                            text=txt.new_wallet_payment_notification(
                                date=datetime.strftime(datetime.now(), '%d.%m.%Y'),
                            ),
                        )
                    except Exception:
                        pass
                await tg_bot.session.close()
            except Exception as e:
                _logging.exception(f'[max][payment] Ошибка уведомления кассиров: {e}')

            await event.message.answer(
                text=f'Договоры сформированы: {len(contracts)}. После выбора ИП кассиром вам придёт акт.',
                parse_mode=ParseMode.HTML,
            )
            await context.clear()
            return
        else:
            await db.update_wallet_payment_status(wp_id=wp_id, status='ERROR')

    await event.message.answer(text=txt.create_payment_error(), parse_mode=ParseMode.HTML)
    await context.clear()


# ==================== ПОДПИСАННЫЕ ДОГОВОРЫ ====================

@router.message_callback(F.callback.payload.startswith('GetWorkerContracts:'))
async def show_worker_contracts(event: MessageCallback, context: MemoryContext):
    """Скачать и отправить PDF договоров"""
    import logging
    from maxapi.enums.upload_type import UploadType
    from max_worker_bot.upload_utils import upload_buffer

    ctx_data = await context.get_data()
    if ctx_data.get('ContractsSending'):
        return
    await context.update_data(ContractsSending=True)

    api_worker_id = int(event.callback.payload.split(':')[1])
    try:
        contracts = await fin_get_worker_contracts_with_pdfs(api_worker_id, ORG_IDS)
        if not contracts:
            await event.message.answer(text='ℹ️ Договоры не найдены', parse_mode=ParseMode.HTML)
            return
        for contract in contracts:
            pdf_bytes = contract.get('pdf')
            org_id = contract.get('org_id')
            if not pdf_bytes:
                continue
            org_name = orgs_dict.get(org_id, f'ИП {org_id}')
            attachment = await upload_buffer(
                bot=event.bot,
                buffer=pdf_bytes,
                upload_type=UploadType.FILE,
                filename=f'contract_{org_id}',
            )
            if attachment:
                # Даём Max API время обработать загруженный файл
                await asyncio.sleep(8)
                sent = False
                for _attempt in range(3):
                    try:
                        await event.message.answer(
                            text=f'📁 Договор с {org_name}',
                            attachments=[attachment],
                            parse_mode=ParseMode.HTML,
                        )
                        sent = True
                        break
                    except Exception:
                        await asyncio.sleep(5)
                if not sent:
                    await event.message.answer(
                        text=f'❗ Не удалось загрузить договор с {org_name}',
                        parse_mode=ParseMode.HTML,
                    )
            else:
                await event.message.answer(
                    text=f'❗ Не удалось загрузить договор с {org_name}',
                    parse_mode=ParseMode.HTML,
                )
    except Exception as e:
        logging.exception(f'[max] show_worker_contracts: {e}')
        await event.message.answer(text='❗ Произошла ошибка при загрузке договоров', parse_mode=ParseMode.HTML)
    finally:
        await context.update_data(ContractsSending=False)


# ==================== АКЦИИ ====================

@router.message_callback(F.callback.payload == 'OpenPromotions')
async def open_promotions(event: MessageCallback):
    """Показать список акций"""
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return
    await _show_promotions(event, worker)


async def _show_promotions(event, worker):
    promos = await db.get_active_promotions_by_city(city=worker.city)
    all_parts = await db.get_worker_participations(worker_id=worker.id)
    parts_by_promo = {p.promotion_id: p for p in all_parts}

    text = '🎁 <b>Акции</b>\n\n'
    if not promos:
        text += 'Активных акций в вашем городе нет.'
    else:
        for p in promos:
            part = parts_by_promo.get(p.id)
            condition = (
                f'{p.n_orders} заявок подряд без пропусков'
                if p.type == 'streak'
                else f'{p.n_orders} заявок за {p.period_days} дн.'
            )
            reward = p.n_orders * p.bonus_amount
            text += f'<b>{p.name}</b>\nУсловие: {condition} → +{reward} ₽\n'
            if part:
                progress = (
                    f'{part.current_streak}/{p.n_orders} 🔥'
                    if p.type == 'streak'
                    else f'{part.period_completed}/{p.n_orders}'
                )
                text += f'Ваш прогресс: {progress}\n'
            text += '\n'

    keyboard = kb.promotions_keyboard(promos, parts_by_promo)
    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=text,
            attachments=[keyboard],
            parse_mode=ParseMode.HTML,
        )
    except (AttributeError, Exception):
        await event.message.answer(text=text, attachments=[keyboard], parse_mode=ParseMode.HTML)


@router.message_callback(F.callback.payload.startswith('WorkerPromo:'))
async def worker_promo_action(event: MessageCallback):
    """Присоединиться к акции или посмотреть прогресс"""
    promo_id = int(event.callback.payload.split(':')[1])
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        return
    promo = await db.get_promotion_by_id(promo_id)
    if not promo or not promo.is_active:
        await event.message.answer(text='Акция недоступна.', parse_mode=ParseMode.HTML)
        return
    existing = await db.get_active_participation(worker_id=worker.id, promotion_id=promo_id)
    if existing:
        if promo.type == 'streak':
            progress = f'{existing.current_streak}/{promo.n_orders} 🔥'
        else:
            progress = f'{existing.period_completed}/{promo.n_orders}'
        await event.message.answer(
            text=f'✅ Вы участвуете: {progress}\nЦиклов завершено: {existing.cycles_completed}',
            parse_mode=ParseMode.HTML,
        )
    else:
        await db.join_promotion(worker_id=worker.id, promotion_id=promo_id)
        await event.message.answer(
            text=f'✅ Вы приняли участие в акции «{promo.name}»!',
            parse_mode=ParseMode.HTML,
        )
    await _show_promotions(event, worker)


@router.message_callback(F.callback.payload == 'WorkerCancelAllPromos')
async def cancel_all_promos(event: MessageCallback):
    """Отказаться от всех акций"""
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        return
    await db.cancel_all_participations(worker_id=worker.id)
    await event.message.answer(text='Вы отказались от участия во всех акциях.', parse_mode=ParseMode.HTML)
    await _show_promotions(event, worker)


# ==================== ПОДТВЕРЖДЕНИЕ / ОТМЕНА ВЫПЛАТЫ ====================

@router.message_callback(F.callback.payload.startswith('WorkConfirmPayment:'))
async def worker_confirm_payment(event: MessageCallback, context: MemoryContext):
    """Запрос пин-кода (4 последних цифры ИНН) для подтверждения выплаты"""
    import logging as _logging
    order_id = int(event.callback.payload.split(':')[1])
    await event.message.answer(text=txt.request_worker_pin_code(), parse_mode=ParseMode.HTML)
    await context.update_data(OrderIDForPayment=order_id)
    await context.set_state(ProfileStates.payment_pin_confirm)
    _logging.info(f'[max][payment-confirm] user={event.from_user.user_id} order={order_id} запросил подтверждение')


@router.message_callback(F.callback.payload.startswith('WorkCancelPayment:'))
async def worker_cancel_payment(event: MessageCallback):
    """Перевод выплаты на кошелёк (отказ от карточной выплаты)"""
    import logging as _logging
    order_id = int(event.callback.payload.split(':')[1])
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        return
    result = await db.update_worker_balance_by_tg_id_op(tg_id=worker.tg_id, order_id=order_id)
    if result['success']:
        if result['payment_error']:
            await event.message.answer(text=result['reason'], parse_mode=ParseMode.HTML)
            _logging.warning(f'[max][payment-cancel] user={event.from_user.user_id} order={order_id} ошибка: {result["reason"]}')
        else:
            await event.message.answer(text=txt.payment_sent_to_balance(), parse_mode=ParseMode.HTML)
            _logging.info(f'[max][payment-cancel] user={event.from_user.user_id} order={order_id} переведено на кошелёк')
    else:
        await event.message.answer(text=txt.update_worker_balance_error(), parse_mode=ParseMode.HTML)
        _logging.warning(f'[max][payment-cancel] user={event.from_user.user_id} order={order_id} неизвестная ошибка')


@router.message_created(ProfileStates.payment_pin_confirm, F.message.body.text)
async def payment_pin_confirm(event: MessageCreated, context: MemoryContext):
    """Проверка пин-кода и установка подтверждения выплаты"""
    import logging as _logging
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await context.clear()
        return
    data = await context.get_data()
    order_id = data.get('OrderIDForPayment')
    if not order_id:
        await context.clear()
        return
    if worker.inn and worker.inn[-4:] == event.message.body.text.strip():
        await context.set_state(None)
        try:
            await db.payment_set_notification_confirmed(
                order_id=order_id,
                worker_id=worker.id,
            )
            await event.message.answer(text=txt.wait_payment(), parse_mode=ParseMode.HTML)
            _logging.info(f'[max][payment-confirm] user={event.from_user.user_id} order={order_id} верный пин')
        except Exception as e:
            _logging.exception(f'[max][payment-confirm] ошибка: {e}')
            await event.message.answer(text=txt.update_worker_balance_error(), parse_mode=ParseMode.HTML)
    else:
        await event.message.answer(text=txt.contract_inn_error(), parse_mode=ParseMode.HTML)
        _logging.info(f'[max][payment-confirm] user={event.from_user.user_id} order={order_id} неверный пин')
    await context.clear()
