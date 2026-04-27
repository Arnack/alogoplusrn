from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from filters import Admin
import keyboards.inline as ikb
import database as db
import texts as txt

router = Router()

# === ГЛАВНОЕ МЕНЮ РОЛЕЙ ===

@router.callback_query(Admin(), F.data == 'RolesMenuBack')
@router.message(Admin(), F.text == '🎭 Роли')
async def roles_main_menu(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    if isinstance(event, Message):
        await event.answer(text=txt.roles_menu(), reply_markup=ikb.roles_menu())
    else:
        await event.answer()
        await event.message.edit_text(text=txt.roles_menu(), reply_markup=ikb.roles_menu())

# === ДИРЕКТОРА ===

@router.callback_query(Admin(), F.data.in_({'DirectorsMenu', 'DirectorAddCancel'}))
async def directors_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        text=txt.directors(),
        reply_markup=ikb.directors_menu()
    )

@router.callback_query(Admin(), F.data == 'AllDirectors')
async def show_directors_list(callback: CallbackQuery):
    await callback.answer()
    all_directors = await db.get_directors()

    if all_directors:
        await callback.message.edit_text(
            text=txt.directors_list(),
            reply_markup=await ikb.directors_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.directors_none(),
            reply_markup=ikb.directors_back()
        )

@router.callback_query(Admin(), F.data.startswith('Director:'))
async def director_info(callback: CallbackQuery):
    await callback.answer()
    director_tg_id = int(callback.data.split(':')[1])
    director = await db.get_director_by_tg_id(tg_id=director_tg_id)

    await callback.message.edit_text(
        text=txt.director_info(
            name=director.full_name,
            tg_id=director_tg_id
        ),
        reply_markup=ikb.delete_director(director_id=director.id)
    )

@router.callback_query(Admin(), F.data == 'AddDirector')
async def add_director(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=txt.add_director_full_name())
    await state.set_state("director_full_name")

@router.message(Admin(), F.text, StateFilter("director_full_name"))
async def save_director_full_name(message: Message, state: FSMContext):
    await message.answer(text=txt.add_director_tg_id())
    await state.update_data(director_full_name=message.text)
    await state.set_state("director_tg_id")

@router.message(Admin(), F.text, StateFilter("director_tg_id"))
async def save_director_tg_id(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        await state.update_data(director_tg_id=int(message.text))
        await message.answer(
            text=txt.accept_new_director(
                name=data['director_full_name'],
                tg_id=message.text
            ),
            reply_markup=ikb.save_director()
        )
    except ValueError:
        await message.answer(text=txt.add_id_error())

@router.callback_query(Admin(), F.data == 'SaveDirector')
async def save_director(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await db.set_director(
        full_name=data['director_full_name'],
        tg_id=data['director_tg_id']
    )
    await callback.answer(text=txt.director_added(), show_alert=True)
    await callback.message.edit_text(
        text=txt.directors(),
        reply_markup=ikb.directors_menu()
    )
    await state.clear()

@router.callback_query(Admin(), F.data.startswith('DeleteDirector:'))
async def delete_director(callback: CallbackQuery):
    director_id = int(callback.data.split(':')[1])
    all_directors = await db.get_directors()

    await db.delete_director(director_id=director_id)
    await callback.answer(text=txt.director_deleted(), show_alert=True)

    if len(all_directors) > 1:
        await callback.message.edit_text(
            text=txt.directors_list(),
            reply_markup=await ikb.directors_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.directors_none(),
            reply_markup=ikb.directors_back()
        )

# === КООРДИНАТОРЫ (ПЕРЕИСПОЛЬЗУЕМ ИЗ СУЩЕСТВУЮЩЕГО) ===

@router.callback_query(Admin(), F.data == 'RoleCoordinators')
async def coordinators_redirect(callback: CallbackQuery, state: FSMContext):
    from handlers.admin.menu.supervisors import supervisors_main_menu
    await supervisors_main_menu(callback, state)

# === КАССИРЫ (ПЕРЕИСПОЛЬЗУЕМ ИЗ СУЩЕСТВУЮЩЕГО) ===

@router.callback_query(Admin(), F.data == 'RoleCashiers')
async def cashiers_redirect(callback: CallbackQuery, state: FSMContext):
    from handlers.admin.menu.accountant import accountants_main_menu
    await accountants_main_menu(callback, state)

# === МЕНЕДЖЕРЫ (ПЕРЕИСПОЛЬЗУЕМ ИЗ СУЩЕСТВУЮЩЕГО) ===

@router.callback_query(Admin(), F.data == 'RoleManagers')
async def managers_redirect(callback: CallbackQuery, state: FSMContext):
    from handlers.admin.menu.managers import managers_main_menu
    await managers_main_menu(callback, state)
