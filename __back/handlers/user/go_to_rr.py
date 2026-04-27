from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaDocument
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from utils.organizations import orgs_dict
from utils.static_contract import get_static_contract_bytes, STATIC_CONTRACT_FILENAME
from utils import (
    normalize_phone_number,
    create_code_hash, check_code,
    schedule_delete_registration_code,
    send_sms_with_api, luhn_check,
)
import keyboards.inline as ikb
import keyboards.reply as kb
from API import (
    api_check_fns_status,
    get_preview_contract_bytes,
    create_all_contracts_for_worker,
    sign_all_worker_contracts,
)
from API.fin.workers import fin_get_worker_by_phone, fin_create_worker
import database as db
import texts as txt
import secrets


router = Router()


@router.callback_query(F.data == 'GoToRR')
async def go_to_rr_request_phone_number(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(text=txt.request_phone_number())
    worker = await db.get_user(tg_id=callback.from_user.id)
    await state.set_state('PhoneNumberForGTRR')
    await state.update_data(
        InnGTRR=worker.inn,
        FirstNameGTRR=worker.first_name or 'Иван',
        LastNameGTRR=worker.last_name or 'Иванов',
        PatronymicGTRR=worker.middle_name or None,
    )


@router.message(F.text, StateFilter('PhoneNumberForGTRR'))
async def get_phone_number(
        message: Message,
        state: FSMContext
):
    phone_number = normalize_phone_number(phone_number=message.text)
    if not phone_number:
        await message.answer(text=txt.phone_number_error(), protect_content=True)
        return

    code = str(secrets.randbelow(900000) + 100000)
    code_hashed = create_code_hash(code=code)
    code_id = await db.set_registration_code(
        code_hash=code_hashed['hash'],
        salt=code_hashed['salt'],
    )
    await schedule_delete_registration_code(code_id=code_id)
    await message.answer(text=txt.request_registration_code(), protect_content=True)
    await state.update_data(PhoneNumberGTRR=phone_number, CodeIdGTRR=code_id)
    await state.set_state('GetCodeGTRR')
    await send_sms_with_api(
        phone_number=phone_number,
        message_text=txt.send_registration_message(code=code),
        tg_id=message.from_user.id,
    )
    del code


@router.message(F.text, StateFilter('GetCodeGTRR'))
async def get_verification_code(
        message: Message,
        state: FSMContext
):
    if not message.text.isdigit():
        await message.answer(text=txt.add_id_error(), protect_content=True)
        return

    data = await state.get_data()
    code_data = await db.get_registration_code_by_id(code_id=data['CodeIdGTRR'])
    if not code_data:
        await message.answer(text=txt.code_error(), protect_content=True)
        await state.clear()
        return

    if not check_code(
        salt=code_data.salt,
        hashed_code=code_data.code_hash,
        entered_code=message.text,
    ):
        await message.answer(text=txt.code_error(), protect_content=True)
        await state.clear()
        return

    await db.delete_registration_code(code_id=code_data.id)
    await state.set_state(None)

    phone = data['PhoneNumberGTRR'].lstrip('+').lstrip('7')
    api_worker = await fin_get_worker_by_phone(phone=phone)

    if api_worker:
        api_worker_id = api_worker['id']
        inn = str(api_worker.get('inn') or data['InnGTRR'])
        await state.update_data(
            ApiWorkerIdGTRR=api_worker_id,
            CardGTRR=api_worker.get('bankcardNumber') or '',
            GTRR_INN=inn,
        )
        await _show_gtrr_contract(message, state, api_worker_id)
    else:
        await message.answer(text=txt.request_card(), protect_content=True)
        await state.set_state('CardNumberGTRR')


@router.message(F.text, StateFilter('CardNumberGTRR'))
async def get_card_number(
        message: Message,
        state: FSMContext
):
    card = message.text.replace(' ', '')
    if not card.isdigit():
        await message.answer(text=txt.card_number_error(), protect_content=True)
        return
    if not luhn_check(card):
        await message.answer(text=txt.luhn_check_error(), protect_content=True)
        return
    if await db.card_unique(card):
        await message.answer(text=txt.card_not_unique_error(), protect_content=True)
        return

    await state.update_data(CardGTRR=card)
    data = await state.get_data()

    api_worker_id = await fin_create_worker(
        phone_number=data['PhoneNumberGTRR'].lstrip('+').lstrip('7'),
        inn=data['InnGTRR'],
        card_number=card,
        first_name=data.get('FirstNameGTRR', 'Иван'),
        last_name=data.get('LastNameGTRR', 'Иванов'),
        patronymic=data.get('PatronymicGTRR'),
    )
    if not api_worker_id:
        await message.answer(text='❗ Не удалось вас зарегистрировать. Пожалуйста, попробуйте позже')
        return

    await state.update_data(ApiWorkerIdGTRR=api_worker_id, GTRR_INN=data['InnGTRR'])

    settings = await db.get_settings()
    _, is_smz = await api_check_fns_status(api_worker_id=api_worker_id)
    if is_smz:
        await _show_gtrr_contract(message, state, api_worker_id)
    else:
        if settings.rr_manual_pic:
            await message.answer_document(
                document=settings.rr_manual_pic,
                caption=txt.send_moy_nalog_manual(),
                reply_markup=ikb.registration_permission_request(
                    api_worker_id=api_worker_id,
                    go_to_rr=True,
                ),
                protect_content=True,
            )
        else:
            await message.answer(
                text=txt.send_moy_nalog_manual(),
                reply_markup=ikb.registration_permission_request(
                    api_worker_id=api_worker_id,
                    go_to_rr=True,
                ),
                protect_content=True,
            )


async def _show_gtrr_contract(event: CallbackQuery | Message, state: FSMContext, api_worker_id: int):
    """Создаёт договора только для ИП, у которых их ещё нет, и показывает PDF первого."""
    msg = event.message if isinstance(event, CallbackQuery) else event

    contracts = await create_all_contracts_for_worker(worker_id=api_worker_id)
    if contracts is None:
        # API недоступен
        await msg.answer(text=txt.send_contract_error())
        return
    if not contracts:
        # Все договора уже подписаны — завершаем без шага подписания
        data = await state.get_data()
        await state.clear()
        await db.update_user_gtrr(
            tg_id=event.from_user.id,
            username=event.from_user.username,
            phone_number=data['PhoneNumberGTRR'],
            api_worker_id=data['ApiWorkerIdGTRR'],
            card=data['CardGTRR'],
        )
        await msg.answer(text=txt.registration_user_completed(), reply_markup=kb.user_menu())
        return

    await state.update_data(GTRRContracts=contracts)

    contract_bytes = get_static_contract_bytes()
    try:
        if contract_bytes:
            await msg.answer_document(
                document=BufferedInputFile(
                    file=contract_bytes,
                    filename=STATIC_CONTRACT_FILENAME,
                ),
                caption=txt.preview_contract(),
                reply_markup=ikb.sign_api_contract(go_to_rr=True),
            )
        else:
            await msg.answer(
                text=txt.preview_contract(),
                reply_markup=ikb.sign_api_contract(go_to_rr=True),
            )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await msg.answer(text=txt.send_contract_error())


@router.callback_query(F.data.startswith('GTRRGavePermission:'))
async def check_permissions(
        callback: CallbackQuery,
        state: FSMContext
):
    api_worker_id = int(callback.data.split(':')[1])
    permissions, is_smz = await api_check_fns_status(api_worker_id=api_worker_id)

    if permissions:
        if is_smz:
            await callback.answer()
            await _show_gtrr_contract(callback, state, api_worker_id)
            await callback.message.delete()
        else:
            settings = await db.get_settings()
            try:
                if settings.registration_pic:
                    await callback.message.edit_media(
                        media=InputMediaDocument(media=settings.registration_pic),
                        reply_markup=ikb.confirmation_became_self_employment(
                            api_worker_id=api_worker_id,
                            go_to_rr=True,
                        ),
                    )
                else:
                    await callback.message.edit_text(
                        text=txt.send_manual_error(),
                        reply_markup=ikb.confirmation_became_self_employment(
                            api_worker_id=api_worker_id,
                            go_to_rr=True,
                        ),
                    )
            except Exception:
                await callback.answer(text='❗️Вы не являетесь самозанятым', show_alert=True)
    else:
        await callback.answer(
            text='⚠️ Разрешение еще не получено. Следуйте инструкции',
            show_alert=True,
        )


@router.callback_query(F.data == 'SignContractGTRR')
async def sign_contract(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    await callback.message.answer(
        text=txt.request_sign_contract(org_name=orgs_dict[392])
    )
    await state.set_state('SignContractCodeGTRR')
    await callback.message.delete()


@router.message(F.text, StateFilter('SignContractCodeGTRR'))
async def get_sign_contract_code(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    if data['GTRR_INN'][-4:] != message.text.strip():
        await message.answer(text=txt.contract_inn_error())
        return

    await state.set_state(None)
    await message.answer(text=txt.sign_contracts_for_registration_wait())

    contracts = data.get('GTRRContracts', [])
    if not contracts:
        await message.answer(text=txt.sign_contract_error())
        return

    signed = await sign_all_worker_contracts(contracts)
    logging.info(f'[gtrr] worker={data["ApiWorkerIdGTRR"]} sign result={signed}')

    if not signed:
        await message.answer(text=txt.sign_contract_error())
        return

    await state.clear()
    await db.update_user_gtrr(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        phone_number=data['PhoneNumberGTRR'],
        api_worker_id=data['ApiWorkerIdGTRR'],
        card=data['CardGTRR'],
    )
    await message.answer(text=txt.registration_user_completed(), reply_markup=kb.user_menu())


@router.callback_query(F.data == 'RejectContractGTRR')
async def reject_contract(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.set_state(None)
    await callback.message.answer(text=txt.contract_rejected_gtrr())
    await callback.message.delete()
