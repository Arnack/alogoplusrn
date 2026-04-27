from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import database as db


def supervisors_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить координатора", callback_data='AddSupervisor')],
            [InlineKeyboardButton(text="📋 Список координаторов", callback_data='AllSupervisors')]
        ]
    )


def supervisors_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data='SupervisorsMenu')]
        ]
    )


def supervisors_list(
        supervisors: list
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for supervisor in supervisors:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👤 {supervisor.full_name}',
                callback_data=f"Supervisor:{supervisor.id}"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data='SupervisorsMenu'
        )
    )

    return keyboard.adjust(1).as_markup()


def delete_supervisor(
        supervisor_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить координатора", callback_data=f'DeleteSupervisor:{supervisor_id}')],
            [InlineKeyboardButton(text="Назад", callback_data='AllSupervisors')]
        ]
    )


def confirmation_add_new_supervisor():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveSupervisor')],
            [InlineKeyboardButton(text="❌ Отменить добавление", callback_data='SupervisorsMenu')]
        ]
    )


def confirmation_delete_supervisor(
        supervisor_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'ConfirmDeleteSupervisor:{supervisor_id}'),
             InlineKeyboardButton(text="Нет", callback_data=f'Supervisor:{supervisor_id}')]
        ]
    )
