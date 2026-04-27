import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import NoReturn

from handlers.admin.menu.customers import open_customer_info
import keyboards.inline as ikb
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerCities:'))
async def update_customer_city(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    customer_id = int(callback.data.split(':')[1])
    await state.update_data(customer_id=customer_id)

    await callback.message.edit_text(
        text=txt.customer_cities_list(),
        reply_markup=await ikb.customer_cities(
            customer_id=customer_id
        )
    )


async def show_update_city_menu(
        callback: CallbackQuery,
        state: FSMContext
) -> NoReturn:
    await callback.answer()
    city_id = int(callback.data.split(':')[1])
    data = await state.get_data()

    await callback.message.edit_text(
        text=txt.choose_customer_city_update(),
        reply_markup=ikb.choose_customer_city_update(
            customer_id=data['customer_id'],
            city_id=city_id
        )
    )
    await state.clear()
    await state.update_data(
        customer_id=data['customer_id']
    )


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerCity:'))
async def update_city_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    await show_update_city_menu(
        callback=callback,
        state=state
    )


@router.callback_query(Admin(), F.data.startswith('UpdateCustomerCityName:'))
async def get_new_city_name(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()

    city_id = int(callback.data.split(':')[1])
    await state.update_data(city_id=city_id)
    await state.set_state('UpdateCity')

    await callback.message.edit_text(
        text=txt.update_city()
    )


@router.message(Admin(), F.text, StateFilter('UpdateCity'))
async def confirmation_save_city(
        message: Message,
        state: FSMContext
):
    await state.update_data(new_city=message.text)
    data = await state.get_data()
    organization = await db.get_customer_organization(customer_id=data['customer_id'])

    await message.answer(
        text=txt.confirmation_update_city_for_customer(
            organization=organization,
            city=message.text
        ),
        reply_markup=ikb.confirmation_update_city(
            customer_id=data['customer_id']
        )
    )


@router.callback_query(Admin(), F.data == 'UpdateNewCity')
async def update_city(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        await db.update_city(
            city=data['new_city'],
            city_id=data['city_id']
        )
        await callback.answer(
            text=txt.city_updated(),
            show_alert=True
        )
    except Exception as e:
        await callback.answer(
            text=txt.update_city_error(),
            show_alert=True
        )
        logging.exception(f'\n\n{e}')
    finally:
        await open_customer_info(
            callback=callback,
            customer_id=data['customer_id']
        )
        await state.clear()
