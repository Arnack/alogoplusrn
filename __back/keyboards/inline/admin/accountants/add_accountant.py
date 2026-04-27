from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import database as db


def accountants_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кассира", callback_data='AddAccountant')],
            [InlineKeyboardButton(text="📋 Список кассиров", callback_data='AllAccountants')]
        ]
    )


def accountants_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data='AccountantsMenu')]
        ]
    )


def accountants_list(
        accountants: list
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for accountant in accountants:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👤 {accountant.full_name}',
                callback_data=f"Accountant:{accountant.id}"
            )
        )

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data='AccountantsMenu'
        )
    )

    return keyboard.adjust(1).as_markup()


def delete_accountant(
        accountant_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить Кассира", callback_data=f'DeleteAccountant:{accountant_id}')],
            [InlineKeyboardButton(text="Назад", callback_data='AllAccountants')]
        ]
    )


def confirmation_add_new_accountant():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveAccountant')],
            [InlineKeyboardButton(text="❌ Отменить добавление", callback_data='AccountantAddCancel')]
        ]
    )


def confirmation_delete_accountant(
        accountant_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'ConfirmDeleteAccountant:{accountant_id}'),
             InlineKeyboardButton(text="Нет", callback_data=f'Accountant:{accountant_id}')]
        ]
    )
