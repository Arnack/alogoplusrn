from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton


def shout_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✉️ Отправить сообщение', callback_data='ShoutSendMessage')],
            [InlineKeyboardButton(text='📊 Статистика', callback_data='ShoutShowStat')]
        ]
    )


def customer_shout_menu(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✉️ Отправить сообщение', callback_data=f'ShoutSendMessage:{order_id}')],
            [InlineKeyboardButton(text='📊 Статистика', callback_data=f'ShoutShowStat:{order_id}')],
            [InlineKeyboardButton(text='Назад', callback_data='AllCustomerOrders')]
        ]
    )


def shout_finish(shout_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Ознакомился ✅', callback_data=f'ShoutFinish:{shout_id}')]
        ]
    )


async def shout_stat(foreman_shouts):
    keyboard = InlineKeyboardBuilder()

    for shout in foreman_shouts:
        keyboard.add(
            InlineKeyboardButton(
                text=f'{shout.id}',
                callback_data=f'ShowShoutStat:{shout.id}'
            )
        )

    keyboard.adjust(4)
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='OpenShoutMenu'))

    return keyboard.as_markup()


async def customer_shout_stat(customer_admin_shouts, order_id):
    keyboard = InlineKeyboardBuilder()

    for shout in customer_admin_shouts:
        keyboard.add(
            InlineKeyboardButton(
                text=f'{shout.id}',
                callback_data=f'ShowShoutStat:{shout.id}'
            )
        )

    keyboard.adjust(4)
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'OpenShoutMenu:{order_id}'))

    return keyboard.as_markup()


def back_to_shout_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='OpenShoutMenu')]
        ]
    )


def customer_back_to_shout_menu(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data=f'OpenShoutMenu:{order_id}')]
        ]
    )


def shout_stat_back():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='ShoutShowStat')]
        ]
    )


def customer_shout_stat_back(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data=f'ShoutShowStat:{order_id}')]
        ]
    )
