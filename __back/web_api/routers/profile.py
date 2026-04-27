from __future__ import annotations

import base64
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated

from aiogram import Bot
from aiogram.enums import ParseMode
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from API import (
    change_current_organization,
    create_worker_contract,
    sign_contract_by_worker,
    update_worker_bank_card,
)
from API.fin.contracts import fin_ensure_contracts_for_all_orgs, fin_get_worker_contracts_with_pdfs, fin_get_missing_contract_org_ids, fin_get_unsigned_contracts_all_orgs
from API.fin.workers import fin_get_worker
import database as db
import texts as txt
from texts.worker import referral_panel_message_html
from config_reader import config
from database.models import User
from handlers.user.sign_act import send_act_to_worker, send_act_to_worker_max
from keyboards.inline.manager.change_city import confirmation_update_city_manager
from texts import manager as txt_manager
from utils import get_rating
from utils.checking import luhn_check
from utils.loggers import write_worker_wp_log
from utils.contract_pin import choose_pin, verify_pin
from utils.organizations import orgs_contract_template_id, orgs_dict, orgs_id
from utils.refuse_assigned_worker import strip_html_plain
from utils.payout_flow import create_contract_documents
from utils.static_contract import get_static_contract_bytes, STATIC_CONTRACT_FILENAME

from web_api.deps import get_current_worker
from web_api.schemas import (
    AboutPanelOut,
    BankCardUpdateBody,
    ChangeCityBody,
    CreateWalletPaymentBody,
    EnsureContractsBody,
    ErasePersonalDataBody,
    MessageResponse,
    ReferralPackOut,
    SecurityDataUpdateBody,
    UserPublic,
)

router = APIRouter()

TG_BOT_URL = 'https://t.me/Algoritmplus_bot'


def _mask_inn(inn: str) -> str:
    digits = re.sub(r'\D', '', inn or '')
    if len(digits) <= 4:
        return '****'
    return f'{"*" * (len(digits) - 4)}{digits[-4:]}'


@router.get('/me', response_model=UserPublic)
async def users_me(user: Annotated[User, Depends(get_current_worker)]):
    return UserPublic(
        id=user.id,
        tg_id=int(user.tg_id),
        city=user.city,
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        inn_masked=_mask_inn(user.inn),
        block=bool(user.block),
        in_rr=bool(user.api_id),
    )


@router.get('/me/rating')
async def users_me_rating(user: Annotated[User, Depends(get_current_worker)]):
    rating = await get_rating(user_id=user.id)
    return {'rating': rating}


@router.get('/me/about-panel', response_model=AboutPanelOut)
async def about_panel(user: Annotated[User, Depends(get_current_worker)]):
    user_rating = await db.get_user_rating(user_id=user.id)
    if not user_rating:
        await db.set_rating(user_id=user.id)
        user_rating = await db.get_user_rating(user_id=user.id)
    real = await db.get_user_real_data_by_id(user_id=user.id)
    rating = await get_rating(user_id=user.id)

    fio_reg = f'{user.last_name} {user.first_name} {user.middle_name}'.strip()
    if real:
        fio_act = f'{real.last_name} {real.first_name} {real.middle_name}'.strip()
        phone_act = real.phone_number or user.phone_number
    else:
        fio_act = fio_reg
        phone_act = user.phone_number

    bal = (user.balance or '').strip() or '0'
    card_val = (user.card or '').strip() or None

    return AboutPanelOut(
        phone_registry=user.phone_number or '—',
        fio_registry=fio_reg or '—',
        phone_actual=phone_act or '—',
        fio_actual=fio_act or '—',
        card=card_val,
        balance=bal,
        city=user.city or '—',
        rating=rating,
        total_orders=user_rating.total_orders,
        successful_orders=user_rating.successful_orders,
        in_rr=bool(user.api_id),
        api_worker_id=user.api_id if user.api_id else None,
    )


def _normalize_security_phone(raw: str) -> str:
    d = re.sub(r'\D', '', raw or '')
    if len(d) == 10:
        return '+7' + d
    if len(d) == 11 and d[0] == '8':
        return '+7' + d[1:]
    if len(d) == 11 and d[0] == '7':
        return '+' + d
    s = (raw or '').strip()[:25]
    return s if s else '+' + d[:25]


@router.post('/me/security-data', response_model=MessageResponse)
async def update_security_data_web(
    user: Annotated[User, Depends(get_current_worker)],
    body: SecurityDataUpdateBody,
):
    w = await db.get_user_with_security_by_user_id(user.id)
    if not w or not w.security:
        raise HTTPException(400, 'Нет записи данных для охраны. Обратитесь в поддержку.')
    phone = _normalize_security_phone(body.phone)
    ln = body.last_name.strip().capitalize()[:20]
    fn = body.first_name.strip().capitalize()[:20]
    mn = body.middle_name.strip().capitalize()[:20]
    try:
        await db.update_data_for_security_by_user_id(
            user_id=user.id,
            phone_number=phone,
            last_name=ln,
            first_name=fn,
            middle_name=mn,
        )
    except Exception as e:
        logging.exception('update_data_for_security web')
        raise HTTPException(500, txt.update_data_for_security_error()) from e
    return MessageResponse(message=txt.data_for_security_updated())


@router.post('/me/change-city-request', response_model=MessageResponse)
async def request_change_city_web(
    user: Annotated[User, Depends(get_current_worker)],
    body: ChangeCityBody,
):
    worker = await db.get_user_with_security_by_user_id(user.id)
    if not worker or not worker.security:
        raise HTTPException(400, 'Недостаточно данных профиля для запроса смены города')
    new_city = await db.get_city_by_id(city_id=body.city_id)
    if not new_city:
        raise HTTPException(400, 'Город не найден')
    if (worker.city or '').strip() == (new_city.city_name or '').strip():
        raise HTTPException(400, 'Этот город уже указан как текущая локация')

    request_id = await db.set_change_city_request(worker_id=worker.id)
    tok = config.bot_token
    if not tok:
        raise HTTPException(503, 'Уведомление менеджеру недоступно (BOT_TOKEN не задан)')
    managers = await db.get_managers_tg_id()
    directors = await db.get_directors_tg_id()
    recipients = list({*managers, *directors})
    full_name = (
        f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}'.strip()
    )
    text = txt_manager.request_to_change_city_for_manager(
        worker_full_name=full_name,
        old_city=worker.city or '—',
        new_city=new_city.city_name,
    )
    markup = confirmation_update_city_manager(
        new_city_id=body.city_id,
        worker_id=worker.id,
        request_id=request_id,
    )
    try:
        async with Bot(token=tok.get_secret_value()) as bot:
            for chat_id in recipients:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=markup,
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    logging.exception('change_city notify manager %s', chat_id)
    except Exception as e:
        logging.exception('change_city bot')
        raise HTTPException(502, txt.request_to_change_city_error()) from e
    return MessageResponse(message=txt.request_to_change_city_sent())


@router.post('/me/bank-card', response_model=MessageResponse)
async def update_bank_card_web(
    user: Annotated[User, Depends(get_current_worker)],
    body: BankCardUpdateBody,
):
    if not user.api_id:
        raise HTTPException(
            400,
            'Смена карты доступна после регистрации в реестре самозанятых.',
        )
    inn_digits = re.sub(r'\D', '', user.inn or '')
    if len(inn_digits) < 4 or body.inn_last4 != inn_digits[-4:]:
        raise HTTPException(400, txt.contract_inn_error())

    card = re.sub(r'\s', '', body.card)
    if not card.isdigit():
        raise HTTPException(400, txt.card_number_error())
    if not luhn_check(card):
        raise HTTPException(400, txt.luhn_check_error())
    if await db.card_unique(card):
        raise HTTPException(400, txt.card_not_unique_error())
    current = (user.card or '').strip()
    if card == current:
        raise HTTPException(400, txt.same_card_error())

    inn_sign = inn_digits[-4:]
    try:
        for org_id in orgs_id:
            await change_current_organization(org_id=org_id)
            cid = await create_worker_contract(
                api_worker_id=user.api_id,
                contract_id=orgs_contract_template_id[org_id],
            )
            if cid is None:
                raise HTTPException(502, txt.sign_contract_error())
            await change_current_organization(org_id=org_id)
            if not await sign_contract_by_worker(contract_id=cid, sign=inn_sign):
                raise HTTPException(502, txt.sign_contract_error())
    except HTTPException:
        raise
    except Exception as e:
        logging.exception('bank_card sign loop')
        raise HTTPException(502, txt.sign_contract_error()) from e

    await db.update_worker_bank_card(worker_id=user.id, card=card)
    if not await update_worker_bank_card(api_worker_id=user.api_id, bank_card=card):
        raise HTTPException(502, txt.update_card_error())
    return MessageResponse(message=txt.bank_card_updated())


@router.get('/me/referral-pack', response_model=ReferralPackOut)
async def referral_pack(user: Annotated[User, Depends(get_current_worker)]):
    settings = await db.get_settings()
    if not settings:
        raise HTTPException(503, 'Настройки платформы недоступны')
    ref_info = await db.get_referral_info(tg_id=user.tg_id)
    link = f'{TG_BOT_URL}?start=ref_{user.tg_id}'
    msg = referral_panel_message_html(
        link=link,
        bonus=str(settings.bonus),
        shifts=int(settings.shifts),
        friends=int(ref_info[0]),
        completed=int(ref_info[1]),
    )
    return ReferralPackOut(
        link=link,
        bonus=str(settings.bonus),
        shifts=int(settings.shifts),
        friends=int(ref_info[0]),
        completed=int(ref_info[1]),
        message_html=msg,
    )


@router.get('/me/data-erasure-notice', response_model=MessageResponse)
async def data_erasure_notice(_: Annotated[User, Depends(get_current_worker)]):
    return MessageResponse(message=strip_html_plain(txt.erase_worker_info_warning()))


@router.post('/me/erase-personal-data', response_model=MessageResponse)
async def erase_personal_data(
    user: Annotated[User, Depends(get_current_worker)],
    body: ErasePersonalDataBody,
):
    if not body.confirm:
        raise HTTPException(400, 'Подтвердите удаление')
    await db.erase_worker_data(user_id=user.id)
    return MessageResponse(message=strip_html_plain(txt.worker_data_erased()))


_CONTRACTS_ORG_IDS = [392, 393, 480]
_MIN_PAYMENT = Decimal('2600')


@router.post('/me/create-payment', response_model=MessageResponse)
async def create_wallet_payment(
    user: Annotated[User, Depends(get_current_worker)],
    body: CreateWalletPaymentBody,
):
    """Вывод средств с кошелька (аналог CreateWorkerPayment в ТГ боте)."""
    try:
        amount = Decimal(body.amount.replace(',', '.'))
    except InvalidOperation:
        raise HTTPException(400, 'Некорректная сумма')

    if amount < _MIN_PAYMENT:
        raise HTTPException(400, f'Минимальная сумма вывода — {_MIN_PAYMENT:,.0f} ₽')

    balance = await db.get_worker_balance_by_tg_id(tg_id=user.tg_id)
    if amount > balance:
        raise HTTPException(400, 'Сумма превышает баланс')

    wp_id = await db.set_wallet_payment(tg_id=user.tg_id, amount=str(amount))
    if not wp_id:
        raise HTTPException(500, txt.create_payment_error())

    new_balance = str(balance - amount)
    is_updated = await db.update_worker_balance(tg_id=user.tg_id, new_balance=new_balance)
    if not is_updated:
        await db.update_wallet_payment_status(wp_id=wp_id, status='ERROR')
        raise HTTPException(500, txt.create_payment_error())

    write_worker_wp_log(
        message=f'Исполнитель {user.tg_id} | Создал выплату из кошелька №{wp_id} на сумму {amount} рублей (веб)',
    )

    act_date = datetime.strftime(datetime.now(), '%d.%m.%Y')
    contracts = await create_contract_documents(
        user_id=user.id,
        wallet_payment_id=wp_id,
        act_date=act_date,
    )

    tok = config.bot_token
    if tok:
        try:
            async with Bot(token=tok.get_secret_value()) as bot:
                accountants = await db.get_accountants_tg_id()
                for tg_id in accountants:
                    try:
                        await bot.send_message(
                            chat_id=tg_id,
                            text=txt.new_wallet_payment_notification(
                                date=act_date,
                            ),
                        )
                    except Exception:
                        logging.exception('notify accountant %s', tg_id)
        except Exception:
            logging.exception('create_wallet_payment bot notify')

    return MessageResponse(
        message=f'Выплата №{wp_id} создана. Сформировано договоров: {len(contracts)}. После выбора ИП кассиром вам придёт акт.'
    )


@router.get('/me/pending-contracts')
async def pending_contracts(user: Annotated[User, Depends(get_current_worker)]):
    """Возвращает информацию о неподписанных договорах (как в Telegram боте)."""
    if not user.api_id:
        return {'needs_signing': False, 'org_names': []}
    try:
        # Use the same function as Telegram bot - checks for UNSIGNED contracts
        unsigned_contracts = await fin_get_unsigned_contracts_all_orgs(
            worker_id=user.api_id,
            org_template_map=orgs_contract_template_id,
        )
    except Exception as e:
        logging.exception('pending_contracts')
        raise HTTPException(502, 'Не удалось проверить договоры. Попробуйте позже.') from e

    if not unsigned_contracts:
        return {'needs_signing': False, 'org_names': []}

    # Get unique org_ids from unsigned contracts
    unsigned_org_ids = list(set(c.get('org_id') for c in unsigned_contracts if c.get('org_id')))
    org_names = [orgs_dict.get(oid, f'ИП {oid}') for oid in unsigned_org_ids]

    security = await db.get_data_for_security(user.tg_id) if user.tg_id else None
    passport_number = (security.passport_number or '') if security else ''
    worker_fin = await fin_get_worker(user.api_id)
    birthday = (worker_fin or {}).get('birthday') or ''
    pin_type, _pin_value, pin_hint = choose_pin(
        inn=user.inn or '',
        birthday=birthday,
        passport_number=passport_number,
    )
    return {'needs_signing': True, 'org_names': org_names, 'pin_type': pin_type, 'pin_hint': pin_hint}


@router.post('/me/ensure-contracts', response_model=MessageResponse)
async def ensure_contracts(
    user: Annotated[User, Depends(get_current_worker)],
    body: EnsureContractsBody,
):
    """Создаёт и подписывает договоры. Требует подтверждения PIN-кодом."""
    if not user.api_id:
        return MessageResponse(message='ok')

    security = await db.get_data_for_security(user.tg_id) if user.tg_id else None
    passport_number = (security.passport_number or '') if security else ''
    worker_fin = await fin_get_worker(user.api_id)
    birthday = (worker_fin or {}).get('birthday') or ''
    if not verify_pin(body.pin_type, body.pin_value, user.inn or '', birthday, passport_number):
        raise HTTPException(400, txt.contract_inn_error())

    try:
        created_org_ids = await fin_ensure_contracts_for_all_orgs(
            worker_id=user.api_id,
            org_template_map=orgs_contract_template_id,
        )
    except Exception as e:
        logging.exception('ensure_contracts')
        raise HTTPException(502, 'Не удалось проверить договоры. Попробуйте позже.') from e

    if created_org_ids:
        names = ', '.join(orgs_dict.get(oid, str(oid)) for oid in created_org_ids)
        return MessageResponse(message=f'Подписаны договоры: {names}')
    return MessageResponse(message='ok')


@router.get('/me/contracts')
async def get_contracts(user: Annotated[User, Depends(get_current_worker)]):
    """Договоры исполнителя по всем ИП (аналог GetWorkerContracts в ТГ боте)."""
    if not user.api_id:
        raise HTTPException(400, 'Договоры доступны после регистрации в реестре самозанятых.')
    try:
        contracts = await fin_get_worker_contracts_with_pdfs(user.api_id, _CONTRACTS_ORG_IDS)
    except Exception as e:
        logging.exception('get_contracts')
        raise HTTPException(502, 'Не удалось получить договоры. Попробуйте позже.') from e

    if not contracts:
        raise HTTPException(404, 'Договоры не найдены.')

    result = []
    for c in contracts:
        pdf: bytes = c.get('pdf')
        org_id = c.get('org_id')
        if pdf:
            result.append({
                'org_name': orgs_dict.get(org_id, f'ИП {org_id}'),
                'pdf_b64': base64.b64encode(pdf).decode(),
            })
    if not result:
        raise HTTPException(502, 'Не удалось загрузить PDF договоров.')
    return result


@router.get('/me/contract-template')
async def contract_template():
    """Возвращает статический PDF файл рамочного договора."""
    contract_bytes = get_static_contract_bytes()
    if not contract_bytes:
        raise HTTPException(500, 'Не удалось загрузить договор')
    
    # Save to temp file and return as FileResponse
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(contract_bytes)
        tmp_path = tmp.name
    
    return FileResponse(
        tmp_path,
        media_type='application/pdf',
        filename=STATIC_CONTRACT_FILENAME,
        background=None  # File will be cleaned up automatically
    )

