from aiogram import Router, F
from aiogram.types import (
    Message, LinkPreviewOptions,
    CallbackQuery, ReplyKeyboardRemove,
    InputMediaDocument, BufferedInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging
import secrets
import asyncio

from utils.organizations import orgs_dict
from utils.static_contract import get_static_contract_bytes, STATIC_CONTRACT_FILENAME
from utils import (
    normalize_phone_number,
    create_code_hash, check_code,
    schedule_delete_verification_code,
    schedule_delete_registration_code,
    send_sms_with_api, luhn_check,
)
import keyboards.inline as ikb
import keyboards.reply as kb
from API import (
    api_get_worker_full_name,
    api_check_fns_status,
    create_all_contracts_for_worker,
    get_preview_contract_bytes,
    sign_all_worker_contracts,
)
from API.fin.workers import fin_get_worker_by_phone, fin_create_worker, fin_get_worker_by_card
import database as db
import texts as txt
from utils.loggers import write_registration_log
from utils.contract_pin import choose_pin, verify_pin


router = Router()


# ── Точка входа: «Войти» / «Регистрация» ─────────────────────────────────────

@router.callback_query(F.data == 'EntryLogin')
async def entry_login(callback: CallbackQuery, state: FSMContext):
    """Нажал «Войти» — выбираем город."""
    await state.clear()
    write_registration_log(f'Пользователь {callback.from_user.id} | Нажал «Войти»')
    await callback.message.edit_text(
        text=txt.request_worker_city(),
        reply_markup=await ikb.cities_for_login(),
    )


@router.callback_query(F.data.startswith('LoginCity:'))
async def login_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(':')[1]
    await state.update_data(LoginCity=city)
    await callback.message.edit_text(text='📱 Введите ваш номер телефона для входа:')
    await state.set_state('LoginRequestPhone')


@router.callback_query(F.data == 'EntryRegister')
async def entry_register(callback: CallbackQuery, state: FSMContext):
    """Нажал «Регистрация» — спрашиваем, является ли самозанятым."""
    await state.clear()
    write_registration_log(f'Пользователь {callback.from_user.id} | Нажал «Регистрация»')
    await callback.message.edit_text(
        text='❓ Вы являетесь самозанятым?',
        reply_markup=ikb.are_you_self_employed(),
    )


# ── Вход по телефону ──────────────────────────────────────────────────────────

@router.message(F.text, StateFilter('LoginRequestPhone'))
async def login_by_phone(message: Message, state: FSMContext):
    """Вход по номеру телефона — только для уже зарегистрированных."""
    phone_number = normalize_phone_number(message.text)
    if not phone_number:
        await message.answer(text=txt.phone_number_error(), protect_content=True)
        return

    worker = await db.get_worker_by_phone_number(phone_number=phone_number)
    if worker:
        if worker.tg_id == 0:
            # tg_id не привязан — проверяем, есть ли Max ID для верификации
            if worker.max_id:
                # Есть Max-аккаунт — отправляем код туда
                code = str(secrets.randbelow(900000) + 100000)
                code_hashed = create_code_hash(code=code)
                code_id = await db.set_verification_code_max(
                    worker_id=worker.id,
                    max_id=worker.max_id,
                    code_hash=code_hashed['hash'],
                    salt=code_hashed['salt'],
                )
                await schedule_delete_verification_code(code_id=code_id)
                try:
                    from config_reader import config as _cfg
                    from maxapi import Bot as MaxBot
                    from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                    _max_bot = MaxBot(token=_cfg.max_bot_token.get_secret_value())
                    await _max_bot.send_message(
                        user_id=worker.max_id,
                        text=txt.verification_code(code=code),
                        parse_mode=MaxParseMode.HTML,
                    )
                    await _max_bot.close_session()
                except Exception:
                    pass
                del code
                await message.answer(text=txt.request_verification_code(), protect_content=True)
                await state.update_data(CodeID=code_id)
                await state.set_state('VerificationCode')
            else:
                # Оба ID не привязаны (администратор стёр) — разрешаем прямой вход
                await db.update_worker_tg_id(worker_id=worker.id, tg_id=message.from_user.id)
                await message.answer(
                    text=txt.rejoin_worker(),
                    reply_markup=kb.user_menu(),
                    protect_content=True,
                )
                await state.clear()
        else:
            # Есть другой TG-аккаунт — отправляем код туда
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
                await message.bot.send_message(
                    chat_id=worker.tg_id,
                    text=txt.verification_code(code=code),
                )
            except Exception:
                pass
            del code
            await message.answer(text=txt.request_verification_code(), protect_content=True)
            await state.update_data(CodeID=code_id)
            await state.set_state('VerificationCode')
    else:
        # Не нашли в локальной БД — проверяем fin API
        existing = await db.get_user(tg_id=message.from_user.id)
        if existing:
            await message.answer(
                text=txt.rejoin_worker(),
                reply_markup=kb.user_menu(),
                protect_content=True,
            )
            await state.clear()
            return

        api_worker = await fin_get_worker_by_phone(
            phone=phone_number.lstrip('+').lstrip('7'),
        )
        if api_worker:
            login_data = await state.get_data()
            await db.set_user(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                phone_number=phone_number,
                city=login_data.get('LoginCity', ''),
                real_phone_number=phone_number,
                first_name=api_worker.get('firstName', ''),
                last_name=api_worker.get('lastName', ''),
                middle_name=api_worker.get('patronymic', ''),
                real_first_name=api_worker.get('firstName', ''),
                real_last_name=api_worker.get('lastName', ''),
                real_middle_name=api_worker.get('patronymic', ''),
                inn=str(api_worker.get('inn', '')),
                api_worker_id=api_worker['id'],
                card=api_worker.get('bankcardNumber') or '',
            )
            await message.answer(
                text=txt.rejoin_worker(),
                reply_markup=kb.user_menu(),
                protect_content=True,
            )
            await state.clear()
        else:
            await message.answer(
                text=(
                    '❗ Номер не найден\n\n'
                    'Ваш номер отсутствует в базе партнёра ООО «Рабочие Руки» или введён с ошибкой\n\n'
                    '📱 Проверьте номер и попробуйте ещё раз\n\n'
                    '🚀 Ещё не зарегистрированы?\n'
                    '➡️ Нажмите /start и выберите «Регистрация» — это займёт 1–2 минуты'
                ),
                protect_content=True,
            )
            await state.clear()


@router.message(F.text, StateFilter('VerificationCode'))
async def get_verification_code(message: Message, state: FSMContext):
    if message.text.isdigit():
        data = await state.get_data()
        code_data = await db.get_code_by_id(code_id=data['CodeID'])
        if code_data:
            checking_code = check_code(
                salt=code_data.salt,
                hashed_code=code_data.code_hash,
                entered_code=message.text
            )
            if checking_code:
                old_worker = await db.get_user_by_id(user_id=code_data.worker_id)
                await db.update_worker_tg_id(
                    worker_id=code_data.worker_id,
                    tg_id=message.from_user.id
                )
                await db.delete_verification_code(code_id=code_data.id)
                city = data.get('RegCity')
                if city:
                    await db.update_user_city(worker_id=code_data.worker_id, city=city)
                await message.answer(
                    text=txt.verification_completed(),
                    reply_markup=kb.user_menu(),
                    protect_content=True
                )
                try:
                    await message.bot.send_message(
                        chat_id=old_worker.tg_id,
                        text=txt.account_notification(),
                        reply_markup=ReplyKeyboardRemove(),
                        protect_content=True
                    )
                except Exception:
                    pass
            else:
                await message.answer(text=txt.verification_code_error(), protect_content=True)
        else:
            await message.answer(text=txt.no_verification_code_error(), protect_content=True)
        await state.clear()
    else:
        await message.answer(text=txt.add_id_error(), protect_content=True)


# ── Самозанятый? ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == 'RegYesSMZ')
async def reg_yes_smz(callback: CallbackQuery):
    """«Да» — показываем выбор города."""
    await callback.answer()
    await callback.message.edit_text(
        text=txt.request_worker_city(),
        reply_markup=await ikb.cities_for_registration(),
    )


@router.callback_query(F.data == 'RegNoSMZ')
async def reg_no_smz(callback: CallbackQuery):
    """«Нет» — показываем картинку-инструкцию как стать самозанятым."""
    await callback.answer()
    settings = await db.get_settings()
    await callback.message.delete()
    if settings.smz_pic:
        await callback.message.answer_document(
            document=settings.smz_pic,
            caption=txt.smz_instruction_text(),
            reply_markup=ikb.became_self_employed_button(),
        )
    else:
        await callback.message.answer(
            text=txt.smz_instruction_text(),
            reply_markup=ikb.became_self_employed_button(),
        )


@router.callback_query(F.data == 'RegBecameSMZ')
async def reg_became_smz(callback: CallbackQuery):
    """«Я стал самозанятым» — переходим к форме регистрации."""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        text=txt.request_worker_city(),
        reply_markup=await ikb.cities_for_registration(),
    )


# ── Форма регистрации: Город → ФИО → ДР → ИНН → Карта → Паспорт → Телефон ──

@router.callback_query(F.data.startswith('RegCity:'))
async def get_city(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split(':')[1]
    await state.update_data(RegCity=city)
    write_registration_log(f'Пользователь {callback.from_user.id} | Выбрал город: {city}')
    await callback.message.edit_text(text='Введите вашу фамилию:')
    await state.set_state('RegLastName')


@router.message(F.text, StateFilter('RegLastName'))
async def get_last_name(message: Message, state: FSMContext):
    value = message.text.strip()
    if len(value) < 2:
        await message.answer('❗ Введите корректную фамилию.')
        return
    await state.update_data(RegLastName=value, RealLastName=value)
    await message.answer('Введите ваше имя:', protect_content=True)
    await state.set_state('RegFirstName')


@router.message(F.text, StateFilter('RegFirstName'))
async def get_first_name(message: Message, state: FSMContext):
    value = message.text.strip()
    if len(value) < 2:
        await message.answer('❗ Введите корректное имя.')
        return
    await state.update_data(RegFirstName=value, RealFirstName=value)
    await message.answer(
        'Введите ваше отчество (или нажмите кнопку если его нет):',
        reply_markup=ikb.skip_patronymic(),
        protect_content=True
    )
    await state.set_state('RegMiddleName')


@router.message(F.text, StateFilter('RegMiddleName'))
async def get_middle_name(message: Message, state: FSMContext):
    value = message.text.strip()
    await state.update_data(RegMiddleName=value, RealMiddleName=value)
    await message.answer('🔢 Введите ваш ИНН (12 цифр):', protect_content=True)
    await state.set_state('RegINN')


@router.callback_query(F.data == 'RegSkipPatronymic', StateFilter('RegMiddleName'))
async def skip_middle_name(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(RegMiddleName='', RealMiddleName='')
    await callback.message.edit_text('🔢 Введите ваш ИНН (12 цифр):')
    await state.set_state('RegINN')


@router.message(F.text, StateFilter('RegINN'))
async def get_reg_inn(message: Message, state: FSMContext):
    value = message.text.strip()
    if not (value.isdigit() and len(value) == 12):
        await message.answer(txt.registration_inn_error(), protect_content=True)
        return
    # Проверяем — нет ли уже такого ИНН в нашей БД
    local_worker = await db.get_worker_by_inn(inn=value)
    if local_worker:
        await message.answer(
            txt.reg_error_inn_exists(),
            protect_content=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
            parse_mode='HTML',
        )
        await state.clear()
        return
    # Проверяем — нет ли уже такого ИНН в глобальной базе РР (fin API)
    from API.fin.workers import fin_get_worker_by_inn
    rr_worker = await fin_get_worker_by_inn(inn=value)
    if rr_worker:
        await message.answer(
            txt.reg_error_inn_rr_exists(),
            protect_content=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        await state.clear()
        return
    await state.update_data(RegINN=value)
    await message.answer(txt.request_card(), protect_content=True)
    await state.set_state('RegCard')


@router.message(F.text, StateFilter('RegCard'))
async def get_reg_card(message: Message, state: FSMContext):
    card = message.text.replace(' ', '')
    if not card.isdigit():
        await message.answer(txt.card_number_error())
        return
    if not luhn_check(card):
        await message.answer(txt.luhn_check_error())
        return
    # Проверяем уникальность в локальной БД
    if await db.card_unique(card):
        await message.answer(
            txt.card_not_unique_error(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    # Проверяем уникальность в fin API (РР)
    existing = await fin_get_worker_by_card(card)
    if existing:
        await message.answer(
            txt.card_not_unique_error(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    await state.update_data(RegCard=card)
    await message.answer(
        '📱 Введите ваш номер телефона (например: +79031234567):',
        protect_content=True,
    )
    await state.set_state('RegPhoneForSMS')


@router.message(F.text, StateFilter('RegPhoneForSMS'))
async def get_phone_for_sms(message: Message, state: FSMContext):
    phone_number = normalize_phone_number(message.text)
    if not phone_number:
        await message.answer(txt.phone_number_error(), protect_content=True)
        return

    # Проверяем что номер ещё не зарегистрирован в локальной БД
    has_worker = await db.get_worker_by_phone_number(phone_number=phone_number)
    if has_worker:
        await message.answer(
            txt.reg_error_phone_exists(),
            protect_content=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    # Проверяем что номер не занят в fin API (чтобы не тратить SMS)
    fin_worker = await fin_get_worker_by_phone(phone_number)
    if fin_worker:
        await message.answer(
            txt.reg_error_phone_exists(),
            protect_content=True,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    # Проверяем лимит SMS (2 в сутки)
    can_send = await db.check_daily_code_attempts(phone_number=phone_number)
    if not can_send:
        write_registration_log(
            f'Пользователь {message.from_user.id} | Превышен лимит SMS | Телефон: {phone_number}',
            level='ERROR',
        )
        await message.answer('⚠️ Превышен лимит. Попробуйте через 24 часа.', protect_content=True)
        return

    code = str(secrets.randbelow(900000) + 100000)
    code_hashed = create_code_hash(code=code)
    code_id = await db.set_registration_code(
        code_hash=code_hashed['hash'],
        salt=code_hashed['salt'],
    )
    await schedule_delete_registration_code(code_id=code_id)
    await state.update_data(
        RegPhoneNumber=phone_number,
        RealPhoneNumber=phone_number,
        RegCodeID=code_id,
    )
    await state.set_state('RegSMSCode')
    await message.answer(txt.request_registration_code(), protect_content=True)
    await send_sms_with_api(
        phone_number=phone_number,
        message_text=txt.send_registration_message(code=code),
        tg_id=message.from_user.id,
    )
    del code


@router.message(F.text, StateFilter('RegSMSCode'))
async def get_reg_sms_code(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(txt.add_id_error(), protect_content=True)
        return

    data = await state.get_data()
    code_data = await db.get_registration_code_by_id(code_id=data['RegCodeID'])

    if not code_data:
        await message.answer(txt.no_registration_code_error(), protect_content=True)
        return

    if not check_code(
        salt=code_data.salt,
        hashed_code=code_data.code_hash,
        entered_code=message.text,
    ):
        await message.answer(txt.registration_code_error(), protect_content=True)
        return

    await state.set_state(None)
    asyncio.create_task(db.delete_registration_code(code_id=code_data.id))

    # Создаём работника в РР (fin API)
    api_worker_id = await fin_create_worker(
        phone_number=data['RegPhoneNumber'].lstrip('+').lstrip('7'),
        inn=data['RegINN'],
        card_number=data['RegCard'],
        first_name=data.get('RegFirstName'),
        last_name=data.get('RegLastName'),
        patronymic=data.get('RegMiddleName') or None,
    )

    if not api_worker_id:
        await message.answer('❗ Не удалось вас зарегистрировать. Пожалуйста, попробуйте позже')
        return

    await state.update_data(RegApiWorkerID=api_worker_id)

    # Проверяем SMZ-статус сразу
    _, is_self_employment = await api_check_fns_status(api_worker_id=api_worker_id)
    write_registration_log(
        f'Пользователь {message.from_user.id} | ФНС статус после создания: is_smz={is_self_employment} | api_worker_id={api_worker_id}'
    )
    if is_self_employment:
        await _show_reg_contract(message, state)
    else:
        await message.answer(
            text=txt.send_moy_nalog_manual(),
            reply_markup=ikb.registration_permission_request(api_worker_id=api_worker_id),
            protect_content=True,
        )


# ── Проверка статуса СМЗ ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith('RegGavePermission:'))
async def check_permissions(callback: CallbackQuery, state: FSMContext):
    api_worker_id = int(callback.data.split(':')[1])
    write_registration_log(
        f'Пользователь {callback.from_user.id} | Нажал «Проверить ещё раз» | api_worker_id={api_worker_id}'
    )
    permissions, is_self_employment = await api_check_fns_status(api_worker_id=api_worker_id)
    write_registration_log(
        f'Пользователь {callback.from_user.id} | ФНС статус: permissions={permissions}, is_smz={is_self_employment}'
    )
    if permissions:
        if is_self_employment:
            await callback.answer()
            data = await state.get_data()

            if data.get('RegCity'):
                # Новый флоу: все данные уже собраны в форме → показываем договор
                await _show_reg_contract(callback, state)
            else:
                # Старый путь: нужно выбрать город и ввести ФИО — получаем из fin API
                result = await api_get_worker_full_name(api_worker_id=api_worker_id)
                if not result:
                    await callback.message.edit_text(text='❗Произошла ошибка. Попробуйте позже')
                    return
                await state.update_data(
                    RegFirstName=result['first_name'],
                    RegLastName=result['last_name'],
                    RegMiddleName=result['middle_name'],
                    RealFirstName=result['first_name'],
                    RealLastName=result['last_name'],
                    RealMiddleName=result['middle_name']
                )
                await callback.message.edit_text(
                    text=txt.request_worker_city(),
                    reply_markup=await ikb.cities_for_registration(),
                    protect_content=True
                )
        else:
            settings = await db.get_settings()
            try:
                if settings.registration_pic:
                    await callback.message.edit_media(
                        media=InputMediaDocument(media=settings.registration_pic),
                        reply_markup=ikb.confirmation_became_self_employment(
                            api_worker_id=api_worker_id,
                        )
                    )
                else:
                    await callback.message.edit_text(
                        text=txt.send_manual_error(),
                        reply_markup=ikb.confirmation_became_self_employment(
                            api_worker_id=api_worker_id,
                        )
                    )
            except Exception:
                await callback.answer(
                    text='❗️Вы не являетесь самозанятым',
                    show_alert=True,
                )
    else:
        await callback.answer()
        wait_text = (
            '⏳ Проверяем ваш статус самозанятости\n'
            'Обычно это занимает до 5 минут\n\n'
            'Пожалуйста, подождите 🙌'
        )
        wait_kb = ikb.registration_permission_request(api_worker_id=api_worker_id)
        try:
            await callback.message.edit_caption(caption=wait_text, reply_markup=wait_kb)
        except Exception:
            await callback.message.edit_text(text=wait_text, reply_markup=wait_kb)


async def _show_reg_contract(event: CallbackQuery | Message, state: FSMContext):
    """Проверяет/создаёт договоры в fin API и показывает PDF первого для подписания."""
    data = await state.get_data()
    api_worker_id = data.get('RegApiWorkerID')
    msg = event.message if isinstance(event, CallbackQuery) else event

    contracts = await create_all_contracts_for_worker(worker_id=api_worker_id)

    if contracts is None:
        # API полностью недоступен
        await msg.answer(text=txt.send_contract_error())
        return

    if not contracts:
        # Все 3 договора уже подписаны — сразу завершаем регистрацию
        await msg.answer(text=txt.all_contracts_already_signed())
        user_id = await registration_complete(state=state, event=event)
        if user_id:
            await db.create_contracts_for_all_orgs(user_id=user_id)
            await db.sign_contracts_for_user(user_id=user_id, tg_id=event.from_user.id)
        return

    await state.update_data(RegContracts=contracts)

    contract_bytes = get_static_contract_bytes()
    try:
        if contract_bytes:
            await msg.answer_document(
                document=BufferedInputFile(
                    file=contract_bytes,
                    filename=STATIC_CONTRACT_FILENAME,
                ),
                caption=txt.preview_contract(),
                reply_markup=ikb.sign_api_contract(),
            )
        else:
            await msg.answer(
                text=txt.preview_contract(),
                reply_markup=ikb.sign_api_contract(),
            )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await msg.answer(text=txt.send_contract_error())
    finally:
        if isinstance(event, CallbackQuery):
            await msg.delete()


async def registration_complete(
        state: FSMContext,
        event: CallbackQuery | Message,
) -> int | None:
    data = await state.get_data()
    await state.clear()

    user_id = await db.set_user(
        tg_id=event.from_user.id,
        username=event.from_user.username,
        phone_number=data['RegPhoneNumber'],
        city=data['RegCity'],
        real_phone_number=data['RealPhoneNumber'],
        real_first_name=data['RealFirstName'],
        real_last_name=data['RealLastName'],
        real_middle_name=data['RealMiddleName'],
        first_name=data['RegFirstName'],
        middle_name=data['RegMiddleName'],
        last_name=data['RegLastName'],
        inn=data['RegINN'],
        api_worker_id=data['RegApiWorkerID'],
        card=data['RegCard'],
        gender=data.get('RegGender'),
    )
    msg = event if isinstance(event, Message) else event.message
    if isinstance(event, CallbackQuery):
        await event.message.delete()

    await msg.answer(
        text=txt.registration_user_completed(),
        reply_markup=kb.user_menu(),
    )

    settings = await db.get_settings()
    if settings.rr_partner_pic:
        await msg.answer_document(
            document=settings.rr_partner_pic,
            caption=txt.rr_partner_connection_caption(),
        )
    else:
        await msg.answer(text=txt.rr_partner_connection_caption())

    return user_id


@router.callback_query(F.data == 'SaveDataForSecurity')
async def registration_completed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение данных безопасности (старый путь через форму без SMZ-проверки)."""
    await callback.answer()
    data = await state.get_data()

    if data.get('IsRegistered', False):
        await registration_complete(state=state, event=callback)
    else:
        await _show_reg_contract(callback, state)


@router.callback_query(F.data == 'NewDataForSecurity')
async def registration_for_security(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        text=txt.phone_for_security(),
        reply_markup=kb.request_phone_number(),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    await callback.message.delete()
    await state.set_state('PhoneNumberForSecurity')


@router.message(F.contact, StateFilter('PhoneNumberForSecurity'))
async def save_contact(message: Message, state: FSMContext):
    await state.update_data(RealPhoneNumber=message.contact.phone_number)
    await message.answer(
        text=txt.last_name_for_security(),
        reply_markup=ReplyKeyboardRemove(),
        protect_content=True
    )
    await state.set_state('LastNameForSecurity')


@router.message(F.text, StateFilter('LastNameForSecurity'))
async def save_last_name(message: Message, state: FSMContext):
    await state.update_data(RealLastName=message.text.capitalize())
    await message.answer(text=txt.first_name_for_security(), protect_content=True)
    await state.set_state('FirstNameForSecurity')


@router.message(F.text, StateFilter('FirstNameForSecurity'))
async def save_first_name(message: Message, state: FSMContext):
    await state.update_data(RealFirstName=message.text.capitalize())
    await message.answer(text=txt.middle_name_for_security(), protect_content=True)
    await state.set_state('MiddleNameForSecurity')


@router.message(F.text, StateFilter('MiddleNameForSecurity'))
async def save_middle_name(message: Message, state: FSMContext):
    await state.update_data(RealMiddleName=message.text.capitalize())
    data = await state.get_data()
    await message.answer(
        text=txt.confirmation_save_new_data_for_security(
            phone_number=data['RealPhoneNumber'],
            last_name=data['RealLastName'],
            first_name=data['RealFirstName'],
            middle_name=data['RealMiddleName']
        ),
        reply_markup=ikb.confirmation_save_data_for_security(),
        protect_content=True
    )


# ── Подписание договора ───────────────────────────────────────────────────────

@router.callback_query(F.data == 'SignContract')
async def sign_contract(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    pin_type, _pin_val, hint = choose_pin(
        inn=data.get('RegINN', ''),
        birthday=data.get('RegBirthDate', ''),
        passport_number=data.get('RegPassportNumber', ''),
    )
    await state.update_data(SignPinType=pin_type)
    await callback.message.answer(
        text=f'📄 Вы подписываете договор с заказчиками\n\n🔐 Для подтверждения введите {hint}'
    )
    await state.set_state('SignContractCode')
    await callback.message.delete()


@router.message(F.text, StateFilter('SignContractCode'))
async def get_sign_contract_code(message: Message, state: FSMContext):
    data = await state.get_data()
    pin_type = data.get('SignPinType', 'inn')
    if not verify_pin(
        pin_type=pin_type,
        entered=message.text,
        inn=data.get('RegINN', ''),
        birthday=data.get('RegBirthDate', ''),
        passport_number=data.get('RegPassportNumber', ''),
    ):
        await message.answer(text=txt.contract_inn_error())
        return

    contracts = data.get('RegContracts', [])
    await state.set_state(None)
    await message.answer(text=txt.sign_contracts_for_registration_wait())

    # Подписываем договоры в fin API
    if contracts:
        signed = await sign_all_worker_contracts(contracts)
        logging.info(f'[sign] fin API sign result={signed} contracts={[c.get("id") for c in contracts]}')

    # Фиксируем подписание в нашей БД
    user_id = await registration_complete(state=state, event=message)
    if user_id:
        await db.create_contracts_for_all_orgs(user_id=user_id)
        await db.sign_contracts_for_user(user_id=user_id, tg_id=message.from_user.id)
        logging.info(f'[sign] user_id={user_id} — 3 договора подписано')


@router.callback_query(F.data == 'RejectContract')
async def reject_contract(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(None)
    await callback.message.answer(text=txt.contract_rejected())
    await callback.message.delete()
