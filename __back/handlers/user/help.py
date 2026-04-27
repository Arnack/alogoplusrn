from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaDocument
import logging

from utils import get_rating, help_logger
import keyboards.inline as ikb
import keyboards.reply as kb
from filters import Worker
import database as db
import texts as txt


router = Router()
router.message.filter(Worker())
router.callback_query.filter(Worker())


async def confirmation_send_help_message(
        message: Message,
        state: FSMContext,
) -> None:
    await state.set_state(None)
    data = await state.get_data()

    await message.answer(
        text=f"<b>💬 Обращение:</b>\n<blockquote>{data['HelpText']}</blockquote>",
    )

    if len(data['HelpPhotos']) > 1:
        await message.answer_media_group(
            media=[
                InputMediaPhoto(
                    media=file_id
                ) for file_id in data['HelpPhotos']
            ]
        )
    elif len(data['HelpPhotos']) == 1:
        await message.answer_photo(
            photo=data['HelpPhotos'][0],
        )

    if len(data['HelpFiles']) > 1:
        await message.answer_media_group(
            media=[
                InputMediaDocument(
                    media=file_id
                ) for file_id in data['HelpFiles']
            ]
        )
    elif len(data['HelpFiles']) == 1:
        await message.answer_document(
            document=data['HelpFiles'][0],
        )

    await message.answer(
        text=txt.confirmation_send_help_message(),
        reply_markup=ikb.confirmation_send_help_message(),
    )


async def send_help_message_to_group(
        message: Message,
        state: FSMContext,
        worker_tg_id: int,
) -> None:
    try:
        settings = await db.get_settings()
        data = await state.get_data()
        worker = await db.get_user_with_data_for_security(
            tg_id=worker_tg_id,
        )

        user_rating = await db.get_user_rating(
            user_id=worker.id
        )
        if not user_rating:
            await db.set_rating(
                user_id=worker.id
            )
            user_rating = await db.get_user_rating(
                user_id=worker.id
            )
        rating = await get_rating(
            user_id=worker.id
        )

        await message.bot.send_message(
            chat_id=settings.help_group_chat_id,
            text=txt.help_message_to_group(
                real_full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                real_phone_number=worker.security.phone_number,
                tg_id=message.from_user.id,
                max_id=worker.max_id,
                city=worker.city,
                total_orders=user_rating.total_orders,
                successful_orders=user_rating.successful_orders,
                rating=rating,
                help_text=data['HelpText'],
            ),
        )

        if len(data['HelpPhotos']) > 1:
            media = [InputMediaPhoto(
                media=data['HelpPhotos'][0],
                caption=txt.help_message_caption(
                    full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                ),
            )]
            for file_id in data['HelpPhotos'][1:]:
                media.append(InputMediaPhoto(media=file_id))

            await message.bot.send_media_group(
                chat_id=settings.help_group_chat_id,
                media=media,
            )
        elif len(data['HelpPhotos']) == 1:
            await message.bot.send_photo(
                chat_id=settings.help_group_chat_id,
                photo=data['HelpPhotos'][0],
                caption=txt.help_message_caption(
                    full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                )
            )

        if len(data['HelpFiles']) > 1:
            media = [InputMediaDocument(
                media=data['HelpFiles'][0],
                caption=txt.help_message_caption(
                    full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                ),
            )]
            for file_id in data['HelpFiles'][1:]:
                media.append(InputMediaDocument(media=file_id))

            await message.bot.send_media_group(
                chat_id=settings.help_group_chat_id,
                media=media,
            )
        elif len(data['HelpFiles']) == 1:
            await message.bot.send_document(
                chat_id=settings.help_group_chat_id,
                document=data['HelpFiles'][0],
                caption=txt.help_message_caption(
                    full_name=f'{worker.security.last_name} {worker.security.first_name} {worker.security.middle_name}',
                )
            )

        await message.edit_text(
            text=txt.help_message_sent(),
        )
        help_logger.info(
            f'{worker_tg_id} - обращение успешно отправлено в группу helpmealgoritm'
        )
        await db.update_help_last_use(
            worker_id=worker.id,
        )
    except Exception as e:
        logging.exception(e)
        help_logger.error(
            f'{worker_tg_id} - не удалось отправить обращение в группу helpmealgoritm',
        )
        await message.edit_text(
            text=txt.send_help_message_error(),
        )


@router.message(F.text == '🆘 СВЯЗЬ С РУКОВОДСТВОМ')
async def request_help_text(
        message: Message,
        state: FSMContext,
):
    worker = await db.get_user(
        tg_id=message.from_user.id,
    )
    can_use = await db.can_use_help(
        worker_id=worker.id,
    )

    if can_use:
        await message.answer(
            text=txt.request_help_text(),
        )
        await state.set_state('GetHelpText')
    else:
        await message.answer(
            text=txt.help_request_limit_reached(),
        )


@router.message(F.text, StateFilter('GetHelpText'))
async def get_help_text(
        message: Message,
        state: FSMContext,
):
    await message.answer(
        text=txt.request_help_files_or_photos(),
        reply_markup=kb.help_skip(),
    )
    await state.set_state('GetHelpFiles')
    await state.update_data(
        HelpText=message.text,
        HelpPhotos=[],
        HelpFiles=[],
    )


@router.message(F.photo, StateFilter('GetHelpFiles'))
@router.message(F.document, StateFilter('GetHelpFiles'))
async def get_help_files(
        message: Message,
        state: FSMContext,
):
    data = await state.get_data()
    help_photos = data['HelpPhotos']
    help_files = data['HelpFiles']

    total_files = len(help_files) + len(help_photos)

    if total_files == 2:
        if message.photo:
            await message.reply(
                text=txt.help_photo_saved(
                    request_more=False,
                ),
                 reply_markup=kb.user_menu(),
            )

            help_photos.append(message.photo[-1].file_id)
            await state.update_data(
                HelpPhotos=help_photos,
            )
        else:
            await message.reply(
                text=txt.help_file_saved(
                    request_more=False,
                ),
                reply_markup=kb.user_menu(),
            )
            help_files.append(message.document.file_id)
            await state.update_data(
                HelpFiles=help_files,
            )

        await confirmation_send_help_message(
            message=message,
            state=state,
        )
    else:
        if message.photo:
            await message.reply(
                text=txt.help_photo_saved(),
            )
            help_photos.append(message.photo[-1].file_id)
            await state.update_data(
                HelpPhotos=help_photos,
            )
        else:
            await message.reply(
                text=txt.help_file_saved(),
            )
            help_files.append(message.document.file_id)
            await state.update_data(
                HelpFiles=help_files,
            )


@router.message(F.text == 'Пропустить', StateFilter('GetHelpFiles'))
async def get_help_files_skip(
        message: Message,
        state: FSMContext,
):
    await message.answer(
        text='.',
        reply_markup=kb.user_menu(),
    )

    await confirmation_send_help_message(
        message=message,
        state=state,
    )


@router.callback_query(F.data == 'SendHelpMessage')
async def send_help_message(
        callback: CallbackQuery,
        state: FSMContext,
):
    msg = await callback.message.edit_text(
        text=txt.sending_help_message(),
    )

    await send_help_message_to_group(
        message=msg,
        state=state,
        worker_tg_id=callback.from_user.id,
    )


@router.callback_query(F.data == 'CancelSendHelpMessage')
async def cancel_send_help_message(
        callback: CallbackQuery,
):
    await callback.message.edit_text(
        text=txt.cancel_send_help_message(),
    )
