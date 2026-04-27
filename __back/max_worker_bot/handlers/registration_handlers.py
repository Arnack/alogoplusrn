"""
Обработчики регистрации исполнителя для Max бота
Адаптировано из Telegram бота
"""
import re
import secrets
from maxapi import Router, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode
from maxapi.enums.attachment import AttachmentType

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from max_worker_bot.states import RegistrationStates
from max_worker_bot.keyboards import worker_keyboards as kb
from utils import (
    normalize_phone_number,
    create_code_hash,
    check_code,
    schedule_delete_verification_code,
    schedule_delete_registration_code,
    send_sms_with_api,
    luhn_check,
)
import database as db
import texts.worker as txt
from API.fin.workers import (
    fin_get_worker_by_phone,
    fin_get_worker_by_inn,
    fin_get_worker_by_card,
    fin_create_worker,
    fin_check_fns_status,
    fin_get_worker_full_name,
    fin_patch_worker_profile,
)
from API import (
    create_all_contracts_for_worker,
    sign_all_worker_contracts,
)
from utils.contract_pin import choose_pin, verify_pin
from utils.max_delivery import send_max_message, remember_dialog_from_event

router = Router()


# ==================== КОМАНДА /START ====================

@router.message_created(Command('start'))
async def cmd_start(event: MessageCreated, context: MemoryContext):
    """Обработка команды /start - начало регистрации"""
    remember_dialog_from_event(event)

    user_id = event.from_user.user_id

    # Сбрасываем старое состояние (важно после перезапуска бота)
    await context.clear()

    # Проверяем, есть ли уже зарегистрированный работник
    worker = await db.get_worker_by_max_id(max_id=user_id)

    if worker:
        # Если работник уже зарегистрирован, показываем главное меню
        is_foreman = await db.is_foreman(worker_id=worker.id)

        if is_foreman:
            await event.message.answer(
                text=txt.rejoin_worker(),
                attachments=[kb.foreman_main_menu()],
            parse_mode=ParseMode.HTML
    )
        else:
            await event.message.answer(
                text=txt.rejoin_worker(),
                attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML
    )
    else:
        await event.message.answer(
            text=txt.cmd_start_user(),
            attachments=[kb.entry_choice_max()],
            parse_mode=ParseMode.HTML
        )


# ==================== ВЫБОР: ВОЙТИ / РЕГИСТРАЦИЯ ====================

@router.message_callback(F.callback.payload == 'EntryLoginMax')
async def entry_login_max(event: MessageCallback, context: MemoryContext):
    """Нажал «Войти» — запрашиваем город"""
    remember_dialog_from_event(event)
    await context.clear()
    await context.update_data(flow='login')
    await event.message.answer(
        text=txt.request_worker_city(),
        attachments=[await kb.cities_keyboard()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.request_city)


@router.message_callback(F.callback.payload == 'EntryRegisterMax')
async def entry_register_max(event: MessageCallback, context: MemoryContext):
    """Нажал «Регистрация» — спрашиваем, является ли самозанятым"""
    remember_dialog_from_event(event)
    await context.clear()
    await event.message.answer(
        text='❓ Вы являетесь самозанятым?',
        attachments=[kb.are_you_self_employed_max()],
        parse_mode=ParseMode.HTML
    )


@router.message_callback(F.callback.payload == 'RegYesSMZMax')
async def reg_yes_smz_max(event: MessageCallback, context: MemoryContext):
    """«Да» — переходим к выбору города"""
    remember_dialog_from_event(event)
    await context.update_data(flow='register')
    await event.message.answer(
        text=txt.request_worker_city(),
        attachments=[await kb.cities_keyboard()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.request_city)


@router.message_callback(F.callback.payload == 'RegNoSMZMax')
async def reg_no_smz_max(event: MessageCallback, context: MemoryContext):
    """«Нет» — показываем картинку-инструкцию как стать самозанятым"""
    remember_dialog_from_event(event)
    import os
    import logging
    from maxapi.enums.upload_type import UploadType
    from max_worker_bot.upload_utils import upload_buffer

    smz_pic_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'Как стать Самозанятым.jpeg',
    )
    if os.path.exists(smz_pic_path):
        try:
            with open(smz_pic_path, 'rb') as f:
                pic_data = f.read()
            attachment = await upload_buffer(
                bot=event.bot,
                buffer=pic_data,
                upload_type=UploadType.IMAGE,
                filename='smz_instruction',
            )
            if attachment:
                await event.message.answer(
                    text=txt.smz_instruction_text(),
                    attachments=[attachment, kb.became_self_employed_max()],
                    parse_mode=ParseMode.HTML,
                )
                return
        except Exception as e:
            logging.exception(f'[max] reg_no_smz_max: {e}')
    await event.message.answer(
        text=txt.smz_instruction_text(),
        attachments=[kb.became_self_employed_max()],
        parse_mode=ParseMode.HTML,
    )


@router.message_callback(F.callback.payload == 'RegBecameSMZMax')
async def reg_became_smz_max(event: MessageCallback, context: MemoryContext):
    """«Я стал самозанятым» — переходим к выбору города"""
    remember_dialog_from_event(event)
    await context.update_data(flow='register')
    await event.message.answer(
        text=txt.request_worker_city(),
        attachments=[await kb.cities_keyboard()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.request_city)


# ==================== ВЫБОР ГОРОДА ====================

@router.message_callback(RegistrationStates.request_city)
async def get_city(event: MessageCallback, context: MemoryContext):
    """Обработка выбора города"""
    remember_dialog_from_event(event)

    if event.callback.payload.startswith('RegCity:'):
        city = event.callback.payload.split(':')[1]
        await context.update_data(city=city)

        ctx_data = await context.get_data()
        pending_phone = ctx_data.get('pending_phone')

        if pending_phone:
            # Пользователь уже вводил телефон — привязываем аккаунт сразу
            worker = await db.get_worker_by_phone_number(phone_number=pending_phone)

            if worker and not worker.max_id:
                await db.update_worker_max_id(
                    worker_id=worker.id,
                    max_id=event.from_user.user_id,
                    max_chat_id=event.message.recipient.chat_id,
                )
                await db.update_user_city(worker_id=worker.id, city=city)

                is_foreman = await db.is_foreman(worker_id=worker.id)
                if is_foreman:
                    await event.message.answer(
                        text=txt.rejoin_worker(),
                        attachments=[kb.foreman_main_menu()],
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await event.message.answer(
                        text=txt.rejoin_worker(),
                        attachments=[kb.user_main_menu()],
                        parse_mode=ParseMode.HTML
                    )
            else:
                await event.message.answer(
                    text='⚠️ Ошибка привязки аккаунта. Отправьте /start и попробуйте снова.',
                    parse_mode=ParseMode.HTML
                )
            await context.clear()
        else:
            ctx_data = await context.get_data()
            flow = ctx_data.get('flow', 'login')
            if flow == 'register':
                await event.message.answer(
                    text='Введите вашу фамилию:',
                    parse_mode=ParseMode.HTML
                )
                await context.set_state(RegistrationStates.reg_last_name)
            else:
                await event.message.answer(
                    text=txt.request_phone_number(),
                    parse_mode=ParseMode.HTML
                )
                await context.set_state(RegistrationStates.request_phone_number)


# ==================== ВХОД: ВВОД НОМЕРА ТЕЛЕФОНА ====================

@router.message_created(RegistrationStates.request_phone_number, F.message.body.text)
async def get_phone_number(event: MessageCreated, context: MemoryContext):
    """Обработка ввода номера телефона (только флоу входа)"""
    remember_dialog_from_event(event)

    phone_number = normalize_phone_number(event.message.body.text)
    data = await context.get_data()

    if not phone_number:
        await event.message.answer(text=txt.phone_number_error(), parse_mode=ParseMode.HTML)
        return

    worker = await db.get_worker_by_phone_number(phone_number=phone_number)

    if worker:
        if not worker.max_id:
            # max_id не привязан — требуем верификацию через Telegram-аккаунт
            if worker.tg_id:
                code = str(secrets.randbelow(900000) + 100000)
                code_hashed = create_code_hash(code=code)
                code_id = await db.set_verification_code(
                    worker_id=worker.id,
                    tg_id=worker.tg_id,
                    code_hash=code_hashed['hash'],
                    salt=code_hashed['salt'],
                )
                await schedule_delete_verification_code(code_id=code_id)
                try:
                    from aiogram import Bot as TgBot
                    from max_worker_bot.config_reader import config as _cfg
                    _tg_bot = TgBot(token=_cfg.bot_token.get_secret_value())
                    await _tg_bot.send_message(
                        chat_id=worker.tg_id,
                        text=txt.verification_code(code=code),
                        parse_mode='HTML',
                    )
                    await _tg_bot.session.close()
                except Exception:
                    pass
                del code
                await event.message.answer(text=txt.request_verification_code(), parse_mode=ParseMode.HTML)
                await context.update_data(CodeID=code_id, PendingMaxId=event.from_user.user_id, PendingCity=data.get('city', ''))
                await context.set_state(RegistrationStates.verification_code)
            else:
                # tg_id тоже не привязан (администратор стёр) — разрешаем прямой вход
                await db.update_worker_max_id(
                    worker_id=worker.id,
                    max_id=event.from_user.user_id,
                    max_chat_id=event.message.recipient.chat_id,
                )
                city = data.get('city')
                if city:
                    await db.update_user_city(worker_id=worker.id, city=city)
                is_foreman = await db.is_foreman(worker_id=worker.id)
                await event.message.answer(
                    text=txt.rejoin_worker(),
                    attachments=[kb.foreman_main_menu() if is_foreman else kb.user_main_menu()],
                    parse_mode=ParseMode.HTML
                )
                await context.clear()
        else:
            code = str(secrets.randbelow(900000) + 100000)
            code_hashed = create_code_hash(code=code)
            code_id = await db.set_verification_code_max(
                worker_id=worker.id,
                max_id=worker.max_id,
                code_hash=code_hashed['hash'],
                salt=code_hashed['salt']
            )
            await schedule_delete_verification_code(code_id=code_id)
            try:
                await send_max_message(
                    event.bot,
                    user_id=worker.max_id,
                    text=txt.verification_code(code=code),
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
            del code
            await event.message.answer(text=txt.request_verification_code(), parse_mode=ParseMode.HTML)
            await context.update_data(CodeID=code_id)
            await context.set_state(RegistrationStates.verification_code)
    else:
        # Не найден в локальной БД — ищем в fin API
        fin_phone = phone_number.lstrip('+').lstrip('7')
        fin_worker = await fin_get_worker_by_phone(fin_phone)
        if fin_worker:
            city = data.get('city', '')
            worker_id = fin_worker.get('id')
            user_id = await db.set_user(
                max_id=event.from_user.user_id,
                max_chat_id=event.message.recipient.chat_id,
                username=event.from_user.username,
                phone_number=phone_number,
                city=city,
                real_phone_number=phone_number,
                first_name=fin_worker.get('firstName', ''),
                last_name=fin_worker.get('lastName', ''),
                middle_name=fin_worker.get('patronymic', ''),
                real_first_name=fin_worker.get('firstName', ''),
                real_last_name=fin_worker.get('lastName', ''),
                real_middle_name=fin_worker.get('patronymic', ''),
                inn=str(fin_worker.get('inn', '')),
                api_worker_id=worker_id,
                card=fin_worker.get('bankcardNumber') or '',
            )
            is_foreman = await db.is_foreman(worker_id=user_id) if user_id else False
            await event.message.answer(
                text=txt.rejoin_worker(),
                attachments=[kb.foreman_main_menu() if is_foreman else kb.user_main_menu()],
                parse_mode=ParseMode.HTML
            )
            await context.clear()
        else:
            await event.message.answer(
                text=(
                    '❗ Номер не найден\n\n'
                    'Ваш номер отсутствует в базе партнёра ООО «Рабочие Руки» или введён с ошибкой\n\n'
                    '📱 Проверьте номер и попробуйте ещё раз\n\n'
                    '🚀 Ещё не зарегистрированы?\n'
                    '➡️ Отправьте /start и выберите «Регистрация»'
                ),
                parse_mode=ParseMode.HTML
            )
            await context.clear()


# ==================== РЕГИСТРАЦИЯ: ФОРМА ДАННЫХ ====================

@router.message_created(RegistrationStates.reg_last_name, F.message.body.text)
async def reg_get_last_name(event: MessageCreated, context: MemoryContext):
    value = event.message.body.text.strip()
    if len(value) < 2:
        await event.message.answer(text='❗ Введите корректную фамилию.', parse_mode=ParseMode.HTML)
        return
    await context.update_data(RegLastName=value, RealLastName=value)
    await event.message.answer(text='Введите ваше имя:', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.reg_first_name)


@router.message_created(RegistrationStates.reg_first_name, F.message.body.text)
async def reg_get_first_name(event: MessageCreated, context: MemoryContext):
    value = event.message.body.text.strip()
    if len(value) < 2:
        await event.message.answer(text='❗ Введите корректное имя.', parse_mode=ParseMode.HTML)
        return
    await context.update_data(RegFirstName=value, RealFirstName=value)
    await event.message.answer(
        text='Введите ваше отчество (или нажмите кнопку если его нет):',
        attachments=[kb.skip_patronymic_max()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.reg_middle_name)


@router.message_callback(F.callback.payload == 'RegSkipPatronymicMax', RegistrationStates.reg_middle_name)
async def reg_skip_middle_name(event: MessageCallback, context: MemoryContext):
    await context.update_data(RegMiddleName='', RealMiddleName='')
    await event.message.answer(text='🔢 Введите ваш ИНН (12 цифр):', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.reg_inn)


@router.message_created(RegistrationStates.reg_middle_name, F.message.body.text)
async def reg_get_middle_name(event: MessageCreated, context: MemoryContext):
    value = event.message.body.text.strip()
    await context.update_data(RegMiddleName=value, RealMiddleName=value)
    await event.message.answer(text='🔢 Введите ваш ИНН (12 цифр):', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.reg_inn)


@router.message_created(RegistrationStates.reg_inn, F.message.body.text)
async def reg_get_inn(event: MessageCreated, context: MemoryContext):
    value = event.message.body.text.strip()
    if not (value.isdigit() and len(value) == 12):
        await event.message.answer(text=txt.registration_inn_error(), parse_mode=ParseMode.HTML)
        return
    local_worker = await db.get_worker_by_inn(inn=value)
    if local_worker:
        # Аккаунт уже существует — вход по ИНН при регистрации недопустим
        await event.message.answer(
            text=(
                '❗ Аккаунт с таким ИНН уже существует.\n\n'
                'Для входа используйте кнопку <b>«Войти»</b> и введите ваш номер телефона.\n\n'
                'Если вы потеряли доступ к прежнему аккаунту — воспользуйтесь кнопкой '
                '<b>«Закрыть другие сессии»</b> или обратитесь к администратору.'
            ),
            parse_mode=ParseMode.HTML,
        )
        await context.clear()
        return
    rr_worker = await fin_get_worker_by_inn(inn=value)
    if rr_worker:
        await event.message.answer(text=txt.reg_error_inn_rr_exists(), parse_mode=ParseMode.HTML)
        await context.clear()
        return
    await context.update_data(RegINN=value)
    await event.message.answer(text=txt.request_card(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.reg_card)


@router.message_created(RegistrationStates.reg_card, F.message.body.text)
async def reg_get_card(event: MessageCreated, context: MemoryContext):
    card = event.message.body.text.strip().replace(' ', '')
    if not card.isdigit():
        await event.message.answer(text=txt.card_number_error(), parse_mode=ParseMode.HTML)
        return
    if not luhn_check(card):
        await event.message.answer(text=txt.luhn_check_error(), parse_mode=ParseMode.HTML)
        return
    if await db.card_unique(card):
        await event.message.answer(text=txt.card_not_unique_error(), parse_mode=ParseMode.HTML)
        return
    if await fin_get_worker_by_card(card):
        await event.message.answer(text=txt.card_not_unique_error(), parse_mode=ParseMode.HTML)
        return
    await context.update_data(RegCard=card)
    await event.message.answer(
        text='📱 Введите ваш номер телефона (например: +79031234567):',
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.reg_phone)


@router.message_created(RegistrationStates.reg_phone, F.message.body.text)
async def reg_get_phone(event: MessageCreated, context: MemoryContext):
    phone_number = normalize_phone_number(event.message.body.text)
    if not phone_number:
        await event.message.answer(text=txt.phone_number_error(), parse_mode=ParseMode.HTML)
        return
    if await db.get_worker_by_phone_number(phone_number=phone_number):
        await event.message.answer(text=txt.reg_error_phone_exists(), parse_mode=ParseMode.HTML)
        return
    if await fin_get_worker_by_phone(phone_number.lstrip('+').lstrip('7')):
        await event.message.answer(text=txt.reg_error_phone_exists(), parse_mode=ParseMode.HTML)
        return
    can_send = await db.check_daily_code_attempts(phone_number=phone_number)
    if not can_send:
        await event.message.answer(
            text='⚠️ Превышен лимит SMS. Попробуйте через 24 часа.',
            parse_mode=ParseMode.HTML
        )
        return
    code = str(secrets.randbelow(900000) + 100000)
    code_hashed = create_code_hash(code=code)
    code_id = await db.set_registration_code(
        code_hash=code_hashed['hash'],
        salt=code_hashed['salt'],
    )
    await schedule_delete_registration_code(code_id=code_id)
    await context.update_data(RegPhoneNumber=phone_number, RegCodeID=code_id)
    await context.set_state(RegistrationStates.registration_code)
    await event.message.answer(text=txt.request_registration_code(), parse_mode=ParseMode.HTML)
    await send_sms_with_api(
        phone_number=phone_number,
        message_text=txt.send_registration_message(code=code),
        tg_id=event.from_user.user_id,
    )
    del code




# ==================== ВВОД КОДА ВЕРИФИКАЦИИ ====================

@router.message_created(RegistrationStates.verification_code, F.message.body.text)
async def get_verification_code(event: MessageCreated, context: MemoryContext):
    """Обработка ввода кода верификации"""
    remember_dialog_from_event(event)

    if not event.message.body.text.isdigit():
        await event.message.answer(text="❗ Код должен содержать только цифры", parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    code_data = await db.get_code_by_id(code_id=data['CodeID'])

    if not code_data:
        await event.message.answer(text=txt.no_verification_code_error(), parse_mode=ParseMode.HTML)
        await context.clear()
        return

    checking_code = check_code(
        salt=code_data.salt,
        hashed_code=code_data.code_hash,
        entered_code=event.message.body.text
    )

    if checking_code:
        # Код верный - обновляем Max ID работника
        old_worker = await db.get_user_by_id(user_id=code_data.worker_id)
        await db.update_worker_max_id(
            worker_id=code_data.worker_id,
            max_id=event.from_user.user_id,
            max_chat_id=event.message.recipient.chat_id,
        )
        await db.delete_verification_code(code_id=code_data.id)

        # Сохраняем город, выбранный при входе
        city = data.get('city')
        if city:
            await db.update_user_city(worker_id=code_data.worker_id, city=city)

        is_foreman = await db.is_foreman(worker_id=code_data.worker_id)

        if is_foreman:
            await event.message.answer(
                text=txt.verification_completed(),
                attachments=[kb.foreman_main_menu()],
                parse_mode=ParseMode.HTML
            )
        else:
            await event.message.answer(
                text=txt.verification_completed(),
                attachments=[kb.user_main_menu()],
                parse_mode=ParseMode.HTML
            )

        # Уведомляем старый аккаунт
        try:
            await send_max_message(
                event.bot,
                user_id=old_worker.max_id,
                text=txt.account_notification(),
                parse_mode=ParseMode.HTML
            )
        except:
            pass

        await context.clear()
    else:
        await event.message.answer(text=txt.verification_code_error(), parse_mode=ParseMode.HTML)


# ==================== ПРОВЕРКА СТАТУСА РЕГИСТРАЦИИ ====================

@router.message_callback(F.callback.payload.startswith('CheckRegistration:'))
async def check_registration(event: MessageCallback, context: MemoryContext):
    """Проверка статуса регистрации через fin API"""

    phone_number = event.callback.payload.split(':')[1]
    fin_phone = phone_number.lstrip('+').lstrip('7')
    fin_worker = await fin_get_worker_by_phone(fin_phone)

    if not fin_worker:
        await event.message.answer(text=txt.try_register_again(), parse_mode=ParseMode.HTML)
        return

    worker_id = fin_worker.get('id')
    _, is_smz = await fin_check_fns_status(worker_id) if worker_id else (False, False)

    if not is_smz:
        await event.message.answer(text=txt.try_register_again(), parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    first_name = fin_worker.get('firstName', '')
    last_name = fin_worker.get('lastName', '')
    middle_name = fin_worker.get('patronymic', '')
    inn = str(fin_worker.get('inn', ''))

    await event.bot.edit_message(
        message_id=event.message.body.mid,
        text=txt.callback_save_data_for_security(
            phone_number=phone_number,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
        ),
        attachments=[kb.accept_save_data_for_security()],
        parse_mode=ParseMode.HTML
    )
    await context.update_data(
        reg_phone_number=phone_number,
        reg_first_name=first_name,
        reg_last_name=last_name,
        reg_middle_name=middle_name,
        reg_max_id=event.from_user.user_id,
        reg_username=event.from_user.username,
        reg_api_phone_number=phone_number,
        reg_city=data.get('city', ''),
        api_first_name=first_name,
        api_middle_name=middle_name,
        api_last_name=last_name,
        inn=inn,
        api_worker_id=worker_id,
        fin_card=fin_worker.get('bankcardNumber') or '',
        action='new',
    )


# ==================== СОХРАНЕНИЕ ДАННЫХ ====================

@router.message_callback(F.callback.payload == 'SaveDataForSecurity')
async def save_data_for_security(event: MessageCallback, context: MemoryContext):
    """Сохранение данных для охраны и завершение регистрации"""

    data = await context.get_data()

    if data.get('action') == 'new':
        # Новая регистрация
        required_keys = [
            'reg_username', 'reg_api_phone_number', 'reg_city', 'reg_phone_number',
            'reg_first_name', 'reg_last_name', 'reg_middle_name', 'api_first_name',
            'api_middle_name', 'api_last_name', 'inn'
        ]

        if all(key in data for key in required_keys):
            # Если паспортные данные ещё не собраны — запускаем опросник
            if not data.get('birthday'):
                await event.message.answer(
                    text=txt.request_birth_date(),
                    parse_mode=ParseMode.HTML
                )
                await context.set_state(RegistrationStates.birthday)
                return

            api_worker_id = data.get('api_worker_id', 0)
            # Патчим fin API с реальными данными (ФИО, дата рождения, паспорт)
            import logging as _logging
            patched = await fin_patch_worker_profile(
                worker_id=api_worker_id,
                first_name=data.get('reg_first_name'),
                last_name=data.get('reg_last_name'),
                patronymic=data.get('reg_middle_name'),
                birthday=data.get('birthday'),
                passport_series=data.get('passport_series'),
                passport_number=data.get('passport_number'),
                passport_issue_date=data.get('passport_date'),
            )
            _logging.info(f'[max][reg] PATCH profile worker={api_worker_id}: {patched}')
            await _show_max_contract(event, context, api_worker_id)
        else:
            await event.message.answer(
                text="Ошибка: отсутствуют данные регистрации. Начните процесс заново с /start",
                parse_mode=ParseMode.HTML
            )
    else:
        # Обновление данных
        required_keys = ['reg_phone_number', 'reg_first_name', 'reg_last_name', 'reg_middle_name']

        if all(key in data for key in required_keys):
            await db.update_data_for_security_max(
                max_id=event.from_user.user_id,
                phone_number=data['reg_phone_number'],
                first_name=data['reg_first_name'],
                last_name=data['reg_last_name'],
                middle_name=data['reg_middle_name']
            )

            await event.message.answer(text=txt.update_data_for_security(), parse_mode=ParseMode.HTML)
            await context.clear()
        else:
            await event.message.answer(
                text="Ошибка: данные не найдены. Начните процесс заново",
                parse_mode=ParseMode.HTML
            )


# ==================== ОБНОВЛЕНИЕ ДАННЫХ ====================

@router.message_callback(F.callback.payload.in_(['UpdateFullNameForSecurity', 'NewDataForSecurity']))
async def update_data_for_security(event: MessageCallback, context: MemoryContext):
    """Начало процесса обновления данных для охраны"""

    action = 'update' if event.callback.payload == 'UpdateFullNameForSecurity' else 'new'
    await context.update_data(action=action)

    if action == 'new':
        # Телефон уже есть в контексте из шага ввода номера — пропускаем его повторный запрос
        await event.message.answer(
            text=txt.last_name_for_security(),
            parse_mode=ParseMode.HTML
        )
        await context.set_state(RegistrationStates.last_name_for_security)
    else:
        await event.message.answer(
            text=txt.phone_for_security(),
            attachments=[kb.request_phone_number_keyboard()],
            parse_mode=ParseMode.HTML
        )
        await context.set_state(RegistrationStates.phone_number_for_security)


@router.message_created(RegistrationStates.phone_number_for_security)
async def save_contact(event: MessageCreated, context: MemoryContext):
    """Сохранение контакта (номера телефона)"""

    phone = None

    # Пробуем извлечь из контактного вложения
    if event.message.body and event.message.body.attachments:
        for attachment in event.message.body.attachments:
            if attachment.type == AttachmentType.CONTACT and attachment.payload:
                vcf_info = attachment.payload.vcf_info or ""
                phone_match = re.search(r'TEL[^:\n]*:(\+?\d+)', vcf_info)
                if phone_match:
                    phone = phone_match.group(1)
                    if not phone.startswith('+'):
                        phone = '+' + phone
                break

    # Если контакт не дал телефон — пробуем текст сообщения
    if not phone and event.message.body and event.message.body.text:
        phone = normalize_phone_number(event.message.body.text)

    if not phone:
        await event.message.answer(
            text=txt.phone_number_error(),
            parse_mode=ParseMode.HTML
        )
        return

    await context.update_data(reg_phone_number=phone)
    await event.message.answer(text=txt.last_name_for_security(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.last_name_for_security)


@router.message_created(RegistrationStates.last_name_for_security, F.message.body.text)
async def save_last_name(event: MessageCreated, context: MemoryContext):
    """Сохранение фамилии"""

    await context.update_data(reg_last_name=event.message.body.text.capitalize())
    await event.message.answer(text=txt.first_name_for_security(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.first_name_for_security)


@router.message_created(RegistrationStates.first_name_for_security, F.message.body.text)
async def save_first_name(event: MessageCreated, context: MemoryContext):
    """Сохранение имени"""

    await context.update_data(reg_first_name=event.message.body.text.capitalize())
    await event.message.answer(
        text=txt.middle_name_for_security(),
        attachments=[kb.skip_patronymic_max()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.middle_name_for_security)


@router.message_callback(F.callback.payload == 'RegSkipPatronymicMax', RegistrationStates.middle_name_for_security)
async def skip_middle_name_max(event: MessageCallback, context: MemoryContext):
    """Пропуск отчества"""
    await context.update_data(reg_middle_name='')
    await event.message.answer(text=txt.request_birth_date(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.birthday)


@router.message_created(RegistrationStates.middle_name_for_security, F.message.body.text)
async def save_middle_name(event: MessageCreated, context: MemoryContext):
    """Сохранение отчества — переход к вводу даты рождения"""

    await context.update_data(reg_middle_name=event.message.body.text.capitalize())
    await event.message.answer(
        text=txt.request_birth_date(),
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.birthday)


@router.message_created(RegistrationStates.birthday, F.message.body.text)
async def save_birthday(event: MessageCreated, context: MemoryContext):
    """Сохранение даты рождения — переход к выбору пола"""
    from utils.validators.passport import validate_passport_issue_date
    value = event.message.body.text.strip()
    if not validate_passport_issue_date(value):
        await event.message.answer(
            text='❗ Неверный формат. Используйте ДД.ММ.ГГГГ (например: 15.03.1990).',
            parse_mode=ParseMode.HTML
        )
        return
    await context.update_data(birthday=value)
    await event.message.answer(
        text='Укажите ваш пол:',
        attachments=[kb.gender_selection_keyboard()],
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.request_gender)


@router.message_callback(RegistrationStates.request_gender)
async def save_gender(event: MessageCallback, context: MemoryContext):
    """Сохранение пола — переход к паспортным данным"""
    if not event.callback.payload.startswith('RegGenderMax:'):
        return
    gender = event.callback.payload.split(':')[1]
    await context.update_data(gender=gender)
    await event.message.answer(
        text='Введите серию паспорта (4 цифры, например: 4510):',
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.passport_series)


@router.message_created(RegistrationStates.passport_series, F.message.body.text)
async def save_passport_series(event: MessageCreated, context: MemoryContext):
    from utils.validators.passport import validate_passport_series
    value = event.message.body.text.strip()
    if not validate_passport_series(value):
        await event.message.answer(
            text='❗ Неверный формат серии. Введите ровно 4 цифры (например: 4510).',
            parse_mode=ParseMode.HTML
        )
        return
    await context.update_data(passport_series=value.upper())
    await event.message.answer(text='Введите номер паспорта (6 цифр):', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.passport_number)


@router.message_created(RegistrationStates.passport_number, F.message.body.text)
async def save_passport_number(event: MessageCreated, context: MemoryContext):
    from utils.validators.passport import validate_passport_number
    value = event.message.body.text.strip()
    if not validate_passport_number(value):
        await event.message.answer(text='❗ Неверный формат. Введите ровно 6 цифр.', parse_mode=ParseMode.HTML)
        return
    await context.update_data(passport_number=value)
    await event.message.answer(text='Введите дату выдачи паспорта (ДД.ММ.ГГГГ):', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.passport_date)


@router.message_created(RegistrationStates.passport_date, F.message.body.text)
async def save_passport_date(event: MessageCreated, context: MemoryContext):
    from utils.validators.passport import validate_passport_issue_date
    value = event.message.body.text.strip()
    if not validate_passport_issue_date(value):
        await event.message.answer(
            text='❗ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 15.03.2018).',
            parse_mode=ParseMode.HTML
        )
        return
    await context.update_data(passport_date=value)
    await event.message.answer(
        text='Введите код подразделения (6 цифр или в формате 000-000):',
        parse_mode=ParseMode.HTML
    )
    await context.set_state(RegistrationStates.passport_dept_code)


@router.message_created(RegistrationStates.passport_dept_code, F.message.body.text)
async def save_passport_dept_code(event: MessageCreated, context: MemoryContext):
    from utils.validators.passport import validate_passport_department_code, format_department_code
    value = event.message.body.text.strip()
    if not validate_passport_department_code(value):
        await event.message.answer(
            text='❗ Неверный формат. Введите 6 цифр (например: 550001 или 550-001).',
            parse_mode=ParseMode.HTML
        )
        return
    await context.update_data(passport_dept_code=format_department_code(value))
    await event.message.answer(text='Введите кем выдан паспорт:', parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.passport_issued_by)


@router.message_created(RegistrationStates.passport_issued_by, F.message.body.text)
async def save_passport_issued_by(event: MessageCreated, context: MemoryContext):
    value = event.message.body.text.strip()
    if len(value) < 5:
        await event.message.answer(
            text='❗ Введите полное название органа, выдавшего паспорт.',
            parse_mode=ParseMode.HTML
        )
        return
    await context.update_data(passport_issued_by=value)
    data = await context.get_data()

    await event.message.answer(
        text=txt.accept_save_new_data_for_security(
            phone_number=data['reg_phone_number'],
            last_name=data['reg_last_name'],
            first_name=data['reg_first_name'],
            middle_name=data['reg_middle_name']
        ),
        attachments=[kb.accept_save_data_for_security()],
        parse_mode=ParseMode.HTML
    )


# ==================== НОВАЯ РЕГИСТРАЦИЯ: SMS-КОД ====================

@router.message_created(RegistrationStates.registration_code, F.message.body.text)
async def get_registration_code(event: MessageCreated, context: MemoryContext):
    """Проверка SMS-кода — создаём работника в РР и переходим к договору"""
    if not event.message.body.text.isdigit():
        await event.message.answer(text=txt.registration_code_error(), parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    code_data = await db.get_registration_code_by_id(code_id=data['RegCodeID'])

    if not code_data:
        await event.message.answer(text=txt.no_registration_code_error(), parse_mode=ParseMode.HTML)
        await context.clear()
        return

    if not check_code(salt=code_data.salt, hashed_code=code_data.code_hash, entered_code=event.message.body.text):
        await event.message.answer(text=txt.registration_code_error(), parse_mode=ParseMode.HTML)
        return

    import asyncio
    asyncio.create_task(db.delete_registration_code(code_id=code_data.id))

    # Создаём работника в РР
    api_worker_id = await fin_create_worker(
        phone_number=data['RegPhoneNumber'].lstrip('+').lstrip('7'),
        inn=data['RegINN'],
        card_number=data.get('RegCard'),
        first_name=data.get('RegFirstName'),
        last_name=data.get('RegLastName'),
        patronymic=data.get('RegMiddleName') or None,
    )

    if not api_worker_id:
        await event.message.answer(
            text='❗ Не удалось зарегистрировать. Попробуйте позже.',
            parse_mode=ParseMode.HTML
        )
        return

    await context.update_data(
        api_worker_id=api_worker_id,
        inn=data['RegINN'],
        reg_max_id=event.from_user.user_id,
        reg_username=event.from_user.username,
        reg_api_phone_number=data['RegPhoneNumber'],
        reg_phone_number=data['RegPhoneNumber'],
        reg_city=data.get('city', ''),
        reg_first_name=data.get('RegFirstName', ''),
        reg_last_name=data.get('RegLastName', ''),
        reg_middle_name=data.get('RegMiddleName', ''),
        api_first_name=data.get('RegFirstName', ''),
        api_last_name=data.get('RegLastName', ''),
        api_middle_name=data.get('RegMiddleName', ''),
        action='new',
    )

    _, is_smz = await fin_check_fns_status(api_worker_id)
    if is_smz:
        await _show_max_contract(event, context, api_worker_id)
    else:
        await event.message.answer(
            text=txt.send_moy_nalog_manual(),
            attachments=[kb.check_registration_keyboard(data['RegPhoneNumber'])],
            parse_mode=ParseMode.HTML
        )


# ==================== НОВАЯ РЕГИСТРАЦИЯ: КАРТА ====================

@router.message_created(RegistrationStates.request_card_number, F.message.body.text)
async def get_card_number(event: MessageCreated, context: MemoryContext):
    """Ввод номера банковской карты"""
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
    # Проверка уникальности карты в глобальной базе РР
    if await fin_get_worker_by_card(card):
        await event.message.answer(text=txt.card_not_unique_error(), parse_mode=ParseMode.HTML)
        return
    await context.update_data(RegCard=card)
    await event.message.answer(text=txt.request_registration_inn(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.request_inn)


# ==================== НОВАЯ РЕГИСТРАЦИЯ: ИНН ====================

@router.message_created(RegistrationStates.request_inn, F.message.body.text)
async def get_registration_inn(event: MessageCreated, context: MemoryContext):
    """Ввод ИНН — проверки + создание работника в fin API"""
    inn = event.message.body.text.strip()
    if not inn.isdigit() or len(inn) != 12:
        await event.message.answer(text=txt.registration_inn_error(), parse_mode=ParseMode.HTML)
        return

    # Проверяем ИНН в нашей БД
    local_worker = await db.get_worker_by_inn(inn=inn)
    if local_worker:
        if not local_worker.max_id:
            # Пользователь зарегистрирован через Telegram — привязываем Max-аккаунт
            await db.update_worker_max_id(
                worker_id=local_worker.id,
                max_id=event.from_user.user_id,
                max_chat_id=event.message.recipient.chat_id,
            )
            is_foreman = await db.is_foreman(worker_id=local_worker.id)
            await event.message.answer(
                text=txt.rejoin_worker(),
                attachments=[kb.foreman_main_menu() if is_foreman else kb.user_main_menu()],
                parse_mode=ParseMode.HTML,
            )
            await context.clear()
        else:
            await event.message.answer(
                text=txt.reg_error_inn_exists(),
                parse_mode=ParseMode.HTML,
            )
            await context.clear()
        return

    # Проверяем ИНН в глобальной базе РР
    rr_worker = await fin_get_worker_by_inn(inn=inn)
    if rr_worker:
        await event.message.answer(
            text=txt.reg_error_inn_rr_exists(),
            parse_mode=ParseMode.HTML,
        )
        await context.clear()
        return

    data = await context.get_data()
    api_worker_id = await fin_create_worker(
        phone_number=data['RegPhoneNumber'].lstrip('+').lstrip('7'),
        inn=inn,
        card_number=data.get('RegCard'),
    )

    if not api_worker_id:
        await event.message.answer(
            text='❗ Не удалось зарегистрировать. Попробуйте позже.',
            parse_mode=ParseMode.HTML
        )
        return

    await context.update_data(RegINN=inn, inn=inn, api_worker_id=api_worker_id)

    # Сразу проверяем SMZ-статус
    _, is_smz = await fin_check_fns_status(api_worker_id)
    if is_smz:
        # Самозанятый — сначала собираем ФИО/паспорт, затем договор
        cur = await context.get_data()
        await context.update_data(
            reg_max_id=event.from_user.user_id,
            reg_username=event.from_user.username,
            reg_api_phone_number=cur.get('RegPhoneNumber', ''),
            reg_phone_number=cur.get('RegPhoneNumber', ''),
            reg_city=cur.get('city', ''),
            api_first_name='',
            api_middle_name='',
            api_last_name='',
            action='new',
        )
        await event.message.answer(text=txt.last_name_for_security(), parse_mode=ParseMode.HTML)
        await context.set_state(RegistrationStates.last_name_for_security)
    else:
        # Нужно подключить «Мой налог»
        await event.message.answer(text=txt.send_moy_nalog_manual(), parse_mode=ParseMode.HTML)
        await event.message.answer(
            text='Нажмите кнопку ниже, когда дадите разрешение в приложении «Мой налог»:',
            attachments=[kb.registration_permission_request(api_worker_id=api_worker_id)],
            parse_mode=ParseMode.HTML
        )


# ==================== НОВАЯ РЕГИСТРАЦИЯ: ПРОВЕРКА РАЗРЕШЕНИЯ ФНС ====================

@router.message_callback(F.callback.payload.startswith('RegGavePermission:'))
async def check_permissions(event: MessageCallback, context: MemoryContext):
    """Проверка статуса самозанятого после выдачи разрешения"""
    api_worker_id = int(event.callback.payload.split(':')[1])

    if not api_worker_id:
        data = await context.get_data()
        phone = data.get('RegPhoneNumber', '').lstrip('+').lstrip('7')
        found = await fin_get_worker_by_phone(phone)
        if found:
            api_worker_id = found.get('id', 0)
        if not api_worker_id:
            await event.message.answer(
                text='⚠️ Не удалось найти ваш аккаунт в системе. Попробуйте позже.',
                parse_mode=ParseMode.HTML
            )
            return
        await context.update_data(api_worker_id=api_worker_id)

    permissions, is_smz = await fin_check_fns_status(api_worker_id)

    if not permissions:
        await event.message.answer(
            text='⚠️ Разрешение ещё не получено. Следуйте инструкции и попробуйте снова.',
            attachments=[kb.registration_permission_request(api_worker_id=api_worker_id)],
            parse_mode=ParseMode.HTML
        )
        return

    if not is_smz:
        await event.message.answer(
            text='❗ Вы не являетесь самозанятым. Зарегистрируйтесь в приложении «Мой налог».',
            attachments=[kb.registration_permission_request(api_worker_id=api_worker_id)],
            parse_mode=ParseMode.HTML
        )
        return

    full_name = await fin_get_worker_full_name(api_worker_id)
    if not full_name:
        await event.message.answer(text='❗ Произошла ошибка. Попробуйте позже.', parse_mode=ParseMode.HTML)
        return

    data = await context.get_data()
    await context.update_data(
        api_first_name=full_name['first_name'],
        api_last_name=full_name['last_name'],
        api_middle_name=full_name['middle_name'],
        reg_max_id=event.from_user.user_id,
        reg_username=event.from_user.username,
        reg_api_phone_number=data.get('RegPhoneNumber', ''),
        reg_phone_number=data.get('RegPhoneNumber', ''),
        reg_city=data.get('city', ''),
        inn=data.get('RegINN', '') or data.get('inn', ''),
        api_worker_id=api_worker_id,
        action='new',
    )

    # Телефон уже в контексте (RegPhoneNumber) — сразу к ФИО
    await event.message.answer(text=txt.last_name_for_security(), parse_mode=ParseMode.HTML)
    await context.set_state(RegistrationStates.last_name_for_security)


# ==================== ДОГОВОР: СОЗДАНИЕ И ПОДПИСАНИЕ ====================

async def _show_max_contract(
    event,
    context: MemoryContext,
    api_worker_id: int,
) -> None:
    """Проверяет/создаёт договоры в fin API и показывает запрос на подписание."""
    contracts = await create_all_contracts_for_worker(worker_id=api_worker_id)

    if contracts is None:
        # API полностью недоступен
        await event.message.answer(
            text=txt.send_contract_error(),
            parse_mode=ParseMode.HTML,
        )
        return

    if not contracts:
        # Все 3 договора уже подписаны — сразу завершаем регистрацию
        data = await context.get_data()
        inn = data.get('RegINN') or data.get('inn', '')
        _first = data.get('RegFirstName') or data.get('api_first_name') or data.get('reg_first_name', '')
        _last = data.get('RegLastName') or data.get('api_last_name') or data.get('reg_last_name', '')
        _middle = data.get('RegMiddleName') or data.get('api_middle_name') or data.get('reg_middle_name', '')
        _city = data.get('city') or data.get('reg_city', '')
        _phone = data.get('RegPhoneNumber') or data.get('reg_api_phone_number', '')
        _username = data.get('reg_username') or str(data.get('reg_max_id', '') or event.from_user.user_id)
        user_id = await db.set_user(
            max_id=event.from_user.user_id,
            max_chat_id=event.message.recipient.chat_id,
            username=_username,
            phone_number=_phone,
            city=_city,
            real_phone_number=_phone,
            real_first_name=_first,
            real_last_name=_last,
            real_middle_name=_middle,
            first_name=_first,
            middle_name=_middle,
            last_name=_last,
            inn=inn,
            api_worker_id=api_worker_id,
            card=data.get('RegCard') or data.get('fin_card') or data.get('card', ''),
            gender=data.get('gender'),
            passport_series=data.get('passport_series'),
            passport_number=data.get('passport_number'),
            passport_issue_date=data.get('passport_date'),
            passport_department_code=data.get('passport_dept_code'),
            passport_issued_by=data.get('passport_issued_by'),
        )
        if user_id:
            await db.create_contracts_for_all_orgs(user_id=user_id)
            await db.sign_contracts_for_user(user_id=user_id, tg_id=event.from_user.user_id)
        await context.clear()
        await event.message.answer(
            text=txt.all_contracts_already_signed() + f'\n\n{txt.registration_user_completed()}',
            attachments=[kb.user_main_menu()],
            parse_mode=ParseMode.HTML,
        )
        return

    await context.update_data(RegContracts=contracts)
    await event.message.answer(
        text=(
            '📄 Для завершения регистрации необходимо подписать договоры с заказчиками.\n\n'
            'Ознакомьтесь с условиями и нажмите «Подписать», если согласны.'
        ),
        attachments=[kb.sign_api_contract_max()],
        parse_mode=ParseMode.HTML,
    )


@router.message_callback(F.callback.payload == 'SignContractMax')
async def sign_contract_max(event: MessageCallback, context: MemoryContext):
    """Запрос PIN для подписания (случайный тип из 4 вариантов)."""
    data = await context.get_data()
    inn = data.get('RegINN') or data.get('inn', '')
    pin_type, _pin_val, hint = choose_pin(
        inn=inn,
        birthday=data.get('birthday') or data.get('RegBirthDate', ''),
        passport_number=data.get('passport_number') or data.get('RegPassportNumber', ''),
    )
    await context.update_data(SignPinType=pin_type)
    await event.message.answer(
        text=f'📄 Вы подписываете договор с заказчиками\n\n🔐 Для подтверждения введите {hint}',
        parse_mode=ParseMode.HTML,
    )
    await context.set_state(RegistrationStates.sign_contract_code)


@router.message_created(RegistrationStates.sign_contract_code, F.message.body.text)
async def get_sign_contract_code_max(event: MessageCreated, context: MemoryContext):
    """Проверяет PIN, подписывает договоры и создаёт пользователя."""
    import logging
    data = await context.get_data()
    inn = data.get('RegINN') or data.get('inn', '')
    pin_type = data.get('SignPinType', 'inn')

    if not verify_pin(
        pin_type=pin_type,
        entered=event.message.body.text,
        inn=inn,
        birthday=data.get('birthday') or data.get('RegBirthDate', ''),
        passport_number=data.get('passport_number') or data.get('RegPassportNumber', ''),
    ):
        await event.message.answer(text=txt.contract_inn_error(), parse_mode=ParseMode.HTML)
        return

    contracts = data.get('RegContracts', [])
    await context.set_state(None)
    await event.message.answer(
        text=txt.sign_contracts_for_registration_wait(),
        parse_mode=ParseMode.HTML,
    )

    if contracts:
        try:
            signed = await sign_all_worker_contracts(contracts)
            logging.info(f'[max][sign] fin API sign result={signed}')
        except Exception as e:
            logging.exception(f'[max][sign] sign_all_worker_contracts failed: {e}')
            await event.message.answer(
                text='⚠️ Не удалось подписать договоры: сервис временно недоступен.\n\nПопробуйте нажать «Подписать» ещё раз через минуту.',
                attachments=[kb.sign_api_contract_max()],
                parse_mode=ParseMode.HTML,
            )
            await context.set_state(RegistrationStates.sign_contract_code)
            return

    # Новый флоу: RegFirstName/RegLastName/RegCity; старый флоу: reg_first_name/reg_city
    first_name = data.get('RegFirstName') or data.get('api_first_name') or data.get('reg_first_name', '')
    last_name = data.get('RegLastName') or data.get('api_last_name') or data.get('reg_last_name', '')
    middle_name = data.get('RegMiddleName') or data.get('api_middle_name') or data.get('reg_middle_name', '')
    city = data.get('city') or data.get('reg_city', '')
    phone_number = data.get('RegPhoneNumber') or data.get('reg_api_phone_number', '')
    username = data.get('reg_username') or str(data.get('reg_max_id', '') or event.from_user.user_id)

    user_id = await db.set_user(
        max_id=event.from_user.user_id,
        max_chat_id=event.message.recipient.chat_id,
        username=username,
        phone_number=phone_number,
        city=city,
        real_phone_number=phone_number,
        real_first_name=first_name,
        real_last_name=last_name,
        real_middle_name=middle_name,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        inn=inn,
        api_worker_id=data.get('api_worker_id', 0),
        card=data.get('RegCard') or data.get('fin_card') or data.get('card', ''),
        gender=data.get('gender'),
        passport_series=data.get('passport_series'),
        passport_number=data.get('passport_number'),
        passport_issue_date=data.get('passport_date'),
        passport_department_code=data.get('passport_dept_code'),
        passport_issued_by=data.get('passport_issued_by'),
    )

    if user_id:
        await db.create_contracts_for_all_orgs(user_id=user_id)
        await db.sign_contracts_for_user(user_id=user_id, tg_id=event.from_user.user_id)

    await context.clear()
    await event.message.answer(
        text=txt.registration_user_completed(),
        attachments=[kb.user_main_menu()],
        parse_mode=ParseMode.HTML,
    )


@router.message_callback(F.callback.payload == 'RejectContractMax')
async def reject_contract_max(event: MessageCallback, context: MemoryContext):
    """Отказ от подписания договора."""
    await context.set_state(None)
    await event.message.answer(
        text=txt.contract_rejected(),
        parse_mode=ParseMode.HTML,
    )
