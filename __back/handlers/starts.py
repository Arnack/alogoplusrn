import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from filters import (
    Admin, Customer,
    Manager, Foreman,
    Accountant, Supervisor,
    Director
)
import texts as txt
import database as db
import keyboards.reply as kb
import keyboards.inline as ikb


router = Router()


@router.message(Admin(), F.text == '🗂️ Главное меню')
@router.message(Admin(), CommandStart())
async def cmd_start_admin(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.start_admin(),
        reply_markup=kb.admin_menu()
    )


@router.message(Accountant(), F.text == '🗂️ Главное меню')
@router.message(Accountant(), CommandStart())
async def cmd_start_accountant(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.start_accountant(),
        reply_markup=kb.accountant_menu()
    )


@router.message(Customer(), CommandStart())
async def cmd_start_customer(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.start_customer(),
        reply_markup=kb.customer_menu()
    )


@router.message(Manager(), CommandStart())
async def cmd_start_manager(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.start_manager(),
        reply_markup=kb.manager_menu()
    )


@router.message(Director(), CommandStart())
async def cmd_start_director(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.start_director(),
        reply_markup=kb.director_menu()
    )


@router.message(Admin(), Command('chat_id'))
async def cmd_start_admin(
        message: Message,
):
    await message.answer(
        text=txt.show_chat_id(
            chat_id=message.chat.id
        )
    )


@router.message(Supervisor(), CommandStart())
async def cmd_start_foreman(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.restart_bot(),
        reply_markup=kb.supervisor_menu(),
        protect_content=True
    )


@router.message(Foreman(), CommandStart())
async def cmd_start_foreman(
        message: Message,
        state: FSMContext
):
    await state.set_state(None)
    await message.answer(
        text=txt.restart_bot(),
        reply_markup=kb.foreman_menu(),
        protect_content=True
    )


@router.message(CommandStart())
@router.message(CommandStart(deep_link=True))
async def cmd_start_worker(
        message: Message,
        state: FSMContext,
        command: CommandObject
):
    await state.clear()
    user = await db.get_user(
        tg_id=message.from_user.id
    )

    if user:
        await message.answer(
            text=txt.restart_bot(),
            reply_markup=kb.user_menu(),
            protect_content=True
        )
    else:
        await message.answer(
            text=(
                '👋 Добро пожаловать на Платформу «Алгоритм Плюс»\n\n'
                '📌 Платформа для самозанятых\n'
                'Вы сами выбираете заявки и оказываете услуги, когда удобно — без графиков и начальников\n\n'
                '💰 Вознаграждение — сразу после оказания услуг\n\n'
                '🔐 Уже проходили регистрацию через «Рабочие Руки»?\n'
                '➡️ Просто войдите по номеру телефона\n\n'
                '🆕 Впервые на платформе?\n'
                '➡️ Пройдите регистрацию — это займёт пару минут\n\n'
                'Понадобится:\n'
                '👤 ФИО • 📅 дата рождения • 🆔 ИНН\n'
                '📱 телефон\n'
                '💳 любая карта только для получения вознаграждения\n'
                '🪪 паспорт (серия, номер, дата выдачи)\n\n'
                '👇 Выберите действие'
            ),
            reply_markup=ikb.entry_choice(),
            protect_content=True
        )
    if command.args:
        try:
            user = int(command.args.split('_')[1])
            await db.set_ref(
                referral_tg_id=message.from_user.id,
                user_id=user
            )
        except Exception as e:
            logging.exception(f'\n\n{e}')
