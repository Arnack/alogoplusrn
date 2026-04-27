from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaDocument
from aiogram.fsm.context import FSMContext
import asyncio
import logging

from API.fin.contracts import fin_get_worker_contracts_with_pdfs
from utils.organizations import orgs_dict
from filters import Worker
import texts as txt


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())

ORG_IDS = [392, 393, 480]


async def download_and_send_contracts(
        callback: CallbackQuery,
        state: FSMContext,
) -> None:
    try:
        api_worker_id = int(callback.data.split(':')[1])

        contracts = await fin_get_worker_contracts_with_pdfs(api_worker_id, ORG_IDS)
        if not contracts:
            await callback.message.answer(text='ℹ️ Договоры не найдены')
            return

        docs = []
        for contract in contracts:
            pdf_bytes = contract.get('pdf')
            org_id = contract.get('org_id')
            if pdf_bytes:
                org_name = orgs_dict.get(org_id, f'ИП {org_id}')
                docs.append((pdf_bytes, org_name))
                logging.info(f'[contracts] org={org_id} id={contract.get("id")} pdf={len(pdf_bytes)}b')

        if not docs:
            await callback.message.answer(text='❗ Не удалось загрузить договоры')
            return

        if len(docs) == 1:
            pdf_bytes, org_name = docs[0]
            await callback.message.answer_document(
                document=BufferedInputFile(
                    file=pdf_bytes,
                    filename=f'Договор_{org_name}.pdf',
                ),
            )
        else:
            await callback.message.answer_media_group(
                media=[
                    InputMediaDocument(
                        media=BufferedInputFile(
                            file=pdf_bytes,
                            filename=f'Договор_{org_name}.pdf',
                        ),
                    ) for pdf_bytes, org_name in docs
                ],
            )
    except Exception:
        logging.exception('[contracts] download_and_send_contracts error')
        await callback.message.answer(text='❗ Произошла ошибка при загрузке договоров')
    finally:
        await state.update_data(ContractsSending=False)


@router.callback_query(F.data.startswith('GetWorkerContracts:'))
async def show_worker_contracts(
        callback: CallbackQuery,
        state: FSMContext,
):
    data = await state.get_data()

    if data.get('ContractsSending'):
        await callback.answer(
            text=txt.contracts_sending_error(),
            show_alert=True,
        )
        return

    await callback.answer(
        text=txt.contracts_sending_info(),
        show_alert=True,
    )
    await state.update_data(ContractsSending=True)
    asyncio.create_task(
        download_and_send_contracts(
            callback=callback,
            state=state,
        )
    )
