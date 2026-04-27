from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def confirmation_payment_notification(
        order_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'WorkConfirmPayment:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'WorkCancelPayment:{order_id}'),],
        ]
    )


def act_sign_keyboard(act_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подписать', callback_data=f'SignAct:{act_id}'),
                InlineKeyboardButton(text='❌ Отказаться', callback_data=f'RefuseAct:{act_id}'),
            ]
        ]
    )
