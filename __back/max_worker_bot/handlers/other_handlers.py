"""
Прочие обработчики для Max бота
Включает: помощь, поддержка, заявка для друга
Адаптировано из Telegram бота
"""
from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback, Command
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from max_worker_bot.keyboards import worker_keyboards as kb
from max_worker_bot.states import OrderForFriendStates, HelpStates
from utils.max_delivery import remember_dialog_from_event
import database as db
import texts.worker as txt


router = Router()


# ==================== ПОМОЩЬ / ПОДДЕРЖКА ====================

async def confirmation_send_help_message(event, context: MemoryContext):
    """Показать подтверждение отправки обращения"""
    remember_dialog_from_event(event)

    data = await context.get_data()

    # Показываем текст обращения
    message_text = f"<b>💬 Обращение:</b>\n{data['HelpText']}"

    # Добавляем информацию о приложенных файлах
    total_files = len(data.get('HelpPhotos', [])) + len(data.get('HelpFiles', []))
    if total_files > 0:
        file_info = []
        if data.get('HelpPhotos'):
            file_info.append(f"📷 Фото: {len(data['HelpPhotos'])}")
        if data.get('HelpFiles'):
            file_info.append(f"📎 Файлов: {len(data['HelpFiles'])}")
        message_text += "\n\n<b>Прикреплено:</b>\n" + "\n".join(file_info)

    await event.message.answer(
        text=message_text,
        parse_mode=ParseMode.HTML
    )

    # Спрашиваем подтверждение
    await event.message.answer(
        text=txt.confirmation_send_help_message(),
        attachments=[kb.confirmation_send_help_message()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(None)


async def send_help_message_to_group(event, context: MemoryContext, worker_max_id: int):
    """Отправить обращение в группу поддержки (Telegram) с файлами"""
    remember_dialog_from_event(event)

    try:
        from aiogram import Bot as TelegramBot
        from aiogram.types import BufferedInputFile
        from config_reader import config
        from utils import get_rating

        settings = await db.get_settings()
        data = await context.get_data()

        # Получаем работника через max_id
        worker = await db.get_worker_by_max_id(max_id=worker_max_id)

        if not worker:
            raise Exception("Worker not found")

        # Получаем реальные данные работника по ID
        real_data = await db.get_user_real_data_by_id(user_id=worker.id)

        user_rating = await db.get_user_rating(user_id=worker.id)
        if not user_rating:
            await db.set_rating(user_id=worker.id)
            user_rating = await db.get_user_rating(user_id=worker.id)

        rating = await get_rating(user_id=worker.id)

        full_name = f'{real_data.last_name} {real_data.first_name}'
        if real_data.middle_name:
            full_name += f' {real_data.middle_name}'

        # Создаем Telegram бот для отправки в группу
        telegram_bot = TelegramBot(token=config.bot_token.get_secret_value())

        # Формируем текст обращения
        help_text = data['HelpText']

        # Отправляем текст обращения
        await telegram_bot.send_message(
            chat_id=settings.help_group_chat_id,
            text=txt.help_message_to_group(
                real_full_name=full_name,
                real_phone_number=real_data.phone_number,
                tg_id=worker.tg_id or 'нет',
                max_id=worker.max_id or 'нет',
                city=worker.city,
                total_orders=user_rating.total_orders,
                successful_orders=user_rating.successful_orders,
                rating=rating,
                help_text=help_text
            ),
            parse_mode="HTML"
        )

        # Скачиваем и отправляем фото из Max
        if data.get('HelpPhotos'):
            for i, max_file_id in enumerate(data['HelpPhotos']):
                try:
                    # Получаем информацию о файле из Max
                    file = await event.bot.get_file(max_file_id)
                    # Скачиваем файл
                    file_bytes = await event.bot.download_file(file.file_path)

                    # Создаем BufferedInputFile для Telegram
                    input_file = BufferedInputFile(file_bytes, filename=f"photo_{i+1}.jpg")

                    # Отправляем в Telegram с подписью только для первого фото
                    if i == 0:
                        await telegram_bot.send_photo(
                            chat_id=settings.help_group_chat_id,
                            photo=input_file,
                            caption=txt.help_message_caption(
                                full_name=full_name
                            )
                        )
                    else:
                        await telegram_bot.send_photo(
                            chat_id=settings.help_group_chat_id,
                            photo=input_file
                        )
                except Exception as e:
                    import logging
                    logging.warning(f"Не удалось передать фото {i+1}: {e}")

        # Скачиваем и отправляем файлы из Max
        if data.get('HelpFiles'):
            for i, max_file_id in enumerate(data['HelpFiles']):
                try:
                    # Получаем информацию о файле из Max
                    file = await event.bot.get_file(max_file_id)
                    # Скачиваем файл
                    file_bytes = await event.bot.download_file(file.file_path)

                    # Определяем имя файла (используем оригинальное или генерируем)
                    filename = file.file_path.split('/')[-1] if '/' in file.file_path else f"document_{i+1}"

                    # Создаем BufferedInputFile для Telegram
                    input_file = BufferedInputFile(file_bytes, filename=filename)

                    # Отправляем в Telegram с подписью только для первого файла
                    if i == 0 and not data.get('HelpPhotos'):
                        await telegram_bot.send_document(
                            chat_id=settings.help_group_chat_id,
                            document=input_file,
                            caption=txt.help_message_caption(
                                full_name=full_name
                            )
                        )
                    else:
                        await telegram_bot.send_document(
                            chat_id=settings.help_group_chat_id,
                            document=input_file
                        )
                except Exception as e:
                    import logging
                    logging.warning(f"Не удалось передать файл {i+1}: {e}")

        await telegram_bot.session.close()

        await event.message.answer(
            text=txt.help_message_sent(),
            parse_mode=ParseMode.HTML
        )

        await db.update_help_last_use(worker_id=worker.id)

    except Exception as e:
        import logging
        logging.exception(e)
        await event.message.answer(
            text=txt.send_help_message_error(),
            parse_mode=ParseMode.HTML
        )


@router.message_created(F.message.body.text == '🆘 СВЯЗЬ С РУКОВОДСТВОМ')
@router.message_callback(F.callback.payload == 'contact_support')
async def contact_support(event, context: MemoryContext):
    """Начать процесс отправки обращения в поддержку"""

    await context.clear()

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)

    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return

    can_use = await db.can_use_help(worker_id=worker.id)

    if can_use:
        await event.message.answer(
            text=txt.request_help_text(),
            parse_mode=ParseMode.HTML
        )
        await context.set_state(HelpStates.enter_text)
    else:
        await event.message.answer(
            text=txt.help_request_limit_reached(),
            parse_mode=ParseMode.HTML
        )


@router.message_created(HelpStates.enter_text, F.message.body.text)
async def get_help_text(event: MessageCreated, context: MemoryContext):
    """Получить текст обращения"""

    await event.message.answer(
        text=txt.request_help_files_or_photos(),
        attachments=[kb.help_skip()],
        parse_mode=ParseMode.HTML
    )

    await context.set_state(HelpStates.enter_files)
    await context.update_data(
        HelpText=event.message.body.text,
        HelpPhotos=[],
        HelpFiles=[]
    )


@router.message_created(HelpStates.enter_files, F.message.photo)
@router.message_created(HelpStates.enter_files, F.message.file)
async def get_help_files(event: MessageCreated, context: MemoryContext):
    """Получить фото или файл для обращения"""

    data = await context.get_data()
    help_photos = data.get('HelpPhotos', [])
    help_files = data.get('HelpFiles', [])

    total_files = len(help_files) + len(help_photos)

    # Проверяем лимит (максимум 3 файла)
    if total_files >= 3:
        await event.message.answer(
            text="❗ Достигнут лимит файлов (максимум 3). Нажмите 'Пропустить' для продолжения.",
            parse_mode=ParseMode.HTML
        )
        return

    if total_files == 2:
        # Это последний файл
        if event.message.photo:
            await event.message.answer(
                text=txt.help_photo_saved(request_more=False),
                parse_mode=ParseMode.HTML
            )
            help_photos.append(event.message.photo.file_id)
            await context.update_data(HelpPhotos=help_photos)
        else:
            await event.message.answer(
                text=txt.help_file_saved(request_more=False),
                parse_mode=ParseMode.HTML
            )
            help_files.append(event.message.file.file_id)
            await context.update_data(HelpFiles=help_files)

        # Показываем подтверждение
        await confirmation_send_help_message(event, context)
    else:
        # Еще можно добавить файлы
        if event.message.photo:
            await event.message.answer(
                text=txt.help_photo_saved(request_more=True),
                parse_mode=ParseMode.HTML
            )
            help_photos.append(event.message.photo.file_id)
            await context.update_data(HelpPhotos=help_photos)
        else:
            await event.message.answer(
                text=txt.help_file_saved(request_more=True),
                parse_mode=ParseMode.HTML
            )
            help_files.append(event.message.file.file_id)
            await context.update_data(HelpFiles=help_files)


@router.message_created(HelpStates.enter_files, F.message.body.text == 'Пропустить')
@router.message_callback(HelpStates.enter_files, F.callback.payload == 'skip_help_files')
async def get_help_files_skip(event, context: MemoryContext):
    """Пропустить загрузку файлов"""

    await confirmation_send_help_message(event, context)


@router.message_callback(F.callback.payload == 'SendHelpMessage')
async def send_help_message(event: MessageCallback, context: MemoryContext):
    """Отправить обращение в группу поддержки"""

    await event.message.answer(
        text=txt.sending_help_message(),
        parse_mode=ParseMode.HTML
    )

    await send_help_message_to_group(event, context, event.from_user.user_id)


@router.message_callback(F.callback.payload == 'CancelSendHelpMessage')
async def cancel_send_help_message(event: MessageCallback, context: MemoryContext):
    """Отменить отправку обращения"""

    await context.clear()
    await event.message.answer(
        text=txt.cancel_send_help_message(),
        parse_mode=ParseMode.HTML
    )


# ==================== ПРАВИЛА ====================

@router.message_created(Command('rules'))
async def show_rules(event: MessageCreated):
    """Показать правила платформы"""

    rules_text = (
        "<b>📋 Правила платформы</b>\n\n"
        "Полные правила доступны на нашем сайте:\n"
        "https://algoritmplus.online/rules\n\n"
        "<b>Основные положения:</b>\n\n"
        "1. Все услуги оказываются на основании гражданско-правового договора\n"
        "2. Исполнитель принимает заявки добровольно\n"
        "3. При отказе от заявки менее чем за 12 часов применяется неустойка 3000₽\n"
        "4. Рейтинг влияет на размер вознаграждения\n"
        "5. За неоказание услуг без уважительной причины возможна блокировка"
    )

    await event.message.answer(
        text=rules_text,
        attachments=[kb.back_to_menu_keyboard()],
        parse_mode=ParseMode.HTML
    )


# ==================== ЗАЯВКА ДЛЯ ДРУГА ====================

async def send_sms_to_worker_max(
        event,
        context: MemoryContext,
        phone_number: str,
        first_name: str,
        middle_name: str,
        last_name: str,
        message_to_edit=None
):
    """Отправка SMS с кодом подтверждения для заявки друга"""
    import secrets
    from utils import create_code_hash, schedule_delete_code_for_order, send_sms_with_api

    request_text = txt.request_code_for_order(
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name
    )

    if message_to_edit:
        try:
            await event.bot.edit_message(
                message_id=message_to_edit.message.body.mid,
                text=request_text,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await event.message.answer(text=request_text, parse_mode=ParseMode.HTML)
    else:
        await event.message.answer(text=request_text, parse_mode=ParseMode.HTML)

    # Генерация и отправка кода
    code = str(secrets.randbelow(900000) + 100000)
    code_hashed = create_code_hash(code=code)
    code_id = await db.set_code_for_order(
        code_hash=code_hashed['hash'],
        salt=code_hashed['salt']
    )
    await schedule_delete_code_for_order(code_id=code_id)
    await send_sms_with_api(
        phone_number=phone_number,
        message_text=txt.code_text_for_message(code=code),
        tg_id=event.from_user.user_id
    )
    await context.set_state(OrderForFriendStates.code_for_order)
    await context.update_data(
        CodeForOrderID=code_id,
        CodeForOrderAttempts=1
    )
    del code


@router.message_created(F.message.body.text == '💼 Заявка для друга')
@router.message_callback(F.callback.payload == 'order_for_friend')
async def order_for_friend(event, context: MemoryContext):
    """Начало процесса заявки для друга"""

    await context.clear()

    await event.message.answer(
        text=txt.order_for_friend_confirmation(),
        attachments=[kb.order_for_friend_confirmation()],
        parse_mode=ParseMode.HTML
    )


@router.message_callback(F.callback.payload == 'CancelOrderForFriend')
async def cancel_order_for_friend(event: MessageCallback, context: MemoryContext):
    """Отмена заявки для друга"""

    await context.clear()
    try:
        await event.message.delete()
    except:
        await event.message.answer(
            text="❌ Отменено",
            parse_mode=ParseMode.HTML
        )


@router.message_callback(F.callback.payload == 'ContinueOrderForFriend')
async def continue_order_for_friend(event: MessageCallback, context: MemoryContext):
    """Выбор метода поиска друга"""

    await event.message.answer(
        text=txt.choose_method_search_friend(),
        attachments=[kb.methods_search_friend()],
        parse_mode=ParseMode.HTML
    )


@router.message_callback(F.callback.payload == 'SearchWorkerByPhone')
async def search_worker_by_phone(event: MessageCallback, context: MemoryContext):
    """Начало поиска друга по номеру телефона"""

    await event.message.answer(
        text=txt.request_worker_phone_number(),
        parse_mode=ParseMode.HTML
    )
    await context.set_state(OrderForFriendStates.search_by_phone)


@router.message_created(OrderForFriendStates.search_by_phone, F.message.body.text)
async def get_worker_phone(event: MessageCreated, context: MemoryContext):
    """Обработка номера телефона друга"""
    from utils import normalize_phone_number

    phone_number = normalize_phone_number(event.message.body.text)

    if not phone_number:
        await event.message.answer(
            text=txt.phone_number_error(),
            parse_mode=ParseMode.HTML
        )
        return

    msg = await event.message.answer(
        text=txt.worker_search(),
        parse_mode=ParseMode.HTML
    )

    friend = await db.get_worker_by_phone_number(phone_number=phone_number)

    if friend:
        real_data = await db.get_user_real_data_by_id(user_id=friend.id)
        await context.update_data(
            FriendID=friend.id,
            FriendCity=friend.city
        )

        if await db.check_daily_code_attempts(phone_number=real_data.phone_number):
            try:
                await event.bot.edit_message(message_id=msg.message.body.mid,
                    text=txt.choose_friend_city(),
                    attachments=[await kb.cities_for_order_for_friend()],
                    parse_mode=ParseMode.HTML
                )
            except:
                await event.message.answer(
                    text=txt.choose_friend_city(),
                    attachments=[await kb.cities_for_order_for_friend()],
                    parse_mode=ParseMode.HTML
                )

            await context.set_state(None)
            await context.update_data(
                ChooseCityAction='RegWorker',
                FriendID=friend.id,
                PhoneNumber=real_data.phone_number,
                FirstName=real_data.first_name,
                MiddleName=real_data.middle_name,
                LastName=real_data.last_name
            )
        else:
            # Too many SMS attempts — clear state so user isn't stuck
            await context.set_state(None)
            try:
                await event.bot.edit_message(message_id=msg.message.body.mid,
                    text=txt.too_many_attempts_for_code(),
                    parse_mode=ParseMode.HTML
                )
            except:
                await event.message.answer(
                    text=txt.too_many_attempts_for_code(),
                    parse_mode=ParseMode.HTML
                )
    else:
        # Friend not found — clear state so user isn't stuck
        await context.set_state(None)
        try:
            await event.bot.edit_message(message_id=msg.message.body.mid,
                text=txt.order_for_friend_worker_not_found(),
                parse_mode=ParseMode.HTML
            )
        except:
            await event.message.answer(
                text=txt.order_for_friend_worker_not_found(),
                parse_mode=ParseMode.HTML
            )


@router.message_callback(F.callback.payload == 'SearchWorkerByInn')
async def search_worker_by_inn(event: MessageCallback, context: MemoryContext):
    """Начало поиска друга по ИНН"""

    await event.message.answer(
        text=txt.request_worker_inn(),
        parse_mode=ParseMode.HTML
    )
    await context.set_state(OrderForFriendStates.search_by_inn)


@router.message_created(OrderForFriendStates.search_by_inn, F.message.body.text)
async def get_worker_inn(event: MessageCreated, context: MemoryContext):
    """Обработка ИНН друга"""

    if not event.message.body.text.isdigit():
        await event.message.answer(
            text=txt.code_for_order_error(),
            parse_mode=ParseMode.HTML
        )
        return

    msg = await event.message.answer(
        text=txt.worker_search(),
        parse_mode=ParseMode.HTML
    )

    friend = await db.get_worker_by_inn(inn=event.message.body.text)

    if friend:
        real_data = await db.get_user_real_data_by_id(user_id=friend.id)
        await context.update_data(
            FriendID=friend.id,
            FriendCity=friend.city
        )

        if await db.check_daily_code_attempts(phone_number=real_data.phone_number):
            try:
                await event.bot.edit_message(message_id=msg.message.body.mid,
                    text=txt.choose_friend_city(),
                    attachments=[await kb.cities_for_order_for_friend()],
                    parse_mode=ParseMode.HTML
                )
            except:
                await event.message.answer(
                    text=txt.choose_friend_city(),
                    attachments=[await kb.cities_for_order_for_friend()],
                    parse_mode=ParseMode.HTML
                )

            await context.set_state(None)
            await context.update_data(
                ChooseCityAction='RegWorker',
                FriendID=friend.id,
                PhoneNumber=real_data.phone_number,
                FirstName=real_data.first_name,
                MiddleName=real_data.middle_name,
                LastName=real_data.last_name
            )
        else:
            # Too many SMS attempts — clear state so user isn't stuck
            await context.set_state(None)
            try:
                await event.bot.edit_message(message_id=msg.message.body.mid,
                    text=txt.too_many_attempts_for_code(),
                    parse_mode=ParseMode.HTML
                )
            except:
                await event.message.answer(
                    text=txt.too_many_attempts_for_code(),
                    parse_mode=ParseMode.HTML
                )
    else:
        # Friend not found — clear state so user isn't stuck
        await context.set_state(None)
        try:
            await event.bot.edit_message(message_id=msg.message.body.mid,
                text=txt.order_for_friend_worker_not_found(),
                parse_mode=ParseMode.HTML
            )
        except:
            await event.message.answer(
                text=txt.order_for_friend_worker_not_found(),
                parse_mode=ParseMode.HTML
            )


@router.message_callback(F.callback.payload.startswith('CityForFriend:'))
async def get_friend_city(event: MessageCallback, context: MemoryContext):
    """Выбор города для друга и отправка SMS"""

    data = await context.get_data()
    city = event.callback.payload.split(':')[1]

    if data.get('ChooseCityAction') == 'NewWorker':
        # Создание нового виртуального пользователя
        friend_id = await db.set_user(
            tg_id=0,
            username=None,
            phone_number=data['PhoneNumber'],
            city=city,
            first_name=data['FirstName'],
            middle_name=data['MiddleName'],
            last_name=data['LastName'],
            inn=data['INN'],
            real_phone_number=data['PhoneNumber'],
            real_first_name=data['FirstName'],
            real_middle_name=data['MiddleName'],
            real_last_name=data['LastName']
        )
        await context.update_data(
            FriendID=friend_id,
            FriendCity=city
        )
        await db.check_daily_code_attempts(phone_number=data['PhoneNumber'])

    else:
        await context.update_data(FriendCity=city)

    await send_sms_to_worker_max(
        event=event,
        context=context,
        phone_number=data['PhoneNumber'],
        first_name=data['FirstName'],
        middle_name=data['MiddleName'],
        last_name=data['LastName']
    )


@router.message_created(OrderForFriendStates.code_for_order, F.message.body.text)
async def code_for_order_check(event: MessageCreated, context: MemoryContext):
    """Проверка кода подтверждения из SMS"""
    from utils import check_code
    from max_worker_bot.handlers.search_orders_handlers import open_customer_search_menu

    if not event.message.body.text.isdigit():
        await event.message.answer(
            text=txt.code_for_order_error(),
            parse_mode=ParseMode.HTML
        )
        return

    data = await context.get_data()
    code_data = await db.get_code_for_order(code_id=data['CodeForOrderID'])

    if code_data:
        checking_code = check_code(
            salt=code_data.salt,
            hashed_code=code_data.code_hash,
            entered_code=event.message.body.text
        )

        if checking_code:
            # Код верный
            await db.delete_code_for_order(code_id=code_data.id)
            friend_id = data['FriendID']
            friend_city = data['FriendCity']
            await context.clear()
            await context.update_data(
                FriendID=friend_id,
                FriendCity=friend_city,
                SearchOrderFor='friend'
            )
            await open_customer_search_menu(event=event, context=context)
        else:
            # Код неверный
            if data['CodeForOrderAttempts'] >= 3:
                await db.delete_code_for_order(code_id=code_data.id)
                await event.message.answer(
                    text=txt.code_for_order_attempts_error(),
                    parse_mode=ParseMode.HTML
                )
                await context.clear()
            else:
                await event.message.answer(
                    text=txt.code_for_order_error(),
                    parse_mode=ParseMode.HTML
                )
                await context.update_data(
                    CodeForOrderAttempts=data['CodeForOrderAttempts'] + 1
                )
    else:
        await event.message.answer(
            text=txt.the_code_has_expired_error(),
            parse_mode=ParseMode.HTML
        )
        await context.clear()


# ==================== УВЕДОМЛЕНИЯ ====================

@router.message_callback(F.callback.payload == 'DismissNotification')
async def dismiss_notification(event: MessageCallback):
    """Закрыть уведомление"""

    try:
        await event.message.delete()
    except:
        await event.bot.edit_message(message_id=event.message.body.mid,text="✅ Уведомление закрыто", parse_mode=ParseMode.HTML)
