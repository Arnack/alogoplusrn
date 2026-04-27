"""Флоу подписания / отклонения акта выполненных работ и сбора чека для Max бота."""
import re
import logging
from decimal import Decimal

from maxapi import Router, F
from maxapi.types import MessageCreated, MessageCallback
from maxapi.context import MemoryContext
from maxapi.enums.parse_mode import ParseMode

from max_worker_bot.keyboards import worker_keyboards as kb
from max_worker_bot.states import ActStates, ReceiptStates
from utils.contract_pin import choose_pin, verify_pin
from utils.max_delivery import remember_dialog_from_event
from utils.scheduler import cancel_act_auto_sign
import database as db
import texts.worker as txt
from utils.payout_flow import (
    _notify_accountants_act_refused,
    complete_receipt_flow,
    ensure_act_pdf,
    get_worker_pin_context,
    refund_wallet_payment,
    send_receipt_instruction_max,
)

# Домены чеков «Мой налог»
_RECEIPT_URL_RE = re.compile(r'https?://(lknpd\.nalog\.ru|check\.nalog\.ru)/\S+')

router = Router()
logger = logging.getLogger(__name__)


async def _resolve_receipt_act_id_max(event, context: MemoryContext) -> int | None:
    data = await context.get_data()
    act_id = data.get('ReceiptActID')
    if act_id:
        return act_id
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        return None
    act = await db.get_latest_receipt_required_act(worker_id=worker.id)
    return act.id if act else None


@router.message_callback(F.callback.payload.startswith('SignAct:'))
async def request_act_pin(event: MessageCallback, context: MemoryContext):
    """Нажал «Подписать» — запрашиваем PIN."""
    remember_dialog_from_event(event)
    act_id = int(event.callback.payload.split(':')[1])
    act = await db.get_worker_act(act_id=act_id)
    if not act or act.status not in ('pending', 'sent'):
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text='ℹ️ Акт уже обработан.',
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await event.message.answer(text='ℹ️ Акт уже обработан.', parse_mode=ParseMode.HTML)
        return

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await event.message.answer(text=txt.no_worker(), parse_mode=ParseMode.HTML)
        return
    worker, security, birthday = await get_worker_pin_context(act.worker_id)
    passport_number = security.passport_number if security else ''

    pin_type, _val, hint = choose_pin(
        inn=(worker.inn if worker else '') or '',
        birthday=birthday,
        passport_number=passport_number or '',
    )
    await context.update_data(SignActID=act_id, SignPinTypeAct=pin_type)
    await context.set_state(ActStates.pin_input)

    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=f'🔐 Введите {hint} для подписания акта:',
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await event.message.answer(
            text=f'🔐 Введите {hint} для подписания акта:',
            parse_mode=ParseMode.HTML,
        )


@router.message_created(ActStates.pin_input, F.message.body.text)
async def verify_act_pin(event: MessageCreated, context: MemoryContext):
    """Проверяет PIN и подписывает акт."""
    remember_dialog_from_event(event)
    data = await context.get_data()
    act_id = data.get('SignActID')
    pin_type = data.get('SignPinTypeAct', 'inn')

    if not act_id:
        await context.clear()
        return

    act = await db.get_worker_act(act_id=act_id)
    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await context.clear()
        return
    _worker, security, birthday = await get_worker_pin_context(act.worker_id if act else worker.id)
    passport_number = security.passport_number if security else ''

    if not verify_pin(
        pin_type=pin_type,
        entered=event.message.body.text,
        inn=worker.inn or '',
        birthday=birthday,
        passport_number=passport_number or '',
    ):
        await event.message.answer(text=txt.act_sign_pin_error(), parse_mode=ParseMode.HTML)
        return

    await context.clear()
    cancel_act_auto_sign(act_id=act_id)
    await db.update_worker_act_status(act_id=act_id, status='signed')
    await ensure_act_pdf(act_id=act_id)
    await event.message.answer(text=txt.act_signed(), parse_mode=ParseMode.HTML)
    await send_receipt_instruction_max(worker_max_id=event.from_user.user_id, act_id=act_id)
    await context.update_data(ReceiptActID=act_id)
    await context.set_state(ReceiptStates.url_input)


@router.message_callback(F.callback.payload.startswith('RefuseAct:'))
async def refuse_act(event: MessageCallback, context: MemoryContext):
    """Нажал «Отказаться» — фиксируем отказ."""
    remember_dialog_from_event(event)
    act_id = int(event.callback.payload.split(':')[1])
    act = await db.get_worker_act(act_id=act_id)
    if not act or act.status not in ('pending', 'sent'):
        try:
            await event.bot.edit_message(
                message_id=event.message.body.mid,
                text='ℹ️ Акт уже обработан.',
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await event.message.answer(text='ℹ️ Акт уже обработан.', parse_mode=ParseMode.HTML)
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
    try:
        await event.bot.edit_message(
            message_id=event.message.body.mid,
            text=txt.act_refused(),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        await event.message.answer(text=txt.act_refused(), parse_mode=ParseMode.HTML)
    await context.clear()


# ── Обработчики для чека из «Мой налог» ────────────────────────────────────────

@router.message_created(ReceiptStates.url_input, F.message.body.text)
async def save_receipt_url(event: MessageCreated, context: MemoryContext):
    """Принимает ссылку на чек из «Мой налог» и сохраняет в БД."""
    remember_dialog_from_event(event)
    url = (event.message.body.text or '').strip()

    if not _RECEIPT_URL_RE.match(url):
        await event.message.answer(
            text='❗ Ссылка не похожа на чек из «Мой налог». Пожалуйста, проверьте и попробуйте снова:',
            parse_mode=ParseMode.HTML,
        )
        return

    act_id = await _resolve_receipt_act_id_max(event, context)

    if not act_id:
        await context.clear()
        return

    worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
    if not worker:
        await context.clear()
        return

    result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
    await context.clear()
    await event.message.answer(
        text=result['message'],
        parse_mode=ParseMode.HTML,
    )


@router.message_created(F.message.body.text)
async def save_receipt_url_without_state(event: MessageCreated, context: MemoryContext):
    remember_dialog_from_event(event)
    url = (event.message.body.text or '').strip()
    if not _RECEIPT_URL_RE.match(url):
        return
    act_id = await _resolve_receipt_act_id_max(event, context)
    if not act_id:
        return
    result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
    await context.clear()
    await event.message.answer(text=result['message'], parse_mode=ParseMode.HTML)


@router.message_created(ReceiptStates.url_input, F.message.body.attachments)
async def save_receipt_from_qr(event: MessageCreated, context: MemoryContext):
    """Принимает фото QR-кода и извлекает из него ссылку на чек."""
    remember_dialog_from_event(event)
    from utils.qr_reader import decode_qr_from_bytes, extract_receipt_url

    act_id = await _resolve_receipt_act_id_max(event, context)

    if not act_id:
        await context.clear()
        return

    # Ищем фото среди вложений
    photo_url = None
    for attachment in event.message.body.attachments:
        if attachment.get('type') == 'photo':
            photo_url = attachment.get('photo', {}).get('url') or attachment.get('url')
            break

    if not photo_url:
        await event.message.answer(
            text='❗ Не удалось найти фото на вложении. Отправьте фото ещё раз:',
            parse_mode=ParseMode.HTML,
        )
        return

    # Скачиваем фото
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_url) as resp:
                image_bytes = await resp.read()

        raw = decode_qr_from_bytes(image_bytes)
        if not raw:
            await event.message.answer(
                text='❗ QR-код на фото не обнаружен. Попробуйте сделать более чёткий скриншот:',
                parse_mode=ParseMode.HTML,
            )
            return

        url = extract_receipt_url(raw)
        if not url:
            await event.message.answer(
                text='❗ QR-код не содержит ссылку на чек из «Мой налог». Отправьте ссылку текстом:',
                parse_mode=ParseMode.HTML,
            )
            return

        worker = await db.get_worker_by_max_id(max_id=event.from_user.user_id)
        if not worker:
            await context.clear()
            return

        result = await complete_receipt_flow(act_id=act_id, receipt_url=url)
        await context.clear()
        await event.message.answer(
            text=result['message'],
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        logging.exception(f'[max] save_receipt_from_qr: {e}')
        await event.message.answer(
            text='❗ Произошла ошибка при обработке фото. Попробуйте отправить ссылку текстом:',
            parse_mode=ParseMode.HTML,
        )


@router.message_created(F.message.body.attachments)
async def save_receipt_from_qr_without_state(event: MessageCreated, context: MemoryContext):
    act_id = await _resolve_receipt_act_id_max(event, context)
    if not act_id:
        return
    await save_receipt_from_qr(event, context)
