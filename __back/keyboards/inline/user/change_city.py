from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

import database as db


class UpdateCityUser(
    CallbackData, prefix='UpdateCity'
):
    new_city_id: int
    worker_id: int
    action: str


def accept_change_city():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data='ChangeCity'),
             InlineKeyboardButton(text='Нет', callback_data='ChangeCityCancel')]
        ]
    )


async def cities_for_change():
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities()

    for city in cities:
        keyboard.add(
            InlineKeyboardButton(
                text=city.city_name,
                callback_data=f'ChangeCity:{city.id}'
            )
        )

    keyboard.adjust(2)
    keyboard.row(
        InlineKeyboardButton(
            text='Отмена',
            callback_data=f'UpdateWorkerInfo'
        )
    )

    return keyboard.as_markup()


def confirmation_update_city_worker(
        city_id: int,
        worker_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Да', callback_data=UpdateCityUser(
                    new_city_id=city_id,
                    worker_id=worker_id,
                    action='ConfirmUpdCity'
                ).pack()
            ),
             InlineKeyboardButton(
                 text='Нет', callback_data='BackToAboutMe'
             )]
        ]
    )
