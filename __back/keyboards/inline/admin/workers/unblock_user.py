from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List

import database as db


def back_to_adm_workers_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Назад',
                callback_data='BackToAdmWorkersMenu'
            )]
        ]
    )


async def blocked_workers_info(
        items: int,
        page: int,
        blocked_workers: List[int]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for i in range(items - 5, len(blocked_workers)):
        if i >= items or i > len(blocked_workers):
            break
        else:
            worker_real_data = await db.get_user_real_data_by_id(
                user_id=blocked_workers[i]
            )
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{worker_real_data.last_name} {worker_real_data.first_name} {worker_real_data.middle_name}",
                    callback_data=f"ConfirmationUnblockWorker:{blocked_workers[i]}"
                )
            )

    pages = len(blocked_workers) // 5 if len(blocked_workers) % 5 == 0 else (len(blocked_workers)//5) + 1
    if 5 >= items >= len(blocked_workers):
        pass
    elif items == 5:
        keyboard.row(
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
            InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardBlockedWorkers")
        )
    elif items >= len(blocked_workers):
        keyboard.row(
            InlineKeyboardButton(text="Назад ◀️", callback_data="BackBlockedWorkers"),
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None")
        )
    else:
        keyboard.row(
            InlineKeyboardButton(text="Назад ◀️", callback_data="BackBlockedWorkers"),
            InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
            InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardBlockedWorkers")
        )

    keyboard.row(InlineKeyboardButton(text=f"Назад", callback_data='BackToAdmWorkersMenu'))

    return keyboard.as_markup()


def confirmation_unblock_worker(worker_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'UnblockWorker:{worker_id}'),
             InlineKeyboardButton(text="Нет", callback_data=f'UnblockUser')]
        ]
    )
