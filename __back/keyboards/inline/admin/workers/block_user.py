from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirmation_block_worker(worker_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'BlockWorker:{worker_id}'),
             InlineKeyboardButton(text="Нет", callback_data=f'BlockCancel')]
        ]
    )
