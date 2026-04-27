from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from filters import Admin
import keyboards.inline as ikb
import database as db
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.callback_query(F.data == 'SupervisorsMenu')
@router.message(F.text == '🦺 Координаторы')
async def supervisors_main_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    await state.clear()
    if isinstance(event, Message):
        await event.answer(
            text=txt.supervisors(),
            reply_markup=ikb.supervisors_menu()
        )
    else:
        await event.answer()
        await event.message.edit_text(
            text=txt.supervisors(),
            reply_markup=ikb.supervisors_menu()
        )


@router.callback_query(F.data == 'AllSupervisors')
async def show_supervisors_list(
        callback: CallbackQuery
):
    await callback.answer()
    all_supervisors = await db.get_supervisors()

    if all_supervisors:
        await callback.message.edit_text(
            text=txt.supervisors_list(),
            reply_markup=ikb.supervisors_list(
                supervisors=all_supervisors
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_supervisors(),
            reply_markup=ikb.supervisors_back()
        )


@router.callback_query(F.data.startswith('Supervisor:'))
async def supervisor_info(
        callback: CallbackQuery
):
    await callback.answer()
    supervisor_id = int(callback.data.split(':')[1])
    supervisor = await db.get_supervisor(
        supervisor_id=supervisor_id
    )

    await callback.message.edit_text(
        text=txt.supervisor_info(
            full_name=supervisor.full_name,
            tg_id=supervisor.tg_id
        ),
        reply_markup=ikb.delete_supervisor(
            supervisor_id=supervisor_id
        )
    )


@router.callback_query(F.data == 'AddSupervisor')
async def add_supervisor(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_text(
        text=txt.request_supervisor_full_name()
    )
    await state.set_state("SupervisorFullName")


@router.message(F.text, StateFilter("SupervisorFullName"))
async def get_supervisor_full_name(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.request_supervisor_tg_id()
    )
    await state.update_data(
        SupervisorFullName=message.text
    )
    await state.set_state("SupervisorTgID")


@router.message(F.text, StateFilter("SupervisorTgID"))
async def get_supervisor_tg_id(
        message: Message,
        state: FSMContext
):
    if message.text.isdigit():
        await state.set_state(None)
        data = await state.get_data()
        await message.answer(
            text=txt.confirmation_add_new_supervisor(
                tg_id=message.text,
                full_name=data['SupervisorFullName']
            ),
            reply_markup=ikb.confirmation_add_new_supervisor()
        )
        await state.update_data(
            SupervisorTgID=int(message.text)
        )
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.callback_query(F.data == 'SaveSupervisor')
async def save_supervisor(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.set_supervisor(
            full_name=data['SupervisorFullName'],
            tg_id=data['SupervisorTgID']
        )
        await callback.answer(
            text=txt.supervisor_added(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(
            f'\n\n{e}'
        )
        await callback.answer(
            text=txt.add_supervisor_error(),
            show_alert=True
        )
    finally:
        await callback.message.edit_text(
            text=txt.supervisors(),
            reply_markup=ikb.supervisors_menu()
        )
        await state.clear()


@router.callback_query(F.data.startswith('DeleteSupervisor:'))
async def confirmation_delete_supervisor(
        callback: CallbackQuery
):
    await callback.message.edit_text(
        text=txt.confirmation_delete_supervisor(),
        reply_markup=ikb.confirmation_delete_supervisor(
            supervisor_id=int(callback.data.split(':')[1])
        )
    )


@router.callback_query(F.data.startswith('ConfirmDeleteSupervisor:'))
async def confirm_delete_supervisor(
        callback: CallbackQuery
):
    await db.delete_supervisor(
        supervisor_id=int(callback.data.split(':')[1])
    )
    all_supervisors = await db.get_supervisors()
    await callback.answer(
        text=txt.supervisor_deleted(),
        show_alert=True
    )

    if all_supervisors:
        await callback.message.edit_text(
            text=txt.supervisors_list(),
            reply_markup=ikb.supervisors_list(
                supervisors=all_supervisors
            )
        )
    else:
        await callback.message.edit_text(
            text=txt.no_supervisors(),
            reply_markup=ikb.supervisors_back()
        )
