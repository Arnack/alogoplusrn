from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
import logging

from filters import Admin
import database as db
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.message(Command('registration_pic'))
async def request_registration_pic(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_manual_pic()
    )
    await state.set_state('RequestRegPic')


@router.message(F.document, StateFilter('RequestRegPic'))
async def get_registration_pic(
        message: Message,
        state: FSMContext
):
    try:
        await db.update_reg_pic(
            pic_id=message.document.file_id
        )
        await message.answer(
            text=txt.registration_pic_saved()
        )
    except Exception as e:
        await message.answer(
            text=txt.save_registration_pic_error()
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.set_state(None)


@router.message(Command('rr_manual_pic'))
async def request_rr_manual_pic(
        message: Message,
        state: FSMContext
):
    await message.answer(text=txt.request_manual_pic())
    await state.set_state('RequestRrManualPic')


@router.message(F.document, StateFilter('RequestRrManualPic'))
async def get_rr_manual_pic(
        message: Message,
        state: FSMContext
):
    try:
        await db.update_rr_manual_pic(pic_id=message.document.file_id)
        await message.answer(text=txt.registration_pic_saved())
    except Exception as e:
        await message.answer(text=txt.save_registration_pic_error())
        logging.exception(f'\n\n{e}')
    finally:
        await state.set_state(None)


@router.message(Command('smz_pic'))
async def request_smz_pic(message: Message, state: FSMContext):
    await message.answer('📷 Отправьте картинку «Как стать самозанятым» (фото или файл):')
    await state.set_state('RequestSMZPic')


@router.message(StateFilter('RequestSMZPic'))
async def get_smz_pic(message: Message, state: FSMContext):
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        else:
            await message.answer('❗ Отправьте фото или файл')
            return
        await db.update_smz_pic(pic_id=file_id)
        await message.answer('✅ Картинка «Как стать самозанятым» сохранена')
    except Exception as e:
        await message.answer('❗ Ошибка при сохранении')
        logging.exception(f'\n\n{e}')
    finally:
        await state.set_state(None)


@router.message(Command('rr_partner_pic'))
async def request_rr_partner_pic(message: Message, state: FSMContext):
    await message.answer('📷 Отправьте инструкцию «Подключение партнёра Рабочие Руки» (файл PDF или фото):')
    await state.set_state('RequestRRPartnerPic')


@router.message(StateFilter('RequestRRPartnerPic'))
async def get_rr_partner_pic(message: Message, state: FSMContext):
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        else:
            await message.answer('❗ Отправьте фото или файл')
            return
        await db.update_rr_partner_pic(pic_id=file_id)
        await message.answer('✅ Инструкция «Подключение партнёра РР» сохранена')
    except Exception as e:
        await message.answer('❗ Ошибка при сохранении')
        logging.exception(f'\n\n{e}')
    finally:
        await state.set_state(None)
