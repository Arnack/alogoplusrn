from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from handlers.user.menu.about_worker import show_info_about_worker
import keyboards.inline as ikb
from filters import Worker
import database as db
import texts as txt


router = Router()


@router.callback_query(Worker(), F.data == 'UpdateWorkerCity')
async def request_change_city(
        callback: CallbackQuery
):
    await callback.answer()
    await callback.message.edit_text(
        text=txt.choose_city(),
        reply_markup=await ikb.cities_for_change()
    )


@router.callback_query(Worker(), F.data.startswith('ChangeCity:'))
async def change_city(callback: CallbackQuery):
    await callback.answer()
    city_id = int(callback.data.split(':')[1])
    user = await db.get_user(
        tg_id=callback.from_user.id
    )
    new_city = await db.get_city_by_id(
        city_id=city_id,
    )

    await callback.message.edit_text(
        text=txt.confirmation_update_city(
            old_city=user.city,
            new_city=new_city.city_name,
        ),
        reply_markup=ikb.confirmation_update_city_worker(
            city_id=city_id,
            worker_id=user.id
        )
    )


@router.callback_query(Worker(), ikb.UpdateCityUser.filter(F.action == 'ConfirmUpdCity'))
async def confirm_update_city_handler(
        callback: CallbackQuery,
        callback_data: ikb.UpdateCityUser
):
    try:
        managers = await db.get_managers_tg_id()
        directors = await db.get_directors_tg_id()
        recipients = list(managers) + list(directors)
        worker = await db.get_user_with_data_for_security(
            tg_id=callback.from_user.id
        )
        request_id = await db.set_change_city_request(
            worker_id=worker.id
        )
        city = await db.get_city_by_id(
            city_id=callback_data.new_city_id,
        )

        for tg_id in recipients:
            try:
                await callback.bot.send_message(
                    chat_id=tg_id,
                    text=txt.request_to_change_city_for_manager(
                        worker_full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                        old_city=worker.city,
                        new_city=city.city_name,
                    ),
                    reply_markup=ikb.confirmation_update_city_manager(
                        request_id=request_id,
                        new_city_id=callback_data.new_city_id,
                        worker_id=callback_data.worker_id
                    )
                )
            except Exception as e:
                logging.exception(f'\n\n{e}')
        await callback.answer(
            text=txt.request_to_change_city_sent(),
            show_alert=True
        )
    except Exception as e:
        logging.exception( f'\n\n{e}')
        await callback.answer(
            text=txt.request_to_change_city_error(),
            show_alert=True
        )
    finally:
        await show_info_about_worker(
            event=callback
        )
