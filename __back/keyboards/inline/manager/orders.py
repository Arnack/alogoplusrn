from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

import database as db


async def orders_menu():
    moderation_count = await db.get_orders_count_for_moderation()
    search_workers_count = await db.get_orders_count_for_applications_moderation()
    in_progress_count = await db.get_orders_count_in_progress()

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🔴 На модерации ({moderation_count})",
                callback_data='ModerationOrders'
            )],
            [InlineKeyboardButton(
                text=f"🟢 Подбор исполнителей ({search_workers_count})",
                callback_data='ModerationApplications'
            )],
            [InlineKeyboardButton(
                text=f"🟡 Оказание услуг ({in_progress_count})",
                callback_data='ShowOrdersInProgress'
            )]
        ]
    )


def amount_for_order_in_button(
        amount: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'{amount}₽', callback_data=f'SetOrderAmount:{amount}')],
            [InlineKeyboardButton(text='Ввести другую', callback_data='SetOtherAmount')]
        ]
    )


def back_to_moderation_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Назад", callback_data='BackToModerationMenu')]
        ]
    )


async def order_moder(page, order_id):
    count = await db.get_orders_count_for_moderation()
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='💵 Установить вознаграждение', callback_data=f'Amount:{order_id}'))
    keyboard.row(InlineKeyboardButton(text='👥 Изменить кол-во исполнителей', callback_data=f'ChangeWorkersCount:{order_id}'))
    keyboard.row(InlineKeyboardButton(text='❌ Удалить заявку', callback_data=f'DeleteOrder:{order_id}'))

    if count == 1:
        pass
    elif page == 1:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='ModerationOrderForward'))
    elif page == count:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='ModerationOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'))
    else:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='ModerationOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='ModerationOrderForward'))
    return keyboard.as_markup()


def accept_order_moder():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Сохранить', callback_data='SaveAmount')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='ModerationOrders')]
        ]
    )


async def orders_info(index, page):
    keyboard = InlineKeyboardBuilder()

    orders = await db.get_orders_for_info()

    pre_sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    sorted_orders = sorted(
        pre_sorted_orders,
        key=lambda order: order.customer_id
    )

    for i in range(index - 5, len(sorted_orders)):
        if i >= index or i > len(sorted_orders):
            break
        else:
            workers_count = await db.get_order_workers_count_by_order_id(order_id=sorted_orders[i].id)
            applications_count = await db.get_applications_count_by_order_id(order_id=sorted_orders[i].id)

            organization = await db.get_customer_organization(customer_id=sorted_orders[i].customer_id)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{organization} | "
                         f"{sorted_orders[i].date[:5:]} {'Д' if sorted_orders[i].day_shift else 'Н'} | "
                         f"{workers_count} из {sorted_orders[i].workers} | "
                         f"{applications_count}",
                    callback_data=f"ManagerModerationOrder:{sorted_orders[i].id}"
                )
            )

    pages = len(sorted_orders) // 5 if len(sorted_orders) % 5 == 0 else (len(sorted_orders)//5) + 1
    if 5 >= index >= len(sorted_orders):
        pass
    elif index == 5:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardModerationOrder"))
    elif index >= len(sorted_orders):
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="BackModerationOrder"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"))
    else:
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="BackModerationOrder"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardModerationOrder"))

    keyboard.row(InlineKeyboardButton(text=f"Назад", callback_data='BackToModerationMenu'))

    return keyboard.as_markup()


def moder_order_info(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='👥 Изменить кол-во исполнителей', callback_data=f'ChangeWorkersCount:{order_id}')],
            [InlineKeyboardButton(text='Предпросмотр PDF', callback_data=f'PreviewPdf:{order_id}')],
            [InlineKeyboardButton(text='Завершить регистрацию', callback_data=f'CompleteRegistration:{order_id}')],
            [InlineKeyboardButton(text='❌ Удалить заявку', callback_data=f'DeleteOrder:{order_id}')],
            [InlineKeyboardButton(text='Отклики', callback_data=f'ApplicationsByOrder:{order_id}'),
             InlineKeyboardButton(text='Исполнители', callback_data=f'OrderWorkers:{order_id}')],
            [InlineKeyboardButton(text='Назад', callback_data='BackToModerationApplications')]
        ]
    )


def order_in_progress_info(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Изменить лимит откликов по заявке',
                callback_data=f'CustomerUpdateWorkers:{order_id}'
            )],
            [InlineKeyboardButton(
                text='Просмотр PDF',
                callback_data=f'CustomerGetPdf:{order_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data='BackToOrdersInProgress'
            )]
        ]
    )


def accept_complete_registration(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmCompleteRegistration:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'ManagerModerationOrder:{order_id}')]
        ]
    )


async def orders_in_progress_info(index, page):
    keyboard = InlineKeyboardBuilder()

    orders = await db.get_orders_in_progress()

    pre_sorted_orders = sorted(
        orders,
        key=lambda order: datetime.strptime(
            f'{order.date} {order.day_shift[:5:] if order.day_shift else order.night_shift[:5:]}',
            '%d.%m.%Y %H:%M'
        )
    )

    sorted_orders = sorted(
        pre_sorted_orders,
        key=lambda order: order.customer_id
    )

    for i in range(index - 5, len(sorted_orders)):
        if i >= index or i > len(sorted_orders):
            break
        else:
            workers_count = await db.get_order_workers_count_by_order_id(order_id=sorted_orders[i].id)
            organization = await db.get_customer_organization(customer_id=sorted_orders[i].customer_id)
            keyboard.row(
                InlineKeyboardButton(
                    text=f"{organization} | "
                         f"{sorted_orders[i].date[:5:]} {'Д' if sorted_orders[i].day_shift else 'Н'} | "
                         f"{workers_count} из {sorted_orders[i].workers}",
                    callback_data=f"OrderInProgress:{sorted_orders[i].id}"
                )
            )

    pages = len(sorted_orders) // 5 if len(sorted_orders) % 5 == 0 else (len(sorted_orders)//5) + 1
    if 5 >= index >= len(sorted_orders):
        pass
    elif index == 5:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardOrdersInProgress"))
    elif index >= len(sorted_orders):
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="BackOrdersInProgress"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"))
    else:
        keyboard.row(InlineKeyboardButton(text="Назад ◀️", callback_data="BackOrdersInProgress"),
                     InlineKeyboardButton(text=f'{page}/{pages}', callback_data="None"),
                     InlineKeyboardButton(text="▶️ Вперед", callback_data="ForwardOrdersInProgress"))

    keyboard.row(InlineKeyboardButton(text=f"Назад", callback_data='BackToModerationMenu'))

    return keyboard.as_markup()
