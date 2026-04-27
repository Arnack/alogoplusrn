import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.filters import or_f
from datetime import datetime

from utils import validate_date
import texts as txt
import keyboards.inline as ikb
import database as db
from filters import Customer, Admin, Director


router = Router()


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data == 'AddOrder')
async def new_order(
        callback: CallbackQuery,
):
    await callback.message.edit_text(
        text=txt.add_order_date_button(),
        reply_markup=await ikb.customer_date_list()
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('Date:'))
async def save_date_in_button(
        callback: CallbackQuery,
        state: FSMContext
):
    date = callback.data.split(':')[1]
    await state.update_data(date=date)
    await callback.message.edit_text(text=txt.add_order_workers())
    await state.set_state("Workers")


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data == 'InputDate')
async def input_date(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.message.edit_text(text=txt.add_order_date())
    await state.set_state("InputDate")


@router.message(or_f(Customer(), Admin(), Director()), F.text, StateFilter("InputDate"))
async def save_date(
        message: Message,
        state: FSMContext
):
        is_valid, formatted_date = validate_date(
            date_str=message.text
        )
        if is_valid:
            await state.update_data(date=formatted_date)
            await message.answer(text=txt.add_order_workers())
            await state.set_state("Workers")
        else:
            await message.answer("❗Неверный формат даты. Попробуйте снова:")


@router.message(or_f(Customer(), Admin(), Director()), F.text, StateFilter("Workers"))
async def save_workers(
        message: Message,
        state: FSMContext
):
    try:
        await state.update_data(workers=int(message.text))
        data = await state.get_data()
        admin_id = data.get('admin_as_customer_id', message.from_user.id)
        await message.answer(
            text=txt.add_order_job(),
            reply_markup=await ikb.customer_jobs_list(
                admin=admin_id
            )
        )
        await state.set_state("Job")
    except ValueError:
        await message.answer(text='❗Введите число:')


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('SetOrderJob:'), StateFilter("Job"))
async def save_job(
        callback: CallbackQuery,
        state: FSMContext
):
    job = callback.data.split(':')[1]
    data = await state.get_data()
    admin_id = data.get('admin_as_customer_id', callback.from_user.id)
    await callback.message.edit_text(
        text=txt.add_order_shift(),
        reply_markup=await ikb.customer_shifts(
            admin=admin_id
        )
    )
    await state.update_data(job=job)
    await state.set_state("Shift")


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('OrderSetDayShift:'), StateFilter("Shift"))
async def save_day_shift(
        callback: CallbackQuery,
        state: FSMContext
):
    time = callback.data.split(':', maxsplit=1)[1]
    await state.update_data(day_shift=time)
    await state.update_data(night_shift=None)
    data = await state.get_data()
    admin_id = data.get('admin_as_customer_id', callback.from_user.id)
    await callback.message.edit_text(
        text=txt.order_cities(),
        reply_markup=await ikb.customer_cities_list(
            admin=admin_id
        )
    )
    await state.set_state("ChooseCity")


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('OrderSetNightShift:'), StateFilter("Shift"))
async def save_night_shift(
        callback: CallbackQuery,
        state: FSMContext
):
    shift = callback.data.split(':', maxsplit=1)[1]
    await state.update_data(night_shift=shift)
    await state.update_data(day_shift=None)
    data = await state.get_data()
    admin_id = data.get('admin_as_customer_id', callback.from_user.id)
    await callback.message.edit_text(
        text=txt.order_cities(),
        reply_markup=await ikb.customer_cities_list(
            admin=admin_id
        )
    )
    await state.set_state("ChooseCity")


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data.startswith('OrderCity:'), StateFilter("ChooseCity"))
async def order_cities(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.update_data(city=callback.data.split(':')[1])
    data = await state.get_data()
    shift = data['day_shift'] if data['day_shift'] else data['night_shift']

    await callback.message.edit_text(
        text=txt.accept_new_order(
            job=data['job'],
            date=data['date'],
            shift=shift,
            workers=data['workers'],
            city=data['city']),
        reply_markup=ikb.save_order(),
        parse_mode='HTML'
    )


@router.callback_query(or_f(Customer(), Admin(), Director()), F.data == 'SaveOrder')
async def save_order(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        data = await state.get_data()
        admin_id = data.get('admin_as_customer_id', callback.from_user.id)

        await db.set_order(
            admin=admin_id,
            job_name=data['job'],
            date=data['date'],
            day_shift=data['day_shift'],
            night_shift=data['night_shift'],
            workers=data['workers'],
            city=data['city']
        )

        await callback.answer(
            text=txt.order_added(),
            show_alert=True
        )

        managers = await db.get_managers_tg_id()
        directors = await db.get_directors_tg_id()
        recipients = list(managers) + list(directors)
        for manager in recipients:
            try:
                await callback.bot.send_message(
                    chat_id=manager,
                    text=txt.new_order_notification()
                )
            except:
                pass
    except Exception as e:
        await callback.answer(
            text=txt.order_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await state.clear()
        await callback.message.edit_text(
            text=txt.orders(),
            reply_markup=ikb.order_management()
        )
