import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

import keyboards.inline as ikb
from filters import Customer, Admin
from aiogram.filters import or_f
import database as db
import texts as txt
from config_reader import config


router = Router()


@router.callback_query(or_f(Customer(), Admin()), F.data.startswith('ShoutSendMessage:'))
async def shout_menu(
        callback: CallbackQuery,
        state: FSMContext
):
    order_id = int(callback.data.split(':')[1])
    workers = await db.get_workers_from_order_workers(order_id=order_id)
    if workers:
        # Check if admin is working as customer
        data = await state.get_data()
        admin_as_customer_id = data.get('admin_as_customer_id')

        if admin_as_customer_id:
            # Admin working as customer - get first admin of the customer
            order = await db.get_order(order_id=order_id)
            customer_admins = await db.get_customer_admins(customer_id=order.customer_id)
            sender_full_name = customer_admins[0].admin_full_name if customer_admins else "Admin"
        else:
            # Regular customer admin
            customer_admin = await db.get_customer_admin(
                admin_tg_id=callback.from_user.id
            )
            sender_full_name = customer_admin.admin_full_name

        await state.update_data(
            order_id=order_id,
            sender_full_name=sender_full_name
        )
        await callback.message.edit_text(
            text=txt.customer_request_shout_message()
        )
        await state.set_state('ShoutGetMessage')
    else:
        await callback.message.edit_text(
            text=txt.customer_shout_workers_count_error(),
            reply_markup=ikb.customer_back_to_shout_menu(
                order_id=order_id
            )
        )


@router.message(or_f(Customer(), Admin()), F.photo, StateFilter('ShoutGetMessage'))
@router.message(or_f(Customer(), Admin()), F.video, StateFilter('ShoutGetMessage'))
@router.message(or_f(Customer(), Admin()), F.document, StateFilter('ShoutGetMessage'))
@router.message(or_f(Customer(), Admin()), F.audio, StateFilter('ShoutGetMessage'))
@router.message(or_f(Customer(), Admin()), F.text, StateFilter('ShoutGetMessage'))
async def shout_send_message(
        message: Message,
        state: FSMContext
):
    try:
        data = await state.get_data()
        workers = await db.get_workers_for_shout(order_id=data['order_id'])
        shout_id = await db.set_shout_stat(
            sender_tg_id=message.from_user.id,
            order_id=data['order_id']
        )

        msg = await message.answer(
            text=txt.shout_start()
        )

        # Создаём Max бота для отправки в Max
        max_bot = None
        if config.max_bot_token:
            try:
                from maxapi import Bot as MaxBot
                max_bot = MaxBot(token=config.max_bot_token.get_secret_value())
            except Exception:
                pass

        count = 0
        shout_text = txt.customer_shout_text(
            sender_full_name=data['sender_full_name'],
            text=message.html_text
        )

        for worker in workers:
            sent = False

            # Отправка в Telegram (если есть tg_id)
            if worker.tg_id and worker.tg_id != 0:
                try:
                    if message.photo:
                        await message.bot.send_photo(
                            chat_id=worker.tg_id,
                            photo=message.photo[-1].file_id,
                            caption=shout_text[:1024],
                            reply_markup=ikb.shout_finish(shout_id=shout_id),
                            protect_content=True
                        )
                    elif message.video:
                        await message.bot.send_video(
                            chat_id=worker.tg_id,
                            video=message.video.file_id,
                            caption=shout_text[:1024],
                            reply_markup=ikb.shout_finish(shout_id=shout_id),
                            protect_content=True
                        )
                    elif message.document:
                        await message.bot.send_document(
                            chat_id=worker.tg_id,
                            document=message.document.file_id,
                            caption=shout_text[:1024],
                            reply_markup=ikb.shout_finish(shout_id=shout_id),
                            protect_content=True
                        )
                    elif message.audio:
                        await message.bot.send_audio(
                            chat_id=worker.tg_id,
                            audio=message.audio.file_id,
                            caption=shout_text[:1024],
                            reply_markup=ikb.shout_finish(shout_id=shout_id),
                            protect_content=True
                        )
                    else:
                        await message.bot.send_message(
                            chat_id=worker.tg_id,
                            text=shout_text,
                            reply_markup=ikb.shout_finish(shout_id=shout_id),
                            protect_content=True
                        )
                    sent = True
                except Exception:
                    pass

            # Отправка в Max (если есть max_id и бот создан)
            if max_bot and worker.max_id and worker.max_id > 1:
                try:
                    await max_bot.send_message(
                        user_id=worker.max_id,
                        text=shout_text
                    )
                    sent = True
                except Exception as e:
                    logging.warning(f'Max shout error for user {worker.max_id}: {e}')

            if sent:
                count += 1

        if max_bot:
            await max_bot.close_session()

        await db.update_shout_workers(
            shout_id=shout_id,
            workers_count=count
        )

        await message.bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=msg.message_id,
            text=txt.shout_finish(
                shout_id=shout_id,
                workers_count=count
            )
        )
    except Exception as e:
        logging.exception(f'\n\n{e}')
        await message.answer(
            text=txt.send_shout_error()
        )
    finally:
        await state.clear()
