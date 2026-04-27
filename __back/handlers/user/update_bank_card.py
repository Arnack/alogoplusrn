from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LinkPreviewOptions
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import asyncio
import logging

from filters import Worker
from API import (
    create_all_contracts_for_worker,
    sign_all_worker_contracts,
    update_worker_bank_card,
)
from utils import delete_state_data, luhn_check
from utils.contract_pin import choose_pin, verify_pin
from API.fin.workers import fin_get_worker
import database as db
import texts as txt


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())


@router.callback_query(F.data == 'UpdateWorkerBankCard')
async def request_new_card(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(text=txt.request_new_card())
    worker = await db.get_user(tg_id=callback.from_user.id)
    security = await db.get_user_real_data_by_id(user_id=worker.id) if worker else None
    worker_fin = await fin_get_worker(worker.api_id) if worker and worker.api_id else None
    await state.set_state('CardToUpdate')
    await state.update_data(
        CurrentCard=worker.card,
        WorkerINN=worker.inn,
        ApiWorkerID=worker.api_id,
        WorkerID=worker.id,
        WorkerPassportNumber=(security.passport_number if security else '') or '',
        WorkerBirthday=(worker_fin or {}).get('birthday') or '',
    )


@router.message(F.text, StateFilter('CardToUpdate'))
async def get_card_number(
        message: Message,
        state: FSMContext
):
    card = message.text.replace(' ', '')
    if not card.isdigit():
        await message.answer(text=txt.card_number_error())
        return
    if not luhn_check(card):
        await message.answer(text=txt.luhn_check_error())
        return
    if await db.card_unique(card):
        await message.answer(
            text=txt.card_not_unique_error(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return
    data = await state.get_data()
    if card == data['CurrentCard']:
        await message.answer(text=txt.same_card_error())
        return

    await state.update_data(NewCard=card)
    data = await state.get_data()
    pin_type, _pin_val, hint = choose_pin(
        inn=data.get('WorkerINN', ''),
        birthday=data.get('WorkerBirthday', ''),
        passport_number=data.get('WorkerPassportNumber', ''),
    )
    await state.update_data(SignPinType=pin_type)
    await message.answer(
        text=(
            'ℹ️ Банковская карта для получения вознаграждения указывается в тексте Договора оказания услуг.\n'
            'При изменении банковской карты автоматически заключаются <b>новые Договоры оказания услуг</b>.\n\n'
            f'Для подтверждения введите {hint}:'
        ),
        protect_content=True,
        parse_mode='HTML',
    )
    await state.set_state('SignContractCodeUpdateCard')


@router.message(F.text, StateFilter('SignContractCodeUpdateCard'))
async def get_sign_contract_code_for_update_card(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    pin_type = data.get('SignPinType', 'inn')
    if not verify_pin(
        pin_type=pin_type,
        entered=message.text,
        inn=data.get('WorkerINN', ''),
        birthday=data.get('WorkerBirthday', ''),
        passport_number=data.get('WorkerPassportNumber', ''),
    ):
        await message.answer(text=txt.contract_inn_error())
        return

    await state.set_state(None)
    msg = await message.answer(text=txt.sign_contracts_for_card_wait())

    api_worker_id = data['ApiWorkerID']
    new_card = data['NewCard']

    # 1. Сначала обновляем карту в fin API — чтобы новые договоры содержали актуальный номер
    card_updated = await update_worker_bank_card(
        api_worker_id=api_worker_id,
        bank_card=new_card,
    )
    logging.info(f'[card-update] worker={api_worker_id} карта обновлена в fin API: {card_updated}')

    if not card_updated:
        await message.bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            text=txt.update_card_error(),
        )
        return

    # 2. Создаём 3 новых договора (уже с новой картой в тексте)
    contracts = await create_all_contracts_for_worker(worker_id=api_worker_id)
    logging.info(f'[card-update] worker={api_worker_id} создано договоров: {len(contracts)}')

    if not contracts:
        await message.bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            text=txt.sign_contract_error(),
        )
        return

    # 3. Подписываем все договоры
    signed = await sign_all_worker_contracts(contracts)
    logging.info(f'[card-update] worker={api_worker_id} подписание: {signed}')

    if not signed:
        await message.bot.edit_message_text(
            chat_id=msg.chat.id,
            message_id=msg.message_id,
            text=txt.sign_contract_error(),
        )
        return

    # 4. Фиксируем новую карту в локальной БД
    asyncio.create_task(
        db.update_worker_bank_card(
            worker_id=data['WorkerID'],
            card=new_card,
        )
    )
    await message.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=msg.message_id,
        text=txt.bank_card_updated(),
    )

    await delete_state_data(
        state=state,
        data_keys_to_delete=[
            'ApiWorkerID', 'WorkerINN', 'CurrentCard', 'NewCard', 'WorkerID',
        ]
    )
