from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import texts as txt
import keyboards.reply as kb
import database as db
from filters import Admin


router = Router()


@router.message(Admin(), F.text == '⚙️ Настройки')
async def open_setting(
        message: Message
):
    settings = await db.get_settings()
    await message.answer(
        text=txt.admin_settings(
            shifts=settings.shifts,
            bonus=settings.bonus
        ),
        reply_markup=kb.admin_settings()
    )


@router.message(Admin(), F.text == '📝 Количество выходов')
async def update_shifts(
        message: Message,
        state: FSMContext
):
    await message.answer(text=txt.update_shifts())
    await state.set_state("set_shifts")


@router.message(Admin(), F.text, StateFilter("set_shifts"))
async def set_shifts(
        message: Message,
        state: FSMContext
):
    try:
        await db.update_shifts(int(message.text))
        await message.answer(
            text=txt.save_settings(),
            reply_markup=kb.admin_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(text=txt.number_error())


@router.message(Admin(), F.text == '💸 Размер бонуса')
async def update_bonus(
        message: Message,
        state: FSMContext
):
    await message.answer(text=txt.update_bonus())
    await state.set_state("set_bonus")


@router.message(Admin(), F.text, StateFilter("set_bonus"))
async def set_bonus(
        message: Message,
        state: FSMContext
):
    try:
        await db.update_bonus(int(message.text))
        await message.answer(
            text=txt.save_settings(),
            reply_markup=kb.admin_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(text=txt.number_error())
