from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup

from utils import get_rating
import database as db


async def applications_menu(order_id):
    keyboard = InlineKeyboardBuilder()
    applications = await db.get_applications_for_moderation(order_id=order_id)

    for application in applications:
        user = await db.get_user_real_data_by_id(user_id=application.worker_id)
        rating = await get_rating(user_id=application.worker_id)

        order_from_friend = '🔵 ' if application.order_from_friend else ''

        keyboard.row(
            InlineKeyboardButton(
                text=f'{order_from_friend}{user.last_name} {user.first_name} {user.middle_name} | {rating}',
                callback_data=f'Application:{application.id}'
            )
        )

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'ManagerModerationOrder:{order_id}'))

    return keyboard.as_markup()


def applications_none(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data=f'ManagerModerationOrder:{order_id}')]
        ]
    )


def application_moder(application_id, order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Одобрить', callback_data=f'ConfirmationApprove:{application_id}'),
             InlineKeyboardButton(text='Отклонить', callback_data=f'ConfirmationReject:{application_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'BackToApplications:{order_id}')]
        ]
    )


def approve_application(application_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ApproveApplication:{application_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'Application:{application_id}')]
        ]
    )


def reject_application(application_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'RejectApplication:{application_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'Application:{application_id}')]
        ]
    )
