from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def choose_rules_for() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Исполнители', callback_data=f'RulesFor:workers')],
            [InlineKeyboardButton(text='Представители исполнителя', callback_data=f'RulesFor:foremen')],
            [InlineKeyboardButton(text='Назад', callback_data=f'WorkerAccount')],
        ]
    )


def admin_rules_actions(
        rules_for: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Показать правила', callback_data=f'ShowRules:{rules_for}')],
            [InlineKeyboardButton(text='Изменить правила', callback_data=f'UpdateRules:{rules_for}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'BotRules')],
        ]
    )


def confirmation_update_rules(
        rules_for: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'ConfirmUpdateRules:{rules_for}'),
             InlineKeyboardButton(text="Нет", callback_data=f'WorkerAccount')]
        ]
    )


def notification_for_update_rules(
        notification_for: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Уведомить пользователей",
                callback_data=f'RulesSendNotification:{notification_for}'
            )]
        ]
    )


def back_to_rules_menu(
        rules_for: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Назад", callback_data=f'RulesFor:{rules_for}'
            )]
        ]
    )
