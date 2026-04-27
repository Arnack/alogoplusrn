from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal
import logging
import asyncio
from io import BytesIO

from datetime import datetime
from API import get_organization_balance, create_payment, get_registry_updated_date, send_registry_for_payment
from API.fin.workers import fin_get_worker
from Schemas import WorkerPaymentSchema
from utils import validate_date, schedule_wallet_payment_check, schedule_sign_workers_acts
from utils.loggers import write_accountant_wp_log
from utils.organizations import orgs_id, orgs_dict
from utils.max_delivery import send_max_message, is_dialog_unavailable_error
from utils.payout_flow import (
    build_act_service_name,
    create_and_send_wallet_payment_act,
    get_wallet_payment_receipt_status,
    save_receipt_documents,
    send_receipt_payment_to_rr,
)
from utils.document_storage import archive_document_file
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


def _normalize_card(value: str | None) -> str:
    return ''.join(ch for ch in (value or '') if ch.isdigit())


async def _get_receipts_queue_items(date: str) -> list[dict]:
    items = []
    wallet_payments = await db.get_wallet_payments_for_receipts(date=date)
    for wp in wallet_payments:
        user = await db.get_user_by_id(user_id=wp.worker.user_id)
        if not user:
            continue
        act = await db.get_wallet_payment_act(wallet_payment_id=wp.id)
        if not act or act.status not in ('signed', 'auto_signed', 'refused'):
            continue
        receipt = await db.get_receipt_by_act(act_id=act.id)
        status = get_wallet_payment_receipt_status(
            wallet_payment_status=wp.status,
            act_status=act.status,
            has_receipt=receipt is not None,
            receipt_url=(receipt.url if receipt else ''),
        )
        items.append({
            'wp_id': wp.id,
            'date': wp.date,
            'full_name': f'{user.last_name} {user.first_name} {user.middle_name}'.strip(),
            'amount': wp.amount,
            'status': status,
            'status_emoji': txt.receipt_status_label(status).split(' ')[0],
        })
    return items


async def _open_receipts_menu(event: Message | CallbackQuery, menu_page: int, date: str) -> None:
    items = await _get_receipts_queue_items(date=date)
    text = txt.no_payments() if not items else txt.receipts_info()
    markup = None if not items else ikb.receipts_queue_menu(items=items, menu_page=menu_page, date=date)
    if isinstance(event, Message):
        await event.answer(text=text, reply_markup=markup)
    else:
        await event.message.edit_text(text=text, reply_markup=markup)


async def _get_wallet_receipt_details(wp_id: int) -> dict | None:
    wp = await db.get_wallet_payment(wp_id=wp_id)
    if not wp:
        return None
    user = await db.get_user_by_id(user_id=wp.worker.user_id)
    act = await db.get_wallet_payment_act(wallet_payment_id=wp_id)
    if not user or not act:
        return None
    receipt = await db.get_receipt_by_act(act_id=act.id)
    service_name = await build_act_service_name(act)
    status = get_wallet_payment_receipt_status(
        wallet_payment_status=wp.status,
        act_status=act.status,
        has_receipt=receipt is not None,
        receipt_url=(receipt.url if receipt else ''),
    )
    return {
        'wallet_payment': wp,
        'user': user,
        'act': act,
        'receipt': receipt,
        'service_name': service_name,
        'status': status,
    }


async def open_wallet_payment_menu(
        event: Message | CallbackQuery,
        menu_page: int,
        date: str,
) -> None:
    wallet_payments = await db.get_wallet_payments(
        date=date,
    )
    if wallet_payments:
        if isinstance(event, Message):
            await event.answer(
                text=txt.wallet_payments_info(),
                reply_markup=ikb.wallet_payments_menu(
                    wallet_payments=wallet_payments,
                    menu_page=menu_page,
                    date=date,
                )
            )
        else:
            await event.message.edit_text(
                text=txt.wallet_payments_info(),
                reply_markup=ikb.wallet_payments_menu(
                    wallet_payments=wallet_payments,
                    menu_page=menu_page,
                    date=date,
                )
            )
    else:
        if isinstance(event, Message):
            await event.answer(
                text=txt.no_payments()
            )
        else:
            await event.message.edit_text(
                text=txt.no_payments()
            )


@router.message(F.text == 'Чеки')
async def receipts_request_date(
        message: Message,
        state: FSMContext,
):
    await message.answer(text=txt.receipts_request_date())
    await state.set_state('AccRequestDateForReceipts')


@router.message(F.text, StateFilter('AccRequestDateForReceipts'))
async def receipts_get_date(
        message: Message,
        state: FSMContext,
):
    is_valid, formatted_date = validate_date(date_str=message.text)
    if not is_valid:
        await message.answer(text=txt.all_format_date_error())
        return
    await state.clear()
    await _open_receipts_menu(event=message, menu_page=1, date=formatted_date)


@router.callback_query(ikb.ReceiptQueueCallbackData.filter(F.action == 'ShowReceipts'))
async def show_receipts_queue(
        callback: CallbackQuery,
        callback_data: ikb.ReceiptQueueCallbackData,
):
    await callback.answer()
    await _open_receipts_menu(event=callback, menu_page=callback_data.menu_page, date=callback_data.date)


@router.callback_query(ikb.ReceiptQueueCallbackData.filter(F.action == 'OpenReceipt'))
async def open_receipt_item(
        callback: CallbackQuery,
        callback_data: ikb.ReceiptQueueCallbackData,
):
    await callback.answer()
    details = await _get_wallet_receipt_details(wp_id=callback_data.wp_id)
    if not details:
        await callback.message.edit_text(text='❌ Не удалось открыть чек.')
        return
    receipt = details['receipt']
    act = details['act']
    user = details['user']
    await callback.message.edit_text(
        text=txt.receipt_card(
            full_name=f'{user.last_name} {user.first_name} {user.middle_name}'.strip(),
            amount=act.amount,
            service_name=details['service_name'],
            inn=user.inn,
            payer_name=orgs_dict.get(act.legal_entity_id, str(act.legal_entity_id)),
            status_label=txt.receipt_status_label(details['status']),
            receipt_url=receipt.url if receipt else None,
        ),
        parse_mode='HTML',
        reply_markup=ikb.receipt_item_actions(
            wp_id=callback_data.wp_id,
            can_pay=details['status'] == 'ready',
            has_receipt=receipt is not None and bool((receipt.url or '').strip()),
        ),
        disable_web_page_preview=True,
    )


@router.callback_query(F.data.startswith('ReceiptPay:'))
async def receipt_pay(
        callback: CallbackQuery,
):
    await callback.answer()
    wp_id = int(callback.data.split(':')[1])
    details = await _get_wallet_receipt_details(wp_id=wp_id)
    if not details:
        await callback.message.edit_text(text='❌ Не удалось отправить выплату.')
        return
    result = await send_receipt_payment_to_rr(act_id=details['act'].id)
    if result.get('success'):
        await callback.message.edit_text(
            text=txt.receipt_sent_to_rr(
                full_name=f"{details['user'].last_name} {details['user'].first_name} {details['user'].middle_name}".strip(),
                amount=details['act'].amount,
            )
        )
    else:
        await callback.message.answer(text=result.get('message', '❌ Не удалось отправить выплату.'))


@router.callback_query(F.data.startswith('ReceiptAdd:'))
async def receipt_add(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    wp_id = int(callback.data.split(':')[1])
    await state.update_data(AccountantReceiptWP=wp_id)
    await state.set_state('AccountantReceiptInput')
    await callback.message.answer('Отправьте ссылку на чек или скриншот/фото QR-кода.')


@router.callback_query(F.data.startswith('ReceiptNew:'))
async def receipt_request_new(
        callback: CallbackQuery,
):
    await callback.answer()
    wp_id = int(callback.data.split(':')[1])
    details = await _get_wallet_receipt_details(wp_id=wp_id)
    if not details:
        await callback.message.answer('❌ Не удалось перевести чек в ожидание нового.')
        return
    receipt = details['receipt']
    if receipt:
        await db.update_receipt_url(receipt_id=receipt.id, url='')
    await db.update_wallet_payment_status(wp_id=wp_id, status='ACT_SENT')
    user = details['user']
    try:
        if user.tg_id:
            await callback.bot.send_message(chat_id=user.tg_id, text=txt.receipt_rejected(), parse_mode='HTML')
    except Exception:
        pass
    if user.max_id:
        try:
            from maxapi import Bot as MaxBot
            from maxapi.enums.parse_mode import ParseMode as MaxParseMode
            from config_reader import config as cfg
            if cfg.max_bot_token:
                max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                try:
                    await send_max_message(
                        max_bot,
                        user_id=user.max_id,
                        chat_id=getattr(user, 'max_chat_id', 0) or None,
                        text=txt.receipt_rejected(),
                        parse_mode=MaxParseMode.HTML,
                    )
                finally:
                    await max_bot.close_session()
        except Exception:
            pass
    await callback.message.answer(text=txt.receipt_replaced())


@router.message(F.text, StateFilter('AccountantReceiptInput'))
async def accountant_receipt_input(
        message: Message,
        state: FSMContext,
):
    wp_id = (await state.get_data()).get('AccountantReceiptWP')
    if not wp_id:
        await state.clear()
        return
    details = await _get_wallet_receipt_details(wp_id=wp_id)
    if not details:
        await state.clear()
        return
    receipt_url = (message.text or '').strip()
    if not receipt_url.startswith('http'):
        await message.answer('❗ Отправьте ссылку на чек из «Мой налог» или фото QR-кода.')
        return
    act = details['act']
    user = details['user']
    security = await db.get_user_real_data_by_id(user_id=user.id)
    receipt = details['receipt']
    if receipt is None:
        receipt = await db.create_receipt(act_id=act.id, worker_id=user.id, url=receipt_url)
    else:
        await db.update_receipt_url(receipt_id=receipt.id, url=receipt_url)
        receipt = await db.get_receipt(receipt_id=receipt.id)
    if security:
        await save_receipt_documents(
            receipt=receipt,
            worker=user,
            security=security,
            act_date=act.date,
            receipt_url=receipt_url,
        )
    await db.update_wallet_payment_status(wp_id=wp_id, status='RECEIPT_READY')
    await state.clear()
    await message.answer('✅ Чек сохранён. Теперь его можно оплатить.')


@router.message(F.photo, StateFilter('AccountantReceiptInput'))
async def accountant_receipt_input_photo(
        message: Message,
        state: FSMContext,
):
    from utils.qr_reader import decode_qr_from_bytes, extract_receipt_url

    wp_id = (await state.get_data()).get('AccountantReceiptWP')
    if not wp_id:
        await state.clear()
        return
    details = await _get_wallet_receipt_details(wp_id=wp_id)
    if not details:
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
    receipt_url = extract_receipt_url(raw)
    if not receipt_url:
        await message.answer(text=txt.receipt_qr_invalid())
        return
    act = details['act']
    user = details['user']
    security = await db.get_user_real_data_by_id(user_id=user.id)
    receipt = details['receipt']
    if receipt is None:
        receipt = await db.create_receipt(act_id=act.id, worker_id=user.id, url=receipt_url)
    else:
        await db.update_receipt_url(receipt_id=receipt.id, url=receipt_url)
        receipt = await db.get_receipt(receipt_id=receipt.id)
    if security:
        await save_receipt_documents(
            receipt=receipt,
            worker=user,
            security=security,
            act_date=act.date,
            receipt_url=receipt_url,
            screenshot_bytes=buf.getvalue(),
            screenshot_extension='jpg',
        )
    await db.update_wallet_payment_status(wp_id=wp_id, status='RECEIPT_READY')
    await state.clear()
    await message.answer('✅ Чек сохранён. Теперь его можно оплатить.')


async def create_registry_for_wp(
        callback: CallbackQuery,
        job_fp: str,
        wp_id: int,
        org_id: int,
) -> None:
    wallet_payment = await db.get_wallet_payment(
        wp_id=wp_id,
    )
    worker = await db.get_user_by_id(
        user_id=wallet_payment.worker.user_id,
    )
    platform_card = _normalize_card(worker.card)
    rr_worker = await fin_get_worker(worker.api_id) if worker and worker.api_id else None
    rr_card = _normalize_card((rr_worker or {}).get('bankcardNumber') or (rr_worker or {}).get('bankcard_number'))
    if not platform_card and rr_card:
        await db.update_worker_bank_card(worker_id=worker.id, card=rr_card)
        worker.card = rr_card
        platform_card = rr_card
    if platform_card and rr_card and platform_card != rr_card:
        old_platform_card = platform_card
        await db.update_worker_bank_card(worker_id=worker.id, card=rr_card)
        worker.card = rr_card
        platform_card = rr_card
        logging.info(
            '[wallet-payment] wp=%s worker=%s action=sync_card_from_rr platform_old=%s rr=%s',
            wp_id,
            worker.id,
            f'****{old_platform_card[-4:]}' if len(old_platform_card) >= 4 else 'empty',
            f'****{rr_card[-4:]}' if len(rr_card) >= 4 else 'empty',
        )
    if not rr_card:
        await db.update_wallet_payment_status(wp_id=wp_id, status='ERROR')
        notify_text = txt.payment_stopped_no_card()
        try:
            if worker.tg_id:
                await callback.bot.send_message(chat_id=worker.tg_id, text=notify_text, parse_mode='HTML')
        except Exception as e:
            logging.exception(f'\n\n{e}')
        if worker.max_id:
            max_bot = None
            try:
                from maxapi import Bot as MaxBot
                from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                from config_reader import config as cfg
                if cfg.max_bot_token:
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                    await send_max_message(
                        max_bot,
                        user_id=worker.max_id,
                        chat_id=getattr(worker, 'max_chat_id', 0) or None,
                        text=notify_text,
                        parse_mode=MaxParseMode.HTML,
                    )
            except Exception as e:
                if is_dialog_unavailable_error(e):
                    logging.warning(f'[max] Не удалось отправить уведомление о проблеме выплаты пользователю {worker.max_id}: чат недоступен')
                else:
                    logging.exception(f'[max] Ошибка отправки уведомления о проблеме выплаты из начислений: {e}')
            finally:
                if max_bot is not None:
                    try:
                        await max_bot.close_session()
                    except Exception:
                        pass
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=txt.workers_skipped_no_card(
                payment_name=f'из начислений №{wp_id}',
                skipped=[{
                    'full_name': f'{worker.last_name} {worker.first_name} {worker.middle_name}'.strip(),
                        'inn': worker.inn,
                        'amount': wallet_payment.amount,
                }],
            ),
            parse_mode='HTML',
        )
        return
    try:
        await callback.bot.send_message(
            chat_id=worker.tg_id,
            text=txt.wallet_payment_notification(
                amount=wallet_payment.amount,
                card=platform_card,
            )
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
    if worker.max_id:
        max_bot = None
        try:
            from maxapi import Bot as MaxBot
            from maxapi.enums.parse_mode import ParseMode as MaxParseMode
            from config_reader import config as cfg

            if cfg.max_bot_token:
                max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                await send_max_message(
                    max_bot,
                    user_id=worker.max_id,
                    chat_id=getattr(worker, 'max_chat_id', 0) or None,
                    text=txt.wallet_payment_notification(
                        amount=wallet_payment.amount,
                        card=worker.card,
                    ),
                    parse_mode=MaxParseMode.HTML,
                )
        except Exception as e:
            if is_dialog_unavailable_error(e):
                logging.warning(f'[max] Не удалось отправить уведомление о выплате из начислений пользователю {worker.max_id}: чат недоступен')
            else:
                logging.exception(f'[max] Ошибка отправки уведомления о выплате из начислений: {e}')
        finally:
            if max_bot is not None:
                try:
                    await max_bot.close_session()
                except Exception:
                    pass

    worker_schema = WorkerPaymentSchema(
        first_name=wallet_payment.worker.first_name,
        middle_name=wallet_payment.worker.middle_name,
        last_name=wallet_payment.worker.last_name,
        inn=worker.inn,
        amount=wallet_payment.amount,
        type_of_work=job_fp,
        card_number=platform_card,
        phone=wallet_payment.worker.phone_number.lstrip('+').lstrip('7'),
    )

    try:
        date_api = datetime.strptime(wallet_payment.date, '%d.%m.%Y').strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        date_api = datetime.now().strftime('%Y-%m-%d')

    api_registry_id, registry_status = await create_payment(
        payment_id=wp_id,
        workers=[worker_schema],
        org_id=org_id,
        is_wallet_payment=True,
    )
    if api_registry_id:
        write_accountant_wp_log(
            message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Создан реестр №{api_registry_id}',
        )
        await db.update_wallet_payment(
            wp_id=wp_id,
            api_registry_id=api_registry_id,
            status=f"rr:{registry_status}",
        )
        try:
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=txt.api_registry_created(
                    payment_name=f'wallet_payment_{wp_id}',
                    registry_id_in_db=wp_id,
                    is_wallet_payment=True,
                ),
            )
        except Exception as e:
            logging.exception(f'\n\n{e}')

        updated_date = await get_registry_updated_date(api_registry_id)
        result = updated_date and await send_registry_for_payment(api_registry_id, updated_date)
        if result:
            write_accountant_wp_log(
                message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Реестр №{api_registry_id} отправлен в оплату',
            )
            try:
                await callback.bot.send_message(
                    chat_id=callback.from_user.id,
                    text=txt.registry_sent_for_payment(
                        payment_name=f'wallet_payment_{wp_id}',
                        registry_id_in_db=wp_id,
                    ),
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            await schedule_sign_workers_acts(
                api_registry_id=api_registry_id,
                order_id=wp_id,
            )

            await schedule_wallet_payment_check(
                api_registry_id=api_registry_id,
                wp_id=wp_id,
                accountant_tg_id=callback.from_user.id,
                worker_full_name=f'{worker.last_name} {worker.first_name} {worker.middle_name}',
                date_api=date_api,
            )

            asyncio.create_task(
                db.update_wallet_payment_status(
                    wp_id=wp_id,
                    status='inPayment',
                )
            )
        else:
            try:
                await callback.bot.send_message(
                    chat_id=callback.from_user.id,
                    text=txt.create_registry_send_for_payment_error(
                        payment_name=f'wallet_payment_{wp_id}',
                        registry_id_in_db=wp_id,
                        is_wallet_payment=True,
                    ),
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')

            asyncio.create_task(
                db.update_wallet_payment_status(
                    wp_id=wp_id,
                    status='ERROR',
                )
            )
            write_accountant_wp_log(
                message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Не удалось отправить реестр №{api_registry_id} в оплату',
                level='ERROR',
            )
    else:
        try:
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=txt.create_registry_api_error(
                    payment_name=f'wallet_payment_{wp_id}',
                    registry_id_in_db=wp_id,
                )
            )
        except Exception as e:
            logging.exception(f'\n\n{e}')

        asyncio.create_task(
            db.update_wallet_payment_status(
                wp_id=wp_id,
                status='ERROR',
            )
        )
        write_accountant_wp_log(
            message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Не удалось создать платежный реестр',
            level='ERROR',
        )


@router.message(F.text == 'Запросы из начислений')
async def wallet_payment_request_date(
        message: Message,
        state: FSMContext,
):
    await message.answer(
        text=txt.request_date_all_formats()
    )
    await state.set_state('AccRequestDateForWP')
    write_accountant_wp_log(
        message=f'Кассир {message.from_user.id} | Открыл раздел "Запросы из начислений"',
    )


@router.message(F.text, StateFilter('AccRequestDateForWP'))
async def wallet_payment_get_date(
        message: Message,
        state: FSMContext
):
    is_valid, formatted_date = validate_date(
        date_str=message.text
    )
    if is_valid:
        await state.set_state(None)
        await open_wallet_payment_menu(
            event=message,
            menu_page=1,
            date=formatted_date,
        )
        write_accountant_wp_log(
            message=f'Кассир {message.from_user.id} | Ввел дату верно',
        )
    else:
        await message.answer(
            text=txt.all_format_date_error(),
        )
        write_accountant_wp_log(
            message=f'Кассир {message.from_user.id} | Ввел дату с ошибкой',
        )


@router.callback_query(ikb.WalletPaymentCallbackData.filter(F.action == 'ShowWalletPayments'))
async def show_wallet_payments(
        callback: CallbackQuery,
        callback_data: ikb.WalletPaymentCallbackData,
):
    await callback.answer()
    await open_wallet_payment_menu(
        event=callback,
        menu_page=callback_data.menu_page,
        date=callback_data.date,
    )


@router.callback_query(ikb.WalletPaymentCallbackData.filter(F.action == 'OpenWP'))
async def open_wallet_payment(
        callback: CallbackQuery,
        callback_data: ikb.WalletPaymentCallbackData,
        state: FSMContext,
):
    await callback.answer()
    payment_amount = Decimal(callback_data.amount)

    checked_orgs = []
    for org_id in orgs_id:
        org_balance = await get_organization_balance(org_id)

        if org_balance and Decimal(org_balance) >= payment_amount:
            checked_orgs.append(
                {'id': org_id, 'balance': org_balance}
            )

    write_accountant_wp_log(
        message=f'Кассир {callback.from_user.id} | Открыл выплату из кошелька №{callback_data.wp_id}',
    )
    if checked_orgs:
        await state.update_data(
            WorkerIDforWP=callback_data.worker_id,
        )
        await callback.message.edit_text(
            text=txt.choose_ip_for_payment(),
            reply_markup=ikb.choose_ip_for_wallet_payment(
                wp_id=callback_data.wp_id,
                orgs=checked_orgs,
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_suitable_org()
        )
        write_accountant_wp_log(
            message=f'Кассир {callback.from_user.id} | Нет подходящих ИП для выплаты из кошелька',
        )


@router.callback_query(F.data.startswith('ConfirmationCreateWP:'))
async def create_wallet_payment(
        callback: CallbackQuery,
):
    await callback.answer()
    org_id = int(callback.data.split(':')[2])
    wp_id = int(callback.data.split(':')[1])

    wallet_payment = await db.get_wallet_payment(
        wp_id=wp_id,
    )

    await callback.message.edit_text(
        text=txt.confirmation_create_wallet_payment(
            wallet_payment=wallet_payment,
            org_name=orgs_dict[org_id],
        ),
        reply_markup=ikb.confirmation_create_wallet_payment(
            wp_id=wp_id,
            org_id=org_id,
        )
    )
    write_accountant_wp_log(
        message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Выбрал {orgs_dict[org_id]}',
    )


@router.callback_query(F.data.startswith('CancelCreateWP:'))
async def cancel_create_wallet_payment(
        callback: CallbackQuery,
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.create_payment_canceled()
    )
    write_accountant_wp_log(
        message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{callback.data.split(":")[1]} | {txt.create_payment_canceled()}',
    )


@router.callback_query(F.data.startswith('ConfirmCreateWP:'))
async def confirm_create_wallet_payment(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    wp_id = int(callback.data.split(':')[1])
    org_id = int(callback.data.split(':')[2])
    data = await state.get_data()
    worker_id = data['WorkerIDforWP']

    # П.7 ТЗ: Архивировать 2 договора из 3, оставить только с выбранным ИП
    archived = await db.archive_contracts_except_legal_entity(
        user_id=worker_id,
        legal_entity_id=org_id,
        wallet_payment_id=wp_id,
    )
    for contract_id in archived:
        contract = await db.get_contract(contract_id=contract_id)
        if contract and contract.file_path:
            archived_path = await archive_document_file(contract.file_path)
            if archived_path:
                await db.set_contract_file_path(contract_id=contract.id, file_path=archived_path)
    if archived:
        write_accountant_wp_log(
            message=f'Кассир {callback.from_user.id} | Архивировано {len(archived)} договоров для worker={worker_id}, оставлен org={org_id}',
        )

    wallet_payment = await db.get_wallet_payment(wp_id=wp_id)
    act_date = datetime.strftime(datetime.now(), "%d.%m.%Y")
    act = await create_and_send_wallet_payment_act(
        bot=callback.bot,
        worker_id=worker_id,
        wallet_payment_id=wp_id,
        org_id=org_id,
        amount=wallet_payment.amount,
        date=act_date,
    )
    if act:
        await callback.message.edit_text(
            text=txt.wallet_payment_created(
                wp_id=wp_id,
            )
        )
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=f'Акт №{act.id} отправлен исполнителю. После чека выплата уйдёт в РР.',
        )
    else:
        write_accountant_wp_log(
            message=f'Кассир {callback.from_user.id} | Выплата из кошелька №{wp_id} | Не удалось создать акт',
        )
        await callback.message.edit_text(
            text='❌ Не удалось создать акт для выплаты'
        )
