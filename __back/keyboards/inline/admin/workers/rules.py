from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def back_to_about_worker() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Назад", callback_data=f'BackToAboutMe'
            )]
        ]
    )
