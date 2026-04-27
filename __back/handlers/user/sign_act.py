"""Флоу подписания / отклонения акта и сбора чека (Telegram)."""
import logging
import re
from decimal import Decimal
from io import BytesIO
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.exceptions import AiogramError

from filters import Worker
from utils.contract_pin import choose_pin, verify_pin
from utils.scheduler import schedule_act_auto_sign, cancel_act_auto_sign
import keyboards.inline as ikb
import database as db
import texts as txt
from utils.max_delivery import send_max_message
from utils.payout_flow import (
    _notify_accountants_act_refused,
    complete_receipt_flow,
    ensure_act_pdf,
    get_worker_pin_context,
    refund_wallet_payment,
    send_receipt_instruction_tg,
)




router = Router()
router.callback_query.filter(Worker())
_RECEIPT_URL_RE = re.compile(r'https?://(lknpd\.nalog\.ru|check\.nalog\.ru)/\S+')


async def _resolve_receipt_act_id_tg(message: Message, state: FSMContext) -> int | None:
    data = await state.get_data()
    act_id = data.get('ReceiptActID')
    if act_id:
        return act_id
    worker = await db.get_user(tg_id=message.from_user.id)
    if not worker:
        return None
    act = await db.get_latest_receipt_required_act(worker_id=worker.id)
    return act.id if act else None


@router.callback_query(F.data.startswith('SignAct:'))
async def request_act_pin(callback: CallbackQuery, state: FSMContext):
    """Нажал «Подписать» — запрашиваем PIN."""
    await callback.answer()
    act_id = int(callback.data.split(':')[1])
    act = await db.get_worker_act(act_id=act_id)
    if not act or act.status not in ('pending', 'sent'):
        await callback.message.edit_text('ℹ️ Акт уже обработан.')
        return

    worker, security, birthday = await get_worker_pin_context(act.worker_id)
    passport_number = security.passport_number if security else ''
    pin_type, _val, hint = choose_pin(
        inn=(worker.inn if worker else '') or '',
        birthday=birthday,
        passport_number=passport_number or '',
    )
    await state.update_data(SignActID=act_id, SignPinTypeAct=pin_type)
    await callback.message.edit_text(
        text=f'🔐 Введите {hint} для подписания акта:',
        reply_markup=None,
    )
    await state.set_state('SignActPinInput')


@router.message(F.text, StateFilter('SignActPinInput'))
async def verify_act_pin(message: Message, state: FSMContext):
    """Проверяет PIN и подписывает акт."""
    data = await state.get_data()
    act_id = data.get('SignActID')
    pin_type = data.get('SignPinTypeAct', 'inn')

    if not act_id:
        await state.clear()
        return

    act = await db.get_worker_act(act_id=act_id)
    if not act:
        await state.clear()
        return
    worker, security, birthday = await get_worker_pin_context(act.worker_id)
    passport_number = security.passport_number if security else ''
    if not verify_pin(
        pin_type=pin_type,
        entered=message.text,
        inn=(worker.inn if worker else '') or '',
        birthday=birthday,
        passport_number=passport_number or '',
    ):
        await message.answer(text=txt.act_sign_pin_error())
        return

    await state.clear()
    cancel_act_auto_sign(act_id=act_id)
    await db.update_worker_act_status(act_id=act_id, status='signed')
    await ensure_act_pdf(act_id=act_id)
    await message.answer(text=txt.act_signed())
    await send_receipt_instruction_tg(bot=message.bot, worker_tg_id=message.from_user.id, act_id=act_id)
    await state.update_data(ReceiptActID=act_id)
    await state.set_state('ReceiptUrlInput')


@router.callback_query(F.data.startswith('RefuseAct:'))
async def refuse_act(callback: CallbackQuery, state: FSMContext):
    """Нажал «Отказаться» — фиксируем отказ."""
    await callback.answer()
    act_id = int(callback.data.split(':')[1])
    act = await db.get_worker_act(act_id=act_id)
    if not act or act.status not in ('pending', 'sent'):
        await callback.message.edit_text('ℹ️ Акт уже обработан.')
        return

    cancel_act_auto_sign(act_id=act_id)
    await db.update_worker_act_status(act_id=act_id, status='refused')
    if act.wallet_payment_id:
        await refund_wallet_payment(wallet_payment_id=act.wallet_payment_id)
    else:
        worker = await db.get_user_by_id(user_id=act.worker_id)
        if worker:
            new_balance = str(Decimal(worker.balance or '0') + Decimal(act.amount or '0'))
            await db.update_worker_balance(worker_id=worker.id, new_balance=new_balance)
    worker = await db.get_user_by_id(user_id=act.worker_id)
    if worker:
        await _notify_accountants_act_refused(worker, act.amount)
    await callback.message.edit_text(text=txt.act_refused())
    await state.clear()


async def send_act_to_worker(
        bot,
        worker_tg_id: int,
        act_id: int,
        amount: str,
        date: str,
        inn: str,
        passport_number: str,
        birthday: str = '',
        card_snapshot: str | None = None,
        worker_max_id: int | None = None,
) -> None:
    """Отправляет акт работнику с кнопками Sign/Refuse и планирует авто-подписание.

    Args:
        card_snapshot: Номер карты на момент подписания акта (п.10 ТЗ)
    """
    from utils.contract_pin import choose_pin
    _pin_type, _val, hint = choose_pin(
        inn=inn,
        birthday=birthday,
        passport_number=passport_number,
    )

    # Сохраняем карту в акт если передана
    if card_snapshot:
        await db.set_worker_act_card_snapshot(act_id=act_id, card_snapshot=card_snapshot)

    await db.update_worker_act_status(act_id=act_id, status='sent')
    try:
        await bot.send_message(
            chat_id=worker_tg_id,
            text=txt.act_accrual_notification(),
        )
        await bot.send_message(
            chat_id=worker_tg_id,
            text=txt.act_sign_request(amount=amount, date=date, pin_hint=hint),
            reply_markup=ikb.act_sign_keyboard(act_id=act_id),
            parse_mode='HTML',
        )
    except Exception:
        pass
    await schedule_act_auto_sign(act_id=act_id, worker_tg_id=worker_tg_id, worker_max_id=worker_max_id)


async def send_act_to_worker_max(
        worker_max_id: int,
        act_id: int,
        amount: str,
        date: str,
        inn: str,
        passport_number: str,
        birthday: str = '',
        card_snapshot: str | None = None,
        worker_tg_id: int | None = None,
) -> None:
    """Отправляет акт работнику в Max бот с кнопками Sign/Refuse.

    Args:
        card_snapshot: Номер карты на момент подписания акта (п.10 ТЗ)
    """
    from utils.contract_pin import choose_pin
    from config_reader import config as cfg
    _pin_type, _val, hint = choose_pin(
        inn=inn,
        birthday=birthday,
        passport_number=passport_number,
    )
    if not cfg.max_bot_token:
        return

    # Сохраняем карту в акт если передана
    if card_snapshot:
        await db.set_worker_act_card_snapshot(act_id=act_id, card_snapshot=card_snapshot)

    try:
        from maxapi import Bot as MaxBot
        from maxapi.enums.parse_mode import ParseMode as MaxParseMode
        from max_worker_bot.keyboards.worker_keyboards import act_sign_keyboard
        worker = await db.get_user_by_id(user_id=act.worker_id)
        max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
        await send_max_message(
            max_bot,
            user_id=worker_max_id,
            chat_id=getattr(worker, 'max_chat_id', 0) or None,
            text=txt.act_accrual_notification(),
            parse_mode=MaxParseMode.HTML,
        )
        await send_max_message(
            max_bot,
            user_id=worker_max_id,
            chat_id=getattr(worker, 'max_chat_id', 0) or None,
            text=txt.act_sign_request(amount=amount, date=date, pin_hint=hint),
            attachments=[act_sign_keyboard(act_id=act_id)],
            parse_mode=MaxParseMode.HTML,
        )
        await max_bot.close_session()
    except Exception:
        pass
    await schedule_act_auto_sign(act_id=act_id, worker_tg_id=worker_tg_id, worker_max_id=worker_max_id)


@router.message(F.text, StateFilter('ReceiptUrlInput'))
async def save_receipt_url(message: Message, state: FSMContext):
    """Принимает ссылку на чек из «Мой налог» и сохраняет в БД."""
    url = (message.text or '').strip()
    act_id = await _resolve_receipt_act_id_tg(message, state)

    if not _RECEIPT_URL_RE.match(url):
        await message.answer(text=txt.receipt_url_invalid())
        return

    if not act_id:
        await state.clear()
        return

    worker = await db.get_user(tg_id=message.from_user.id)
    result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
    await state.clear()
    await message.answer(text=result['message'])


@router.message(F.text.regexp(_RECEIPT_URL_RE))
async def save_receipt_url_without_state(message: Message, state: FSMContext):
    act_id = await _resolve_receipt_act_id_tg(message, state)
    if not act_id:
        return
    result = await complete_receipt_flow(act_id=act_id, receipt_url=(message.text or '').strip())
    await state.clear()
    await message.answer(text=result['message'])


@router.message(F.photo, StateFilter('ReceiptUrlInput'))
async def save_receipt_from_qr(message: Message, state: FSMContext):
    """Принимает фото QR-кода и извлекает из него ссылку на чек."""
    from utils.qr_reader import decode_qr_from_bytes, extract_receipt_url

    act_id = await _resolve_receipt_act_id_tg(message, state)
    if not act_id:
        await state.clear()
        return

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    buf = BytesIO()
    await message.bot.download_file(file.file_path, buf)

    raw = decode_qr_from_bytes(buf.getvalue())
    if not raw:
        await message.answer(text=txt.receipt_qr_not_found())
        return

    url = extract_receipt_url(raw)
    if not url:
        await message.answer(text=txt.receipt_qr_invalid())
        return

    result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
    await state.clear()
    await message.answer(text=result['message'])


@router.message(F.photo)
async def save_receipt_from_qr_without_state(message: Message, state: FSMContext):
    act_id = await _resolve_receipt_act_id_tg(message, state)
    if not act_id:
        return

    from utils.qr_reader import decode_qr_from_bytes, extract_receipt_url

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    buf = BytesIO()
    await message.bot.download_file(file.file_path, buf)

    raw = decode_qr_from_bytes(buf.getvalue())
    if not raw:
        return

    url = extract_receipt_url(raw)
    if not url:
        return

    result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
    await state.clear()
    await message.answer(text=result['message'])


# ── Обработчики кнопок копирования для чека ────────────────────────────────────

@router.callback_query(F.data.startswith('CopyServiceName:'))
async def copy_service_name(callback: CallbackQuery):
    """Обработчик кнопки копирования названия услуги."""
    await callback.answer(
        text=callback.data.split(':', 1)[1],
        show_alert=False,
    )


@router.callback_query(F.data.startswith('CopyInn:'))
async def copy_inn(callback: CallbackQuery):
    """Обработчик кнопки копирования ИНН."""
    await callback.answer(
        text=callback.data.split(':', 1)[1],
        show_alert=False,
    )


@router.callback_query(F.data.startswith('CopyReceiptAmount:'))
async def copy_receipt_amount(callback: CallbackQuery):
    await callback.answer(
        text=callback.data.split(':', 1)[1],
        show_alert=False,
    )


@router.callback_query(F.data == 'ShowReceiptInstruction')
async def show_receipt_instruction(callback: CallbackQuery, state: FSMContext):
    """Повторно показать инструкцию по чеку."""
    await callback.answer()
    data = await state.get_data()
    act_id = data.get('ReceiptActID')
    if act_id:
        await send_receipt_instruction_tg(bot=callback.bot, worker_tg_id=callback.from_user.id, act_id=act_id)


@router.callback_query(F.data == 'ReceiptSent')
async def receipt_sent_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    worker = await db.get_user(tg_id=callback.from_user.id)
    if not worker:
        return
    act = await db.get_latest_receipt_required_act(worker_id=worker.id)
    if not act:
        await callback.message.answer('ℹ️ Нет акта, ожидающего чек.')
        return
    await state.update_data(ReceiptActID=act.id)
    await callback.message.answer(text=txt.request_receipt_url(), parse_mode='HTML')
    await state.set_state('ReceiptUrlInput')


@router.callback_query(F.data == 'ReceiptScreenshot')
async def receipt_screenshot_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    worker = await db.get_user(tg_id=callback.from_user.id)
    if not worker:
        return
    act = await db.get_latest_receipt_required_act(worker_id=worker.id)
    if not act:
        await callback.message.answer('ℹ️ Нет акта, ожидающего чек.')
        return
    await state.update_data(ReceiptActID=act.id)
    await callback.message.answer(text=txt.request_receipt_url(), parse_mode='HTML')
    await state.set_state('ReceiptUrlInput')
