import asyncio
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from decimal import Decimal

import keyboards.inline as ikb
from utils import (
    get_day_of_week_by_date,
    get_rating_coefficient,
    get_rating
)
from utils.debtor_pricing import calculate_reduced_unit_price
from filters import Worker
import database as db
import texts as txt
from handlers.user.menu.phone_verification import require_phone_verification
from utils.contract_pin import choose_pin, verify_pin
from utils.organizations import orgs_contract_template_id
from utils.static_contract import get_static_contract_bytes, STATIC_CONTRACT_FILENAME


router = Router()


# ---------------------------------------------------------------------------
# Phase 4 helpers
# ---------------------------------------------------------------------------

async def _find_unsigned_contracts(api_worker_id: int) -> list:
    """
    Возвращает список неподписанных договоров работника по всем 3 ИП.
    Если по какому-то ИП договора нет, он будет создан до показа экрана подписи.
    """
    try:
        from API.fin.contracts import fin_get_unsigned_contracts_all_orgs
        return await fin_get_unsigned_contracts_all_orgs(
            worker_id=api_worker_id,
            org_template_map=orgs_contract_template_id,
        )
    except Exception as e:
        logging.warning(f'[Phase4] contract check error for worker {api_worker_id}: {e}')
        return []


async def _start_contract_signing(
        callback: CallbackQuery,
        state: FSMContext,
        contracts: list,
        order_id: int,
        worker_id: int,
        worker_inn: str | None,
        order_from_friend: bool,
) -> None:
    """Запускает флоу подписания договора перед откликом на заявку."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    contract = contracts[0] if contracts else {}
    contract_ids = [contract_item.get('id') for contract_item in contracts if contract_item.get('id')]
    contract_id = contract.get('id')
    worker = await db.get_user(tg_id=callback.from_user.id)
    security = await db.get_user_real_data_by_id(user_id=worker.id) if worker else None
    birthday = ''
    if worker and worker.api_id:
        from API.fin.workers import fin_get_worker
        worker_fin = await fin_get_worker(worker.api_id)
        birthday = (worker_fin or {}).get('birthday') or ''
    pin_type, _pin_value, hint = choose_pin(
        inn=(worker_inn or ''),
        birthday=birthday,
        passport_number=(security.passport_number if security else '') or '',
    )
    await state.update_data(
        ContractOrderId=order_id,
        ContractWorkerId=worker_id,
        ContractWorkerINN=worker_inn,
        ContractContractId=contract_id,
        ContractContractIds=contract_ids,
        ContractOrderFromFriend=order_from_friend,
        ContractSignPinType=pin_type,
    )
    await state.set_state('ContractSignCodeOrder')

    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='❌ Отказаться', callback_data='RejectContractOrder'),
    ]])

    pdf_bytes = get_static_contract_bytes()
    if pdf_bytes:
        await callback.message.answer_document(
            document=BufferedInputFile(file=pdf_bytes, filename=STATIC_CONTRACT_FILENAME),
            caption=txt.preview_contract(),
            reply_markup=cancel_kb,
            protect_content=True,
        )
        await callback.message.answer(
            text=f'Введите {hint}:',
            protect_content=True,
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.message.edit_text(
            text=txt.preview_contract(),
            reply_markup=cancel_kb,
        )
        await callback.message.answer(
            text=f'Введите {hint}:',
            protect_content=True,
        )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@router.callback_query(Worker(), F.data.startswith('RespondToAnOrder:'))
async def confirmation_respond(
        callback: CallbackQuery,
        state: FSMContext,
):
    worker = await db.get_user(
        tg_id=callback.from_user.id
    )
    if worker and worker.api_id:
        unsigned = await _find_unsigned_contracts(api_worker_id=worker.api_id)
        if unsigned:
            await callback.answer()
            await _start_contract_signing(
                callback=callback,
                state=state,
                contracts=unsigned,
                order_id=int(callback.data.split(':')[1]),
                worker_id=worker.id,
                worker_inn=worker.inn,
                order_from_friend=False,
            )
            return

    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(
        order_id=order_id
    )

    rating = await get_rating(
        user_id=worker.id
    )
    user_rating = await db.get_user_rating(
        user_id=worker.id
    )
    coefficient = get_rating_coefficient(
        rating=rating[:-1]
    )
    if Decimal(rating[:-1]) >= Decimal('85'):
        text = txt.confirmation_respond_high_rating()
    else:
        unit_price = Decimal(order.amount.replace(',', '.'))
        withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=worker.id)
        if withholding > 0:
            display_amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
        else:
            display_amount = unit_price * coefficient
        text = txt.confirmation_respond_low_rating(
            rating=rating,
            amount=display_amount,
            total_orders=user_rating.total_orders,
            successful_orders=user_rating.successful_orders,
            plus=user_rating.plus,
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=ikb.accept_respond(
            order_id=order_id
        )
    )


@router.callback_query(Worker(), F.data.startswith('ConfirmRespond:'))
async def confirm_respond(
        callback: CallbackQuery,
        state: FSMContext
):
    phone_verification_started = False
    contract_signing_started = False
    try:
        order_id = int(callback.data.split(':')[1])

        # Проверка SMS-верификации телефона (и call_block)
        current_user = await db.get_user(tg_id=callback.from_user.id)
        if not await require_phone_verification(callback, state, current_user, order_id):
            phone_verification_started = True
            return

        order = await db.get_order(order_id=order_id)
        if not order:
            await callback.answer("Заявка не найдена или была удалена", show_alert=True)
            return

        order_shift = f"{order.date} {'день' if order.day_shift else 'ночь'}"
        data = await state.get_data()

        if data.get('SearchOrderFor', 'myself') == 'myself':
            worker = current_user
            worker_id = worker.id
            order_from_friend = False
        else:
            friend = await db.get_user_by_id(
                user_id=data['FriendID']
            )
            who_signed = await db.get_user(
                tg_id=callback.from_user.id
            )
            await db.set_order_for_friend_log(
                order_id=order_id,
                who_signed=who_signed.id,
                who_signed_tg_id=callback.from_user.id,
                friend_id=friend.id,
                friend_tg_id=friend.tg_id
            )
            worker_id = data['FriendID']
            order_from_friend = True

        worker_dates = await db.get_worker_dates(worker_id=worker_id)

        if order_shift in worker_dates:
            await callback.answer()
            await callback.message.edit_text(
                text=txt.has_date(
                    date_time=order_shift
                )
            )
            return

        # --- Phase 4: проверка договора ---
        if current_user.api_id:
            unsigned = await _find_unsigned_contracts(api_worker_id=current_user.api_id)
            if unsigned:
                await callback.answer()
                await _start_contract_signing(
                    callback=callback,
                    state=state,
                    contracts=unsigned,
                    order_id=order_id,
                    worker_id=worker_id,
                    worker_inn=current_user.inn,
                    order_from_friend=order_from_friend,
                )
                contract_signing_started = True
                return

        # --- Подаём отклик ---
        await callback.answer()
        applied = await db.set_application(
            order_id=order_id,
            worker_id=worker_id,
            order_from_friend=order_from_friend
        )
        if applied == 'ok':
            await callback.message.edit_text(
                text=txt.send_respond()
            )

            applications_count = await db.get_applications_count_by_order_id(order_id=order_id)
            if applications_count == order.workers:
                managers = await db.get_managers_tg_id()
                directors = await db.get_directors_tg_id()
                recipients = list(managers) + list(directors)
                for manager in recipients:
                    try:
                        await callback.bot.send_message(
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
        elif applied == 'duplicate':
            await callback.message.edit_text(text=txt.send_respond())
        else:
            await callback.message.edit_text(text=txt.no_respond_sent())
    finally:
        if not phone_verification_started and not contract_signing_started:
            await state.clear()


# ---------------------------------------------------------------------------
# Phase 4: договор при отклике — подписание
# ---------------------------------------------------------------------------

@router.callback_query(Worker(), F.data == 'SignContractOrder', StateFilter('ContractSigningForOrder'))
async def sign_contract_order_callback(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    data = await state.get_data()
    worker = await db.get_user(tg_id=callback.from_user.id)
    security = await db.get_user_real_data_by_id(user_id=worker.id) if worker else None
    birthday = ''
    if worker and worker.api_id:
        from API.fin.workers import fin_get_worker
        worker_fin = await fin_get_worker(worker.api_id)
        birthday = (worker_fin or {}).get('birthday') or ''
    pin_type, _pin_value, hint = choose_pin(
        inn=(worker.inn if worker else '') or '',
        birthday=birthday,
        passport_number=(security.passport_number if security else '') or '',
    )
    await state.update_data(ContractSignPinType=pin_type)
    await callback.message.answer(
        text=f'📄 <b>Для отклика на заявку необходимо подписать договор.</b>\n\nВведите {hint}:',
        protect_content=True,
        parse_mode='HTML',
    )
    await state.set_state('ContractSignCodeOrder')
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(Worker(), F.data == 'RejectContractOrder', StateFilter('ContractSignCodeOrder'))
async def reject_contract_order(
        callback: CallbackQuery,
        state: FSMContext,
):
    await callback.answer()
    data = await state.get_data()
    order_id = data.get('ContractOrderId')
    order = await db.get_order(order_id=order_id) if order_id else None
    if not order:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text=txt.contract_reject_order())
        await state.clear()
        return

    day = get_day_of_week_by_date(date=order.date)
    worker = await db.get_user(tg_id=callback.from_user.id)
    job_fp = await db.get_job_fp_for_txt(worker_id=worker.id) if worker else ''
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        text=await txt.sending_order_to_users(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day=day,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=order.amount,
            job_fp=job_fp,
        ),
        reply_markup=ikb.respond_to_an_order(order_id=order.id),
    )
    await state.clear()


@router.message(Worker(), F.text, StateFilter('ContractSignCodeOrder'))
async def handle_contract_sign_code_for_order(
        message: Message,
        state: FSMContext,
):
    from API.fin.contracts import fin_sign_contracts_all_orgs
    data = await state.get_data()
    inn: str = data.get('ContractWorkerINN', '')
    pin_type: str = data.get('ContractSignPinType', 'inn')
    contract_ids: list[int] = data.get('ContractContractIds', [])
    contract_id: int | None = data.get('ContractContractId')
    order_id: int = data.get('ContractOrderId')
    worker_id: int = data.get('ContractWorkerId')
    order_from_friend: bool = data.get('ContractOrderFromFriend', False)
    worker = await db.get_user(tg_id=message.from_user.id)
    security = await db.get_user_real_data_by_id(user_id=worker.id) if worker else None
    birthday = ''
    if worker and worker.api_id:
        from API.fin.workers import fin_get_worker
        worker_fin = await fin_get_worker(worker.api_id)
        birthday = (worker_fin or {}).get('birthday') or ''

    if not verify_pin(
        pin_type=pin_type,
        entered=message.text.strip(),
        inn=inn or '',
        birthday=birthday,
        passport_number=(security.passport_number if security else '') or '',
    ):
        await message.answer(text=txt.contract_inn_error(), protect_content=True)
        return

    await state.set_state(None)

    signed = False
    if contract_ids:
        signed = await fin_sign_contracts_all_orgs(
            worker_id=worker.api_id if worker else 0,
            contract_ids=contract_ids,
        )
    elif contract_id:
        signed = await fin_sign_contracts_all_orgs(
            worker_id=worker.api_id if worker else 0,
            contract_ids=[contract_id],
        )

    if not signed:
        await message.answer(text=txt.sign_contract_error(), protect_content=True)
        await state.clear()
        return

    # Подаём отклик
    order = await db.get_order(order_id=order_id)
    if not order:
        await message.answer(text=txt.no_respond_sent(), protect_content=True)
        await state.clear()
        return

    applied = await db.set_application(
        order_id=order_id,
        worker_id=worker_id,
        order_from_friend=order_from_friend,
    )
    if applied in ('ok', 'duplicate'):
        await message.answer(text=txt.contract_signed_proceed(), protect_content=True)
        if applied == 'ok':
            applications_count = await db.get_applications_count_by_order_id(order_id=order_id)
            if applications_count == order.workers:
                managers = await db.get_managers_tg_id()
                directors = await db.get_directors_tg_id()
                for manager_id in list(managers) + list(directors):
                    try:
                        await message.bot.send_message(
                            chat_id=manager_id,
                            text=await txt.notification_by_order(
                                order_id=order_id,
                                customer_id=order.customer_id,
                                date=order.date,
                                day_shift=order.day_shift,
                                night_shift=order.night_shift,
                                workers_count=order.workers,
                            )
                        )
                    except Exception:
                        pass
    else:
        await message.answer(text=txt.no_respond_sent(), protect_content=True)

    await state.clear()


# ---------------------------------------------------------------------------
# Cancel / back handlers
# ---------------------------------------------------------------------------

@router.callback_query(Worker(), F.data.startswith('CancelRespond:'))
async def cancel_respond(
        callback: CallbackQuery
):
    await callback.answer()

    order_id = int(callback.data.split(':')[1])
    order = await db.get_order(order_id=order_id)
    if not order:
        await callback.message.delete()
        return
    day = get_day_of_week_by_date(date=order.date)
    worker = await db.get_user(
        tg_id=callback.from_user.id
    )

    job_fp = await db.get_job_fp_for_txt(
        worker_id=worker.id
    )

    await callback.message.edit_text(
        text=await txt.sending_order_to_users(
            city=order.city,
            customer_id=order.customer_id,
            job=order.job_name,
            date=order.date,
            day=day,
            day_shift=order.day_shift,
            night_shift=order.night_shift,
            amount=order.amount,
            job_fp=job_fp
        ),
        reply_markup=ikb.respond_to_an_order(
            order_id=order_id
        )
    )


@router.callback_query(Worker(), F.data.startswith('RespondToAnOrderSearch:'))
async def respond_in_search(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    data = await state.get_data()
    order_for = data.get('SearchOrderFor', 'myself')

    if order_for == 'myself':
        user = await db.get_user(tg_id=callback.from_user.id)
        if user and user.api_id:
            unsigned = await _find_unsigned_contracts(api_worker_id=user.api_id)
            if unsigned:
                await callback.answer()
                await _start_contract_signing(
                    callback=callback,
                    state=state,
                    contracts=unsigned,
                    order_id=order_id,
                    worker_id=user.id,
                    worker_inn=user.inn,
                    order_from_friend=False,
                )
                return

    order = await db.get_order(
        order_id=order_id
    )

    if order_for == 'myself':
        user = await db.get_user(
            tg_id=callback.from_user.id
        )
        rating = await get_rating(
            user_id=user.id
        )
        user_rating = await db.get_user_rating(
            user_id=user.id
        )
        coefficient = get_rating_coefficient(
            rating=rating[:-1]
        )
        if Decimal(rating[:-1]) >= Decimal('93'):
            text = txt.confirmation_respond_high_rating()
        else:
            unit_price = Decimal(order.amount.replace(',', '.'))
            withholding = await db.get_max_assigned_amount_for_active_cycle(worker_id=user.id)
            if withholding > 0:
                display_amount = calculate_reduced_unit_price(unit_price, coefficient, withholding)
            else:
                display_amount = unit_price * coefficient
            text = txt.confirmation_respond_low_rating(
                rating=rating,
                amount=display_amount,
                total_orders=user_rating.total_orders,
                successful_orders=user_rating.successful_orders,
                plus=user_rating.plus,
            )
        keyboard = ikb.accept_respond_in_search(
            order_id=order_id
        )
    else:
        real_data = await db.get_user_real_data_by_id(
            user_id=data['FriendID']
        )
        user = await db.get_user_by_id(
            user_id=data['FriendID']
        )
        rating = await get_rating(
            user_id=user.id
        )
        coefficient = get_rating_coefficient(
            rating=rating[:-1]
        )

        text = await txt.confirmation_respond_for_friend(
            order_id=order_id,
            first_name=real_data.first_name,
            middle_name=real_data.middle_name,
            last_name=real_data.last_name,
            amount=str(
                round(Decimal(order.amount) * coefficient, 2)
            )
        )
        keyboard = ikb.confirmation_respond_for_friend(
            order_id=order_id
        )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard
    )


@router.callback_query(Worker(), F.data == 'CancelRespondOrderForFriend')
async def cancel_respond_order_for_friend(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.clear()
    await callback.message.delete()
    await callback.answer(
        text=txt.cancel_respond_order_for_friend(),
        show_alert=True
    )
