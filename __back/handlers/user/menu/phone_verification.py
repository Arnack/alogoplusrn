import logging
import random
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from filters import Worker
import database as db
import texts as txt
from utils import (
    normalize_phone_number,
    create_code_hash,
    check_code,
    send_sms_with_api,
    send_phone_to_pp
)

router = Router()

VERIFY_INTERVAL_DAYS = 30
SMS_TEMPLATE = '[Алгоритм Плюс] Код подтверждения: {code}'


async def _need_verification(user_id: int, call_block: bool) -> tuple[bool, str]:
    """
    Проверяет, нужна ли SMS-верификация.
    Возвращает (need: bool, reason: str).
    reason: 'call_block' | ''
    
    Логика: SMS запрашивается ТОЛЬКО если установлен call_block 
    (после получения blue/yellow от прозвона) И прошло 30+ дней с последней верификации.
    """
    if not call_block:
        # Нет блокировки — верификация не нужна
        return False, ''
    
    # call_block установлен — проверяем, была ли недавняя верификация
    verification = await db.get_phone_verification(user_id)
    if not verification or not verification.verified_at:
        # Никогда не проходил верификацию
        return True, 'call_block'
    
    days_since = (datetime.now() - verification.verified_at).days
    if days_since >= VERIFY_INTERVAL_DAYS:
        # Прошло 30+ дней — требуем новую верификацию
        return True, 'call_block'
    
    # Верификация была менее 30 дней назад — не требуем повторно
    return False, ''


async def require_phone_verification(
    callback: CallbackQuery,
    state: FSMContext,
    worker,
    order_id: int
) -> bool:
    """
    Проверяет необходимость верификации перед взятием заявки.
    Возвращает True — верификация не нужна (продолжать обычный флоу).
    Возвращает False — запустил флоу верификации, основной флоу нужно прервать.
    """
    need, reason = await _need_verification(worker.id, worker.call_block)
    
    # Если call_block установлен, но верификация свежая — снимаем блокировку
    if worker.call_block and not need:
        await db.clear_worker_call_block(worker.id)
        return True
    
    if not need:
        return True

    # Сохраняем данные для продолжения после верификации
    data = await state.get_data()
    await state.update_data(
        phone_verify_order_id=order_id,
        phone_verify_reason=reason,
        SearchOrderFor=data.get('SearchOrderFor', 'myself'),
        FriendID=data.get('FriendID'),
        phone_verify_signer_tg_id=callback.from_user.id,
    )
    await state.set_state('PhoneVerification_Enter')

    # Всегда показываем сообщение о call_block
    intro = txt.phone_verify_call_block()

    await callback.answer()
    await callback.message.edit_text(
        text=intro + '\n\n' + txt.phone_verify_enter_phone()
    )
    return False


@router.message(Worker(), F.text, StateFilter('PhoneVerification_Enter'))
async def handle_phone_input(message: Message, state: FSMContext) -> None:
    """Обработать ввод номера телефона при верификации."""
    phone = normalize_phone_number(message.text)
    if not phone:
        await message.answer(text=txt.phone_verify_phone_error())
        return

    user = await db.get_user(tg_id=message.from_user.id)

    code = str(random.randint(1000, 9999))
    hashed = create_code_hash(code)

    await db.upsert_phone_verification(
        user_id=user.id,
        code_hash=hashed['hash'],
        salt=hashed['salt'],
        pending_phone=phone
    )

    sms_text = SMS_TEMPLATE.format(code=code)
    await send_sms_with_api(
        phone_number=phone.lstrip('+'),
        message_text=sms_text,
        tg_id=message.from_user.id
    )

    await state.set_state('PhoneVerification_Code')
    await message.answer(text=txt.phone_verify_sms_sent(phone=phone))


@router.message(Worker(), F.text, StateFilter('PhoneVerification_Code'))
async def handle_sms_code(message: Message, state: FSMContext) -> None:
    """Обработать ввод SMS-кода верификации."""
    user = await db.get_user(tg_id=message.from_user.id)
    verification = await db.get_phone_verification(user.id)

    if not verification or not verification.code_hash:
        await state.clear()
        await message.answer(text=txt.phone_verify_code_error())
        return

    if not check_code(
        salt=verification.salt,
        hashed_code=verification.code_hash,
        entered_code=message.text.strip()
    ):
        await message.answer(text=txt.phone_verify_code_error())
        return

    # Сохраняем phone до confirm (он обнулит pending_phone)
    verified_phone = verification.pending_phone

    await db.confirm_phone_verification(user.id)

    # Обновляем телефон пользователя в User и DataForSecurity
    if verified_phone:
        await db.update_user_phone(user.id, verified_phone)
        
        # Также обновляем реальный номер для охраны
        real_data = await db.get_user_real_data_by_id(user_id=user.id)
        if real_data:
            await db.update_data_for_security(
                tg_id=user.tg_id,
                phone_number=verified_phone,
                first_name=real_data.first_name,
                last_name=real_data.last_name,
                middle_name=real_data.middle_name
            )

    # Снимаем call_block если был
    if user.call_block:
        await db.clear_worker_call_block(user.id)

    # Отправляем обновлённый номер партнёру РР
    if verified_phone and user.inn:
        try:
            await send_phone_to_pp(worker_inn=user.inn, phone=verified_phone)
        except Exception as e:
            logging.warning(f'[phone_verify] Ошибка отправки номера партнёру РР: {e}')

    data = await state.get_data()
    order_id = data.get('phone_verify_order_id')
    search_order_for = data.get('SearchOrderFor', 'myself')
    friend_id = data.get('FriendID')
    signer_tg_id = data.get('phone_verify_signer_tg_id', message.from_user.id)

    await state.clear()
    await message.answer(text=txt.phone_verify_success())

    if order_id:
        await _complete_order_application(
            message=message,
            order_id=order_id,
            user=user,
            search_order_for=search_order_for,
            friend_id=friend_id,
            signer_tg_id=signer_tg_id,
        )


async def _complete_order_application(
    message: Message,
    order_id: int,
    user,
    search_order_for: str,
    friend_id,
    signer_tg_id: int,
) -> None:
    """Завершить запись на заявку после успешной верификации телефона."""
    try:
        order = await db.get_order(order_id=order_id)
        order_shift = f"{order.date} {'день' if order.day_shift else 'ночь'}"

        if search_order_for == 'myself' or not friend_id:
            worker_id = user.id
            order_from_friend = False
        else:
            friend = await db.get_user_by_id(user_id=friend_id)
            who_signed = user
            await db.set_order_for_friend_log(
                order_id=order_id,
                who_signed=who_signed.id,
                who_signed_tg_id=signer_tg_id,
                friend_id=friend.id,
                friend_tg_id=friend.tg_id
            )
            worker_id = friend_id
            order_from_friend = True

        worker_dates = await db.get_worker_dates(worker_id=worker_id)
        if order_shift in worker_dates:
            await message.answer(text=txt.has_date(date_time=order_shift))
            return

        applied = await db.set_application(
            order_id=order_id,
            worker_id=worker_id,
            order_from_friend=order_from_friend
        )
        if applied == 'error':
            await message.answer(text=txt.no_respond_sent())
            return

        # 'ok' or 'duplicate' both mean the application exists
        await message.answer(text=txt.send_respond())

        if applied == 'ok':
            applications_count = await db.get_applications_count_by_order_id(order_id=order_id)
            if applications_count == order.workers:
                managers = await db.get_managers_tg_id()
                directors = await db.get_directors_tg_id()
                recipients = list(managers) + list(directors)
                for manager in recipients:
                    try:
                        await message.bot.send_message(
                            chat_id=manager,
                            text=await txt.notification_by_order(
                                order_id=order_id,
                                customer_id=order.customer_id,
                                date=order.date,
                                day_shift=order.day_shift,
                                night_shift=order.night_shift,
                                workers_count=order.workers
                            )
                        )
                    except Exception:
                        pass

    except Exception as e:
        await message.answer(text=txt.no_respond_sent())
        logging.exception(f'\n\n{e}')
