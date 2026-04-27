from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import database as db


def premium_workers_menu(customer_id: int) -> InlineKeyboardMarkup:
    """Главное меню управления исполнителями с дополнительным вознаграждением"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Закрепить исполнителя',
                callback_data=f'AddPremiumWorker:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='📋 Список закреплённых',
                callback_data=f'ShowPremiumWorkersList:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='❌ Открепить исполнителя',
                callback_data=f'DeletePremiumWorkersMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=f'Customer:{customer_id}'
            )]
        ]
    )


def premium_workers_back(customer_id: int) -> InlineKeyboardMarkup:
    """Кнопка 'Назад' в меню премиальных исполнителей"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Назад',
                callback_data=f'PremiumWorkersMenu:{customer_id}'
            )]
        ]
    )


async def select_worker_from_list(workers: List[db.User]) -> InlineKeyboardMarkup:
    """Список найденных исполнителей для выбора"""
    keyboard = InlineKeyboardBuilder()

    for worker in workers:
        real_data = await db.get_user_real_data_by_id(worker.id)
        keyboard.add(
            InlineKeyboardButton(
                text=f'{real_data.last_name} {real_data.first_name} {real_data.middle_name}',
                callback_data=f'SelectWorker:{worker.id}'
            )
        )

    keyboard.adjust(1)
    return keyboard.as_markup()


def select_bonus_type() -> InlineKeyboardMarkup:
    """Выбор типа дополнительного вознаграждения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='💰 Безусловное вознаграждение',
                callback_data='BonusTypeUnconditional'
            )],
            [InlineKeyboardButton(
                text='📊 Условное вознаграждение',
                callback_data='BonusTypeConditional'
            )]
        ]
    )


def add_more_conditions_or_finish(customer_id: int) -> InlineKeyboardMarkup:
    """Выбор: добавить ещё условие или завершить"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Добавить ещё условие',
                callback_data='AddMoreConditions'
            )],
            [InlineKeyboardButton(
                text='✅ Завершить',
                callback_data='FinishConditions'
            )]
        ]
    )


def confirm_save_premium_worker(customer_id: int) -> InlineKeyboardMarkup:
    """Подтверждение сохранения премиального исполнителя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='✅ Сохранить',
                callback_data='SavePremiumWorker'
            ),
            InlineKeyboardButton(
                text='❌ Отменить',
                callback_data=f'PremiumWorkersMenu:{customer_id}'
            )]
        ]
    )


async def premium_workers_list(
    customer_id: int,
    premium_workers: List[db.PremiumWorker]
) -> InlineKeyboardMarkup:
    """Список всех закреплённых исполнителей"""
    keyboard = InlineKeyboardBuilder()

    for pw in premium_workers:
        worker = pw.worker
        real_data = await db.get_user_real_data_by_id(worker.id)
        bonus_type_emoji = '💰' if pw.bonus_type == 'unconditional' else '📊'

        keyboard.add(
            InlineKeyboardButton(
                text=f'{bonus_type_emoji} {real_data.last_name} {real_data.first_name}',
                callback_data=f'ViewPremiumWorker:{pw.id}'
            )
        )

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(
            text='Назад',
            callback_data=f'PremiumWorkersMenu:{customer_id}'
        )
    )

    return keyboard.as_markup()


async def delete_premium_workers_list(
    customer_id: int,
    premium_workers: List[db.PremiumWorker]
) -> InlineKeyboardMarkup:
    """Список исполнителей для открепления"""
    keyboard = InlineKeyboardBuilder()

    for pw in premium_workers:
        worker = pw.worker
        real_data = await db.get_user_real_data_by_id(worker.id)

        keyboard.add(
            InlineKeyboardButton(
                text=f'❌ {real_data.last_name} {real_data.first_name}',
                callback_data=f'DeletePremiumWorker:{pw.id}'
            )
        )

    keyboard.adjust(1)
    keyboard.row(
        InlineKeyboardButton(
            text='Назад',
            callback_data=f'PremiumWorkersMenu:{customer_id}'
        )
    )

    return keyboard.as_markup()


def confirm_delete_premium_worker(
    premium_worker_id: int,
    customer_id: int
) -> InlineKeyboardMarkup:
    """Подтверждение открепления исполнителя"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Да',
                callback_data=f'ConfirmDeletePremiumWorker:{premium_worker_id}:{customer_id}'
            ),
            InlineKeyboardButton(
                text='Нет',
                callback_data=f'DeletePremiumWorkersMenu:{customer_id}'
            )]
        ]
    )
