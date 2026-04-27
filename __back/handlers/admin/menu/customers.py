from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import logging

from utils import (
    check_auto_order_builder,
    schedule_auto_order_build,
    delete_auto_order_build,
    is_number
)
import database as db
from filters import Admin
import keyboards.inline as ikb
import keyboards.reply as kb
import texts as txt


router = Router()
router.message.filter(Admin())
router.callback_query.filter(Admin())


@router.callback_query(F.data.in_({'CustomerAddCancel', 'CustomersMenu'}))
@router.message(F.text == '🏢 Получатели услуг')
async def customers_main_menu(
        event: Message | CallbackQuery,
        state: FSMContext
):
    await state.clear()
    if isinstance(event, Message):
        await event.answer(
            text=txt.customers(),
            reply_markup=ikb.customers_menu()
        )
    else:
        await event.answer()
        await event.message.edit_text(
            text=txt.customers(),
            reply_markup=ikb.customers_menu()
        )


@router.callback_query(F.data == 'AllCustomers')
async def show_customers_list(
        callback: CallbackQuery
):
    await callback.answer()
    all_customers = await db.get_customers()

    if all_customers:
        await callback.message.edit_text(
            text=txt.customers_list(),
            reply_markup=await ikb.customers_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.customers_none(),
            reply_markup=ikb.customers_back()
        )


async def open_customer_info(
        callback: CallbackQuery,
        customer_id: int
) -> None:
    customer = await db.get_customer_full_info(
        customer_id=customer_id
    )
    auto_build = await check_auto_order_builder(
        customer_id=customer_id
    )
    _, email_sending_enabled = await db.get_customer_email_settings(customer_id)

    await callback.message.edit_text(
        text=txt.customer_info(
            organization=customer[0].organization,
            admins=customer[3],
            foremen=customer[4],
            customer_cities=customer[1],
            jobs=customer[2],
            customer_day_shift=customer[0].day_shift,
            customer_night_shift=customer[0].night_shift),
        reply_markup=ikb.customer_edit_menu(
            customer_id=customer_id,
            auto_order_builder=auto_build,
            email_sending_enabled=email_sending_enabled,
            travel_compensation=customer[0].travel_compensation
        )
    )


@router.callback_query(F.data.startswith('EnableAutoOrderBuilder:'))
async def enable_auto_order_builder(
        callback: CallbackQuery
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])
    await schedule_auto_order_build(
        customer_id=customer_id
    )
    await open_customer_info(
        callback=callback,
        customer_id=customer_id
    )


@router.callback_query(F.data.startswith('DisableAutoOrderBuilder:'))
async def disable_auto_order_builder(
        callback: CallbackQuery
):
    await callback.answer()
    customer_id = int(callback.data.split(':')[1])
    await delete_auto_order_build(
        customer_id=customer_id
    )
    await open_customer_info(
        callback=callback,
        customer_id=customer_id
    )


@router.callback_query(F.data.startswith('Customer:'))
async def customer_info(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await state.clear()

    customer_id = int(callback.data.split(':')[1])
    await open_customer_info(
        callback=callback,
        customer_id=customer_id
    )


@router.callback_query(F.data == 'AddCustomer')
async def add_customer(
        callback: CallbackQuery,
        state: FSMContext
):
    await callback.answer()
    await callback.message.edit_text(text=txt.add_customer_organization())
    await state.set_state("organization")


@router.message(F.text, StateFilter("organization"))
async def save_organization(
        message: Message,
        state: FSMContext
):
    await message.answer(
        text=txt.add_customer_cities(),
        reply_markup=kb.proceed()
    )
    await state.update_data(organization=message.text)
    await state.update_data(cities={})
    await state.set_state("cities")


@router.message(F.text, StateFilter("cities"))
async def save_city(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()

    if message.text in ['Пропустить', 'Далее']:
        if len(data['cities']) > 0:
            await message.answer(
                text=txt.add_customer_jobs()
            )
            await state.update_data(Jobs={})
            await state.set_state("JobName")
        else:
            await message.answer(
                text=txt.no_cities()
            )
    else:
        await state.set_state('CityWayDescription')
        await state.update_data(CurrentCity=message.text)
        await message.answer(
            text=txt.add_city_way_description()
        )


@router.message(F.text, StateFilter("CityWayDescription"))
async def save_city_way_description(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    cities = data.get('cities', {})

    if message.text.lower() == 'далее':
        await message.answer(text=txt.enter_city_way_description())
    else:
        cities[data['CurrentCity']] = {
            'CityWayDescription': message.text,
            'CityWayPhotos': []
        }
        await state.update_data(cities=cities)
        await message.answer(
            text=txt.add_city_way_photo(),
            reply_markup=kb.skip()
        )
        await state.set_state("CityWayPhotos")


@router.message(F.text, StateFilter("CityWayPhotos"))
@router.message(F.photo, StateFilter("CityWayPhotos"))
async def save_city_way_photos(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    cities = data.get('cities', {})
    city_photos = cities[data['CurrentCity']]['CityWayPhotos']

    if len(city_photos) + 1 < 3:
        if message.photo:
            city_photos.append(
                message.photo[-1].file_id
            )
            cities[data['CurrentCity']]['CityWayPhotos'] = city_photos
            await state.update_data(
                cities=cities
            )

    if message.text in ['Пропустить', 'Далее'] or len(city_photos) == 2:
        await message.answer(
            text=txt.add_city_more(),
            reply_markup=kb.proceed()
        )
        await state.set_state('cities')
    else:
        if len(city_photos) != 2:
            await message.reply(
                text=txt.add_city_way_photo_more(),
                reply_markup=kb.proceed()
            )


@router.message(F.text, StateFilter("JobName"))
async def save_job_name(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    jobs = data.get('Jobs', {})

    if message.text.lower() == 'далее':
        if len(jobs) > 0:
            await message.answer(text=txt.add_customer_admin_fio())
            await state.update_data(admins={})
            await state.set_state("admin_fio")
        else:
            await message.answer(text=txt.no_jobs())
    else:
        await state.set_state('JobAmount')
        await state.update_data(
            CurrentJob=message.text
        )
        await message.answer(
            text=txt.add_job_amount()
        )


@router.message(F.text, StateFilter("JobAmount"))
async def save_job_amount(
        message: Message,
        state: FSMContext
):
    if is_number(message.text):
        data = await state.get_data()
        jobs = data.get('Jobs', {})

        if message.text.lower() == 'далее':
            await message.answer(text=txt.enter_job_amount())
        else:
            jobs[data['CurrentJob']] = message.text
            await state.update_data(Jobs=jobs)
            await message.answer(
                text=txt.add_jobs_more()
            )
            await state.set_state("JobName")
    else:
        await message.answer(
            text=txt.add_id_error()
        )


@router.message(F.text.lower() == 'далее', StateFilter("admin_fio"))
@router.message(F.text, StateFilter("admin_fio"))
async def save_admin_fio(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    admins = data.get('admins', {})

    if message.text.lower() == 'далее':
        if len(admins) > 0:
            await message.answer(
                text=txt.add_customer_foreman_full_name()
            )
            await state.update_data(foremen={})
            await state.set_state("ForemanFullName")
        else:
            await message.answer(text=txt.none_admins())
    else:
        await state.set_state("admin_tg_id")
        await state.update_data(fio=message.text)
        await message.answer(text=txt.add_customer_admin_tg_id())


@router.message(F.text, StateFilter("admin_tg_id"))
async def save_admin_tg_id(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    admins = data.get('admins', {})

    if message.text.lower() == 'далее':
        await message.answer(text=txt.enter_tg_id())
    else:
        try:
            admins[data['fio']] = int(message.text)
            await state.update_data(admins=admins)
            await message.answer(text=txt.add_admins_more())
            await state.set_state("admin_fio")
        except ValueError:
            await message.answer(text=txt.add_id_error())


@router.message(F.text.lower() == 'далее', StateFilter("ForemanFullName"))
@router.message(F.text, StateFilter("ForemanFullName"))
async def save_foreman_full_name(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    foremen = data.get('foremen', {})

    if message.text.lower() == 'далее':
        if len(foremen) > 0:
            await message.answer(
                text=txt.day_shift(),
                reply_markup=kb.skip()
            )
            await state.set_state("day_shift")
        else:
            await message.answer(text=txt.no_foremen())
    else:
        await state.set_state("ForemenTgID")
        await state.update_data(ForemanFullName=message.text)
        await message.answer(text=txt.add_customer_foreman_tg_id())


@router.message(F.text.lower() == 'далее', StateFilter("ForemenTgID"))
@router.message(F.text, StateFilter("ForemenTgID"))
async def save_foreman_tg_id(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    foremen = data.get('foremen', {})

    if message.text.lower() == 'далее':
        await message.answer(text=txt.enter_foreman_tg_id())
    else:
        try:
            foremen[data['ForemanFullName']] = int(message.text)
            await state.update_data(foremen=foremen)
            await message.answer(text=txt.add_foremen_more())
            await state.set_state("ForemanFullName")
        except ValueError:
            await message.answer(text=txt.add_id_error())


@router.message(F.text, StateFilter("day_shift"))
async def save_day_shift(
        message: Message,
        state: FSMContext
):
    if message.text.lower() != 'пропустить':
        if '-' in message.text:
            await state.update_data(day_shift=message.text)
            await message.answer(text=txt.night_shift())
            await state.set_state("night_shift")
        else:
            await message.answer(text=txt.time_error())
    else:
        await state.update_data(day_shift=None)
        await message.answer(text=txt.night_shift())
        await state.set_state("night_shift")


@router.message(F.text, StateFilter("night_shift"))
async def save_night_shift(
        message: Message,
        state: FSMContext
):
    if message.text.lower() != 'пропустить':
        if '-' in message.text:
            await state.update_data(night_shift=message.text)
            await message.answer(
                text='.',
                reply_markup=kb.admin_menu()
            )
            data = await state.get_data()
            await message.answer(
                text=txt.confirmation_add_new_customer(
                    organization=data['organization'],
                    admins=data['admins'],
                    foremen=data['foremen'],
                    _customer_cities=data['cities'],
                    jobs=data['Jobs'],
                    customer_day_shift=data['day_shift'],
                    customer_night_shift=data['night_shift']),
                reply_markup=ikb.save_costumer()
            )
        else:
            await message.answer(text=txt.time_error())
    else:
        await state.update_data(night_shift=None)
        await message.answer(
            text='.',
            reply_markup=kb.admin_menu()
        )
        data = await state.get_data()
        await message.answer(
            text=txt.confirmation_add_new_customer(
                organization=data['organization'],
                admins=data['admins'],
                foremen=data['foremen'],
                _customer_cities=data['cities'],
                jobs=data['Jobs'],
                customer_day_shift=data['day_shift'],
                customer_night_shift=data['night_shift']),
            reply_markup=ikb.save_costumer()
        )


@router.callback_query(F.data == 'SaveCustomer')
async def save_customer(
        callback: CallbackQuery,
        state: FSMContext
):
    try:
        data = await state.get_data()

        await db.set_costumer(
            admins=data['admins'],
            foremen=data['foremen'],
            organization=data['organization'],
            day_shift=data['day_shift'],
            night_shift=data['night_shift'],
            cities=data['cities'],
            jobs=data['Jobs']
        )

        try:
            for tg_id in data['foremen'].values():
                await callback.bot.send_message(
                    chat_id=tg_id,
                    text=txt.forman_notification(
                        customer=data['organization']
                    ),
                    reply_markup=kb.foreman_menu()
                )
        except:
            pass

        await callback.answer(
            text=txt.customer_added(),
            show_alert=True
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.add_customer_error(),
            show_alert=True
        )
    finally:
        await state.clear()
        await callback.message.edit_text(
            text=txt.customers(),
            reply_markup=ikb.customers_menu()
        )


@router.callback_query(F.data.startswith('DeleteCustomer:'))
async def confirmation_delete_customer(
        callback: CallbackQuery
):
    customer_id = callback.data.split(':')[1]
    await callback.message.edit_text(
        text=txt.confirmation_delete_customer(),
        reply_markup=ikb.confirmation_delete_customer(
            customer_id=customer_id
        )
    )


@router.callback_query(F.data.startswith('ConfirmDeleteCustomer:'))
async def delete_customer(
        callback: CallbackQuery
):
    customer_id = int(callback.data.split(':')[1])
    all_customers = await db.get_customers_for_filter()

    await db.delete_customer(customer_id=customer_id)
    await callback.answer(
        text=txt.customer_deleted(),
        show_alert=True
    )

    if all_customers:
        await callback.message.edit_text(
            text=txt.customers_list(),
            reply_markup=await ikb.customers_list()
        )
    else:
        await callback.message.edit_text(
            text=txt.customers_none(),
            reply_markup=ikb.customers_back()
        )
