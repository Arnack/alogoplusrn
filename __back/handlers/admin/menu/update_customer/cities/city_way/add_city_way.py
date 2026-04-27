from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from handlers.admin.menu.update_customer.cities.city.update_city import show_update_city_menu
import keyboards.inline as ikb
import keyboards.reply as kb
from filters import Admin
import database as db
import texts as txt


router = Router()


@router.callback_query(Admin(), F.data.startswith('UpdateCityWay:'))
@router.callback_query(Admin(), F.data.startswith('AddCityWay:'))
async def add_new_city_way(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    action = 'NewCityWay' if callback.data.startswith('AddCityWay:') else 'UpdateCityWay'
    await state.update_data(
        city_id=int(callback.data.split(':')[1]),
        CityWayAction=action
    )
    await callback.message.edit_text(
        text=txt.add_city_way_description()
    )
    await state.set_state('NewCityWayDescription')


@router.message(Admin(), F.text, StateFilter('NewCityWayDescription'))
async def get_city_way(
        message: Message,
        state: FSMContext
):
    await state.update_data(
        CityWayDescription=message.text,
        CityWayPhotos=[]
    )
    await message.answer(
        text=txt.add_city_way_photo(),
        reply_markup=kb.skip()
    )
    await state.set_state('NewCityWayPhotos')


@router.message(Admin(), F.text, StateFilter("NewCityWayPhotos"))
@router.message(Admin(), F.photo, StateFilter("NewCityWayPhotos"))
async def save_city_way_photos(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    city_photos = data.get('CityWayPhotos', [])

    if len(city_photos) + 1 < 3:
        if message.photo:
            city_photos.append(
                message.photo[-1].file_id
            )
            await state.update_data(
                CityWayPhotos=city_photos
            )

    if message.text in ['Пропустить', 'Далее'] or len(city_photos) == 2:
        await message.answer(
            text=txt.confirmation_save_city_way(),
            reply_markup=ikb.confirmation_update_city_way(
                city_id=data['city_id']
            )
        )
        await state.set_state('ConfirmationSaveCityWay')
    else:
        if len(city_photos) != 2:
            await message.reply(
                text=txt.add_city_way_photo_more(),
                reply_markup=kb.proceed()
            )


@router.callback_query(
    Admin(),
    F.data.startswith('ConfirmUpdateCityWay:'),
    StateFilter('ConfirmationSaveCityWay')
)
async def confirm_save_city_way(
        callback: CallbackQuery,
        state: FSMContext
):
    data = await state.get_data()
    try:
        city_id = int(callback.data.split(':')[1])

        if data['CityWayAction'] == 'NewCityWay':
            await db.set_customer_city_way(
                city_id=city_id,
                way_description=data['CityWayDescription'],
                way_photos=data['CityWayPhotos']
            )
            await callback.answer(
                text=txt.city_way_added(),
                show_alert=True
            )
        else:
            await db.update_customer_city_way(
                city_id=city_id,
                way_description=data['CityWayDescription'],
                way_photos=data['CityWayPhotos']
            )
            await callback.answer(
                text=txt.city_way_updated(),
                show_alert=True
            )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.add_city_way_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await state.update_data(
            customer_id=data['customer_id']
        )
        await callback.message.answer(
            text='.',
            reply_markup=kb.admin_menu()
        )
        await show_update_city_menu(
            callback=callback,
            state=state
        )
