from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton


def update_worker_info(
        api_worker_id: int,
        in_rr: bool = True,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text='💰 Получить вознаграждение', callback_data='CreateWorkerPayment'))
    keyboard.row(InlineKeyboardButton(text='📁 Подписанные договоры', callback_data=f'GetWorkerContracts:{api_worker_id}'))
    keyboard.row(InlineKeyboardButton(text='🎁 Акции', callback_data='OpenPromotions'))
    keyboard.row(InlineKeyboardButton(text='💵 Получить бонус', callback_data='GetBonus'))
    keyboard.row(InlineKeyboardButton(text='📄 Правила', callback_data='BotRules'))
    keyboard.row(InlineKeyboardButton(text='🔄 Обновить данные', callback_data='UpdateWorkerInfo'))
    keyboard.row(InlineKeyboardButton(text='❌ Удалить данные', callback_data='EraseWorkerInfo'))
    return keyboard.as_markup()


def choose_update() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💳 Банковская карта', callback_data='UpdateWorkerBankCard')],
            [InlineKeyboardButton(text='👤 Данные для охраны', callback_data='UpdateDataForSecurity')],
            [InlineKeyboardButton(text='🌆 Город', callback_data='UpdateWorkerCity')],
            [InlineKeyboardButton(text='Назад', callback_data='BackToAboutMe')]
        ]
    )


def confirmation_erase_worker_data() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Да', callback_data='ConfirmEraseWorkerData'
            ),
             InlineKeyboardButton(
                text='Нет', callback_data='BackToAboutMe'
            )]
        ]
    )
