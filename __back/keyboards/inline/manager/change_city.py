from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


class UpdateCityManager(
    CallbackData, prefix='UpdateCity'
):
    request_id: int
    new_city: int
    worker_id: int
    action: str


def confirmation_update_city_manager(
        new_city_id: int,
        worker_id: int,
        request_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Да', callback_data=UpdateCityManager(
                    request_id=request_id,
                    new_city=new_city_id,
                    worker_id=worker_id,
                    action='ConfirmUpdCity'
                ).pack()
             ),
             InlineKeyboardButton(
                    text='Нет', callback_data=UpdateCityManager(
                        request_id=request_id,
                        new_city=new_city_id,
                        worker_id=worker_id,
                        action='CancelUpdCity'
                    ).pack()
             )]
        ]
    )
