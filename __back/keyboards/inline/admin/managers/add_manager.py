from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

import database as db


def managers_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить менеджера", callback_data='AddManager')],
            [InlineKeyboardButton(text="📋 Список менеджеров", callback_data='AllManagers')]
        ]
    )


def managers_back():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data='ManagersMenu')]
        ]
    )


async def managers_list():
    keyboard = InlineKeyboardBuilder()
    all_managers = await db.get_managers()

    for manager in all_managers:
        keyboard.add(InlineKeyboardButton(text=f'👤 {manager.manager_full_name}',
                                          callback_data=f"Manager:{manager.manager_id}"))

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data='ManagersMenu'))

    return keyboard.adjust(1).as_markup()


def delete_manager(manager_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить Менеджера", callback_data=f'DeleteManager:{manager_id}')],
            [InlineKeyboardButton(text="Назад", callback_data='AllManagers')]
        ]
    )


def save_manager():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveManager')],
            [InlineKeyboardButton(text="❌ Отменить добавление", callback_data='ManagerAddCancel')]
        ]
    )
