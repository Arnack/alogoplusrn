import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import keyboards.inline as ikb
from filters import Director
import database as db
import texts as txt
from config_reader import config


router = Router()


@router.message(Director(), F.text == '📣 Уведомления')
@router.message(Director(), F.text == '✍️ Уведомление')
async def newsletter(
        message: Message
):
    await message.answer(
        text=txt.accept_newsletter(),
        reply_markup=ikb.accept_newsletter()
    )


@router.callback_query(Director(), F.data == 'Newsletter')
async def newsletter_cancel(
        callback: CallbackQuery
):
    await callback.message.edit_text(
        text=txt.newsletter_city(),
        reply_markup=await ikb.cities_for_newsletter()
    )


@router.callback_query(Director(), F.data.startswith('NewsletterCity:'))
async def newsletter_city(
        callback: CallbackQuery,
        state: FSMContext
):
    city = callback.data.split(':')[1]

    await callback.message.edit_text(
        text=txt.newsletter_text(
            city=city
        )
    )
    await state.update_data(newsletter_city=city)
    await state.set_state("NewsletterMessage")


@router.message(Director(), StateFilter("NewsletterMessage"))
async def newsletter_message(
        message: Message,
        state: FSMContext
):
    data = await state.get_data()
    await state.clear()

    await message.answer(text=txt.newsletter_started())

    text_content = (message.text or message.caption or '').strip()

    # Создаём Max бота для отправки в Max
    max_bot = None
    if config.max_bot_token:
        try:
            from maxapi import Bot as MaxBot
            max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
        except Exception:
            pass

    workers = await db.get_users_by_city(city=data['newsletter_city'])
    for worker in workers:
        # Отправка в Telegram
        if worker.tg_id and worker.tg_id != 0:
            try:
                await message.send_copy(chat_id=worker.tg_id)
            except Exception:
                pass

        if text_content:
            try:
                await db.add_web_panel_notification(worker_id=worker.id, body=text_content)
            except Exception:
                logging.exception('web_panel_notification save')

        # Отправка в Max
        if max_bot and worker.max_id and worker.max_id > 1:
            try:
                await max_bot.send_message(
                    user_id=worker.max_id,
                    text=message.text or message.caption or ''
                )
            except Exception as e:
                logging.warning(f'Max newsletter error for user {worker.max_id}: {e}')

    if max_bot:
        await max_bot.close_session()

    await message.answer(text=txt.newsletter_finished())


@router.callback_query(Director(), F.data == 'NewsletterCancel')
async def newsletter_cancel(
        callback: CallbackQuery
):
    await callback.message.delete()
