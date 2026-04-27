from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

from utils import get_rating
import database as db


async def foreman_applications_menu(
        applications
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for application in applications:
        user = await db.get_user_real_data_by_id(user_id=application.worker_id)
        rating = await get_rating(user_id=application.worker_id)

        keyboard.row(
            InlineKeyboardButton(
                text=f'{user.last_name} {user.first_name} {user.middle_name} | {rating}',
                callback_data=f'None'
            )
        )

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'Reject'))

    return keyboard.as_markup()
