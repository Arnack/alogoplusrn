from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from filters import Admin
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.in_({'ManagerAddCancel', 'ManagersMenu'}))
@router.message(Admin(), F.text == '👥 Менеджеры')
async def managers_main_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    await state.clear()
    if isinstance(event, Message):
        await event.answer(
            text=txt.managers(),
            reply_markup=ikb.managers_menu()
        )
    else:
        await event.answer()
        await event.message.edit_text(
            text=txt.managers(),
            reply_markup=ikb.managers_menu()
        )


@router.callback_query(Admin(), F.data == 'AllManagers')
async def show_managers_list(
        callback: CallbackQuery
):
    await callback.answer()
    all_managers = await db.get_managers_tg_id()

    if all_managers:
        await callback.message.edit_text(
            text=txt.managers_list(),
            reply_markup=await ikb.managers_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.managers_none(),
            reply_markup=ikb.managers_back()
        )


@router.callback_query(Admin(), F.data.startswith('Manager:'))
async def manager_info(
        callback: CallbackQuery
):
    await callback.answer()
    manager_id = int(callback.data.split(':')[1])
    manager = await db.get_manager(manager_tg_id=manager_id)

    await callback.message.edit_text(
        text=txt.manager_info(
            name=manager.manager_full_name,
            manager_id=manager_id
        ),
        reply_markup=ikb.delete_manager(
            manager_id=manager_id
        )
    )


@router.callback_query(Admin(), F.data == 'AddManager')
async def add_manager(
        callback: CallbackQuery, state: FSMContext
):
    await callback.message.edit_text(text=txt.add_manager_full_name())
    await state.set_state("manager_full_name")


@router.message(Admin(), F.text, StateFilter("manager_full_name"))
async def save_manager_full_name(
        message: Message,
        state: FSMContext
):
    await message.answer(text=txt.add_manager_id())
    await state.update_data(manager_full_name=message.text)
    await state.set_state("manager_id")


@router.message(Admin(), F.text, StateFilter("manager_id"))
async def save_manager_id(
        message: Message,
        state: FSMContext
):
    try:
        data = await state.get_data()
        await state.update_data(manager_id=int(message.text))
        await message.answer(
            text=txt.accept_new_manager(
                manager=message.text,
                name=data['manager_full_name']
            ),
            reply_markup=ikb.save_manager()
        )
    except ValueError:
        await message.answer(text=txt.add_id_error())


@router.callback_query(Admin(), F.data == 'SaveManager')
async def save_manager(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()

    await db.set_manager(
        manager_full_name=data['manager_full_name'],
        manager_id=data['manager_id']
    )
    await callback.answer(
        text=txt.manager_added(),
        show_alert=True
    )
    await callback.message.edit_text(
        text=txt.managers(),
        reply_markup=ikb.managers_menu()
    )
    await state.clear()


@router.callback_query(Admin(), F.data.startswith('DeleteManager'))
async def delete_manager(
        callback: CallbackQuery
):
    manager_id = int(callback.data.split(':')[1])
    all_managers = await db.get_managers_tg_id()

    await db.delete_manager(manager_id=manager_id)
    await callback.answer(
        text=txt.manager_deleted(),
        show_alert=True
    )

    if all_managers:
        await callback.message.edit_text(
            text=txt.managers_list(),
            reply_markup=await ikb.managers_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.managers_none(),
            reply_markup=ikb.managers_back()
        )
