import logging
import os
import re
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

import database as db
import texts as txt
from API.fin.receipt_payment import create_receipt_payment
from API.fin.workers import fin_get_worker
from config_reader import config
from utils.document_storage import (
    download_and_save_receipt,
    save_act_pdf,
    save_contract_pdf,
    save_receipt_image,
    save_receipt_txt,
)
from utils.max_delivery import send_max_message
from utils.organizations import orgs_dict, orgs_inn


_FONT_REGISTERED = False
_CONTRACT_TITLE = 'Договор оказания услуг'
_ACT_TITLE = 'Акт выполненных работ'


def _normalize_card(value: str | None) -> str:
    return ''.join(ch for ch in (value or '') if ch.isdigit())


def _register_fonts() -> str:
    global _FONT_REGISTERED
    font_name = 'Helvetica'
    if _FONT_REGISTERED:
        return 'DejaVuSerif'

    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif.ttf')
        bold_path = os.path.join(project_root, 'static', 'fonts', 'DejaVuSerif-Bold.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSerif', font_path))
        pdfmetrics.registerFont(TTFont('DejaVuSerif-Bold', bold_path))
        _FONT_REGISTERED = True
        font_name = 'DejaVuSerif'
    except Exception as e:
        logging.warning(f'[payout_flow] Не удалось зарегистрировать шрифты PDF: {e}')
    return font_name


def _build_pdf(title: str, lines: list[str]) -> bytes:
    font_name = _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=48)
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.fontName = 'DejaVuSerif-Bold' if font_name == 'DejaVuSerif' else font_name
    body_style = styles['BodyText']
    body_style.fontName = font_name
    body_style.leading = 16
    body_style.spaceAfter = 10

    story = [Paragraph(title, title_style), Spacer(1, 12)]
    for line in lines:
        story.append(Paragraph(line.replace('\n', '<br/>'), body_style))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _worker_label(last_name: str, first_name: str, middle_name: str) -> str:
    first_initial = f'{first_name[:1]}.' if first_name else ''
    middle_initial = f'{middle_name[:1]}.' if middle_name else ''
    return f'{last_name} {first_initial}{middle_initial}'.strip()


def _clean_card(card: str | None) -> str | None:
    if not card:
        return None
    digits = re.sub(r'\D', '', card)
    return digits[:16] if digits else None


async def get_worker_pin_context(user_id: int) -> tuple[db.User | None, db.DataForSecurity | None, str]:
    worker = await db.get_user_by_id(user_id=user_id)
    security = await db.get_user_real_data_by_id(user_id=user_id)
    birthday = ''
    if worker and worker.api_id:
        worker_fin = await fin_get_worker(worker.api_id)
        birthday = (worker_fin or {}).get('birthday') or ''
    return worker, security, birthday


def build_receipt_service_name(worker: db.User | None) -> str:
    if not worker:
        return 'Услуги по подбору персонала'
    short_name = _worker_label(worker.last_name or '', worker.first_name or '', worker.middle_name or '')
    value = f'Услуги по подбору персонала для ИП {short_name}'
    return value[:256]


async def build_act_service_name(act) -> str:
    if not act:
        return 'Услуга самозанятого'
    if act.order_id:
        order = await db.get_order(order_id=act.order_id)
        if order:
            description = (order.job_name or 'оказанию услуг').strip()
            return f'Услуга самозанятого по {description}, заявка № {order.id}'
    return f'Услуга самозанятого, акт № {act.id}'


async def create_contract_documents(
    user_id: int,
    *,
    order_id: int | None = None,
    wallet_payment_id: int | None = None,
    act_date: str,
) -> list:
    worker, security, _birthday = await get_worker_pin_context(user_id)
    if not worker or not security:
        return []

    contracts = await db.create_contracts_for_all_orgs(
        user_id=user_id,
        order_id=order_id,
        wallet_payment_id=wallet_payment_id,
    )
    fio = _worker_label(security.last_name, security.first_name, security.middle_name)
    for contract in contracts:
        pdf_bytes = _build_pdf(
            _CONTRACT_TITLE,
            [
                f'Номер договора: {contract.number}',
                f'Дата формирования: {act_date}',
                'Единый шаблон гражданско-правового договора.',
                'Документ сформирован автоматически в системе Алгоритм Плюс.',
            ],
        )
        file_path = await save_contract_pdf(
            pdf_content=pdf_bytes,
            last_name=security.last_name,
            first_name=security.first_name,
            middle_name=security.middle_name,
            inn=worker.inn,
            act_date=act_date,
            contract_id=contract.id,
        )
        await db.set_contract_file_path(contract_id=contract.id, file_path=file_path)
    return contracts


async def ensure_act_pdf(act_id: int) -> str | None:
    act = await db.get_worker_act(act_id=act_id)
    if not act:
        return None
    worker, security, _birthday = await get_worker_pin_context(act.worker_id)
    if not worker or not security:
        return None
    if act.file_path and os.path.exists(act.file_path):
        return act.file_path

    fio = _worker_label(security.last_name, security.first_name, security.middle_name)
    service_name = await build_act_service_name(act)
    pdf_bytes = _build_pdf(
        _ACT_TITLE,
        [
            f'Акт № {act.id}',
            f'Исполнитель: {fio}',
            f'ИНН исполнителя: {worker.inn}',
            f'Услуга: {service_name}',
            f'Юридическое лицо: {orgs_dict.get(act.legal_entity_id, act.legal_entity_id)}',
            f'Вознаграждение: {act.amount} ₽',
            f'Дата акта: {act.date}',
            f'Статус: {act.status}',
            f'Карта на момент подписания: {act.card_snapshot or "не указана"}',
        ],
    )
    file_path = await save_act_pdf(
        pdf_content=pdf_bytes,
        last_name=security.last_name,
        first_name=security.first_name,
        middle_name=security.middle_name,
        inn=worker.inn,
        act_date=act.date,
        act_id=act.id,
    )
    await db.set_worker_act_file_path(act_id=act.id, file_path=file_path)
    return file_path


async def send_receipt_instruction_tg(bot: Bot, worker_tg_id: int, act_id: int) -> None:
    import keyboards.inline as ikb

    act = await db.get_worker_act(act_id=act_id)
    if not act:
        return
    worker = await db.get_user_by_id(user_id=act.worker_id)
    if not worker:
        return
    service_name = await build_act_service_name(act)
    inn = orgs_inn.get(act.legal_entity_id, '')
    act_pdf_path = await ensure_act_pdf(act_id=act_id)
    if act_pdf_path and os.path.exists(act_pdf_path):
        try:
            with open(act_pdf_path, 'rb') as f:
                await bot.send_document(
                    chat_id=worker_tg_id,
                    document=BufferedInputFile(f.read(), filename=os.path.basename(act_pdf_path)),
                    caption='📄 Акт',
                )
        except Exception as e:
            logging.exception(f'[payout_flow] Не удалось отправить PDF акта: {e}')
    await bot.send_message(
        chat_id=worker_tg_id,
        text=txt.receipt_instruction().format(amount=act.amount, service_name=service_name, inn=inn),
        parse_mode=ParseMode.HTML,
        reply_markup=ikb.receipt_copy_keyboard(service_name=service_name, inn=inn, amount=act.amount),
    )


async def send_receipt_instruction_max(worker_max_id: int, act_id: int) -> None:
    if not config.max_bot_token:
        return
    from maxapi import Bot as MaxBot
    from maxapi.enums.parse_mode import ParseMode as MaxParseMode

    act = await db.get_worker_act(act_id=act_id)
    if not act:
        return
    worker = await db.get_user_by_id(user_id=act.worker_id)
    if not worker:
        return
    service_name = await build_act_service_name(act)
    inn = orgs_inn.get(act.legal_entity_id, '')
    max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
    try:
        await send_max_message(
            max_bot,
            user_id=worker_max_id,
            chat_id=getattr(worker, 'max_chat_id', 0) or None,
            text=txt.receipt_instruction_no_copy(service_name=service_name, inn=inn, amount=act.amount),
            parse_mode=MaxParseMode.HTML,
        )
        await send_max_message(
            max_bot,
            user_id=worker_max_id,
            chat_id=getattr(worker, 'max_chat_id', 0) or None,
            text='📋 Отправьте ссылку на чек или фото QR-кода:',
            parse_mode=MaxParseMode.HTML,
        )
    finally:
        await max_bot.close_session()


async def create_and_send_wallet_payment_act(
    *,
    bot: Bot | None,
    worker_id: int,
    wallet_payment_id: int,
    org_id: int,
    amount: str,
    date: str,
) -> db.WorkerAct | None:
    worker, security, birthday = await get_worker_pin_context(worker_id)
    if not worker or not security:
        return None

    card_snapshot = _clean_card(worker.card)
    act = await db.create_worker_act(
        worker_id=worker_id,
        legal_entity_id=org_id,
        amount=amount,
        date=date,
        wallet_payment_id=wallet_payment_id,
        card_snapshot=card_snapshot,
    )
    await ensure_act_pdf(act.id)
    await db.update_wallet_payment_status(wp_id=wallet_payment_id, status='ACT_SENT')

    from handlers.user.sign_act import send_act_to_worker, send_act_to_worker_max

    passport_number = (security.passport_number or '')
    if worker.tg_id and bot:
        await send_act_to_worker(
            bot=bot,
            worker_tg_id=worker.tg_id,
            act_id=act.id,
            amount=amount,
            date=date,
            inn=worker.inn or '',
            passport_number=passport_number,
            birthday=birthday,
            card_snapshot=card_snapshot,
            worker_max_id=worker.max_id or 0,
        )
    if worker.max_id:
        await send_act_to_worker_max(
            worker_max_id=worker.max_id,
            act_id=act.id,
            amount=amount,
            date=date,
            inn=worker.inn or '',
            passport_number=passport_number,
            birthday=birthday,
            card_snapshot=card_snapshot,
            worker_tg_id=worker.tg_id or 0,
        )
    return act


async def refund_wallet_payment(wallet_payment_id: int) -> bool:
    wallet_payment = await db.get_wallet_payment(wp_id=wallet_payment_id)
    if not wallet_payment or wallet_payment.refund:
        return False
    worker = await db.get_user_by_id(user_id=wallet_payment.worker.user_id)
    if not worker:
        return False
    new_balance = str(Decimal(worker.balance or '0') + Decimal(wallet_payment.amount))
    updated = await db.update_worker_balance(worker_id=worker.id, new_balance=new_balance)
    if updated:
        await db.update_wallet_payment_status(wp_id=wallet_payment_id, status='REFUSED')
    return updated


async def _notify_accountants_act_refused(worker, amount: str) -> None:
    if not config.bot_token:
        return
    accountants = await db.get_accountants_tg_id()
    if not accountants:
        return
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for tg_id in accountants:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text=txt.act_refused_by_worker(
                        full_name=f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip(),
                        amount=amount,
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logging.exception(f'[payout_flow] accountant refusal notify error: {e}')


async def _notify_accountants_receipt_ready(worker, amount: str) -> None:
    if not config.bot_token:
        return
    accountants = await db.get_accountants_tg_id()
    if not accountants:
        return
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for tg_id in accountants:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text=txt.receipt_added_by_worker(
                        full_name=f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip(),
                        amount=amount,
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logging.exception(f'[payout_flow] accountant receipt notify error: {e}')


async def save_receipt_documents(
        *,
        receipt,
        worker,
        security,
        act_date: str,
        receipt_url: str,
        screenshot_bytes: bytes | None = None,
        screenshot_extension: str = 'jpg',
) -> None:
    txt_path = await save_receipt_txt(
        receipt_url=receipt_url,
        last_name=security.last_name,
        first_name=security.first_name,
        middle_name=security.middle_name,
        inn=worker.inn,
        act_date=act_date,
        receipt_id=receipt.id,
    )
    await db.set_receipt_file_path(receipt_id=receipt.id, file_path=txt_path)
    await download_and_save_receipt(
        receipt_url=receipt_url,
        last_name=security.last_name,
        first_name=security.first_name,
        middle_name=security.middle_name,
        inn=worker.inn,
        act_date=act_date,
        receipt_id=receipt.id,
    )
    if screenshot_bytes:
        await save_receipt_image(
            image_content=screenshot_bytes,
            last_name=security.last_name,
            first_name=security.first_name,
            middle_name=security.middle_name,
            inn=worker.inn,
            act_date=act_date,
            receipt_id=receipt.id,
            extension=screenshot_extension,
        )


def get_wallet_payment_receipt_status(wallet_payment_status: str, act_status: str, has_receipt: bool, receipt_url: str | None = None) -> str:
    if act_status == 'refused':
        return 'refused'
    if wallet_payment_status in ('inPayment', 'paid', 'RR_CREATED'):
        return 'sent'
    if has_receipt and (receipt_url or '').strip():
        return 'ready'
    return 'missing'


async def _notify_accountants_wallet_payment_issue(worker, amount: str, payment_name: str, *, conflict: bool) -> None:
    if not config.bot_token:
        return
    accountants = await db.get_accountants_tg_id()
    if not accountants:
        return
    text = (
        txt.workers_skipped_conflict(
            payment_name=payment_name,
            skipped=[{
                'full_name': f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip(),
                'inn': worker.inn,
                'amount': amount,
            }],
        )
        if conflict else
        txt.workers_skipped_no_card(
            payment_name=payment_name,
            skipped=[{
                'full_name': f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip(),
                'inn': worker.inn,
                'amount': amount,
            }],
        )
    )
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for tg_id in accountants:
            try:
                await bot.send_message(chat_id=tg_id, text=text, parse_mode=ParseMode.HTML)
            except Exception as e:
                logging.exception(f'[payout_flow] accountant notify error: {e}')


async def send_receipt_payment_to_rr(act_id: int) -> dict:
    act = await db.get_worker_act(act_id=act_id)
    if not act:
        return {'success': False, 'message': 'Акт не найден'}

    worker, _security, _birthday = await get_worker_pin_context(act.worker_id)
    if not worker:
        return {'success': False, 'message': 'Исполнитель не найден'}

    receipt = await db.get_receipt_by_act(act_id=act_id)
    if not receipt or not (receipt.url or '').strip():
        return {'success': False, 'message': 'Чек отсутствует'}

    if not act.card_snapshot:
        return {'success': False, 'message': 'Не зафиксирована карта для выплаты'}

    rr_worker = await fin_get_worker(worker.api_id) if worker.api_id else None
    rr_card = _normalize_card((rr_worker or {}).get('bankcardNumber') or (rr_worker or {}).get('bankcard_number'))
    act_card = _normalize_card(act.card_snapshot)
    if not rr_card or rr_card != act_card:
        if act.wallet_payment_id:
            await db.update_wallet_payment_status(wp_id=act.wallet_payment_id, status='ERROR')
        await _notify_accountants_wallet_payment_issue(
            worker,
            act.amount,
            payment_name=f'из начислений №{act.wallet_payment_id or act.id}',
            conflict=bool(rr_card and rr_card != act_card),
        )
        return {
            'success': False,
            'message': (
                'Выплата не отправлена: обнаружено расхождение платёжных данных. Средства переведены в «Начисления».'
                if rr_card else
                'Выплата не отправлена: в РР отсутствует способ получения выплаты. Средства переведены в «Начисления».'
            ),
        }

    payout = await create_receipt_payment(
        receipt_url=receipt.url,
        inn=worker.inn,
        amount=act.amount,
        card_number=act.card_snapshot,
        org_id=act.legal_entity_id,
        worker_id=worker.id,
        act_id=act.id,
    )
    if payout and payout.get('success'):
        if act.wallet_payment_id:
            await db.update_wallet_payment_status(wp_id=act.wallet_payment_id, status='RR_CREATED')
        return {'success': True, 'message': 'Чек принят и выплата отправлена в РР'}
    return {'success': False, 'message': 'Чек сохранён, но выплату в РР создать не удалось'}


async def complete_receipt_flow(act_id: int, receipt_url: str) -> dict:
    act = await db.get_worker_act(act_id=act_id)
    if not act:
        return {'success': False, 'message': 'Акт не найден'}

    worker, security, _birthday = await get_worker_pin_context(act.worker_id)
    if not worker or not security:
        return {'success': False, 'message': 'Исполнитель не найден'}

    receipt = await db.get_receipt_by_act(act_id=act_id)
    if receipt is None:
        receipt = await db.create_receipt(act_id=act_id, worker_id=worker.id, url=receipt_url)
    elif receipt.url != receipt_url:
        await db.update_receipt_url(receipt_id=receipt.id, url=receipt_url)
        receipt = await db.get_receipt(receipt_id=receipt.id)

    await save_receipt_documents(
        receipt=receipt,
        worker=worker,
        security=security,
        act_date=act.date,
        receipt_url=receipt_url,
    )

    if act.wallet_payment_id:
        await db.update_wallet_payment_status(wp_id=act.wallet_payment_id, status='RECEIPT_READY')
    await _notify_accountants_receipt_ready(worker, act.amount)
    logging.info(f'[acts] receipt saved act={act.id} worker={worker.id} source=worker_link')
    return {'success': True, 'message': txt.receipt_saved_for_review()}
