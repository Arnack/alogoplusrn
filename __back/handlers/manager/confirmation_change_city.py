from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

import keyboards.inline as ikb
from filters import Manager, Director
from aiogram.filters import Filter
from aiogram.types import CallbackQuery as CQ


class ManagerOrDirector(Filter):
    async def __call__(self, event: CQ):
        return await Manager()(event) or await Director()(event)
import database as db
import texts as txt
from config_reader import config as cfg


router = Router()


@router.callback_query(ManagerOrDirector(), ikb.UpdateCityManager.filter(F.action == 'ConfirmUpdCity'))
async def confirm_update_city_handler(
        callback: CallbackQuery,
        callback_data: ikb.UpdateCityManager
):
    try:
        request = await db.get_change_city_request(
            request_id=callback_data.request_id
        )
        if not request.changed:
            city = await db.get_city_by_id(
                city_id=callback_data.new_city
            )
            await db.update_user_city(
                worker_id=callback_data.worker_id,
                city=city.city_name
            )
            await db.complete_change_city_request(
                request_id=callback_data.request_id
            )
            worker = await db.get_user_by_id(
                user_id=callback_data.worker_id
            )
            notification_text = txt.notification_city_changed(city=city.city_name)
            if worker.tg_id:
                try:
                    await callback.bot.send_message(
                        chat_id=worker.tg_id,
                        text=notification_text
                    )
                except Exception as e:
                    logging.exception(f'\n\n{e}')
            if worker.max_id and cfg.max_bot_token:
                try:
                    from maxapi import Bot as MaxBot
                    from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                    max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                    await max_bot.send_message(user_id=worker.max_id, text=notification_text, parse_mode=MaxParseMode.HTML)
                    await max_bot.session.close()
                except Exception as e:
                    logging.exception(f'\n\n{e}')
            await callback.answer(
                text=txt.city_for_worker_updated(),
                show_alert=True
            )
        else:
            await callback.answer(
                text=txt.request_was_handle_another_manager(),
                show_alert=True
            )
    except Exception as e:
        logging.exception(
            f'\n\n{e}'
        )
        await callback.answer(
            text=txt.update_city_for_worker_error(),
            show_alert=True
        )
    finally:
        await callback.message.delete()


@router.callback_query(ManagerOrDirector(), ikb.UpdateCityManager.filter(F.action == 'CancelUpdCity'))
async def cancel_update_city_handler(
        callback: CallbackQuery,
        callback_data: ikb.UpdateCityManager
):
    try:
        request = await db.get_change_city_request(
            request_id=callback_data.request_id
        )
        if not request.changed:
            await db.complete_change_city_request(
                request_id=callback_data.request_id
            )
            await callback.answer(
                text=txt.update_city_canceled(),
                show_alert=True
            )
            try:
                worker = await db.get_user_by_id(
                    user_id=callback_data.worker_id
                )
                notification_text = txt.notification_city_not_changed(city=worker.city)
                if worker.tg_id:
                    await callback.bot.send_message(
                        chat_id=worker.tg_id,
                        text=notification_text
                    )
                if worker.max_id and cfg.max_bot_token:
                    try:
                        from maxapi import Bot as MaxBot
                        from maxapi.enums.parse_mode import ParseMode as MaxParseMode
                        max_bot = MaxBot(token=cfg.max_bot_token.get_secret_value())
                        await max_bot.send_message(user_id=worker.max_id, text=notification_text, parse_mode=MaxParseMode.HTML)
                        await max_bot.session.close()
                    except Exception as e:
                        logging.exception(f'\n\n{e}')
            except Exception as e:
                logging.exception(f'\n\n{e}')
        else:
            await callback.answer(
                text=txt.request_was_handle_another_manager(),
                show_alert=True
            )
    finally:
        await callback.message.delete()
