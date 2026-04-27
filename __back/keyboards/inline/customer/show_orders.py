from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

import database as db


def back_to_customer_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='OrderCancel')]
        ]
    )


async def show_order(page, admin, order_id, workers_count):
    count = await db.get_orders_count_for_customer(admin=admin)
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='Изменить количество исполнителей',
                                      callback_data=f'CustomerUpdateWorkers:{order_id}'))

    if workers_count > 0:
        keyboard.row(InlineKeyboardButton(text='Сформировать PDF', callback_data=f'CustomerGetPdf:{order_id}'))

    check_time = await db.check_time(order_id=order_id)
    if check_time:
        keyboard.row(InlineKeyboardButton(text='Завершить оказание услуг', callback_data=f'CustomerOrderFinish:{order_id}'))

    keyboard.row(InlineKeyboardButton(text='📣 Оповещение на объекте', callback_data=f'OpenShoutMenu:{order_id}'))

    if count == 1:
        pass
    elif page == 1:
        keyboard.row(InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='CustomerOrderForward'))
    elif page == count:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='CustomerOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'))
    else:
        keyboard.row(InlineKeyboardButton(text='Назад ◀️', callback_data='CustomerOrderBack'),
                     InlineKeyboardButton(text=f'{page}/{count}', callback_data='None'),
                     InlineKeyboardButton(text='▶️ Вперед', callback_data='CustomerOrderForward'))
    return keyboard.as_markup()


def confirmation_order_finish(order_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmOrderFinish:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'AllCustomerOrders')]
        ]
    )


def confirmation_common_hours(
        order_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmCommonHours:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelCommonHours:{order_id}')]
        ]
    )


def confirmation_set_common_hours(
        order_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmSetCommonHours:{order_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'CancelCommonHours:{order_id}')]
        ]
    )


def confirmation_set_hours() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmSetHours'),
             InlineKeyboardButton(text='Нет', callback_data=f'AllCustomerOrders')]
        ]
    )


async def accept_update_workers_count(order_id, tg_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Да', callback_data=f'ApproveUpdateWorkersCount:{order_id}'))

    customers = await db.get_customers_for_filter()
    if tg_id in customers:
        keyboard.add(InlineKeyboardButton(text='Нет', callback_data=f'AllCustomerOrders'))
    else:
        keyboard.add(InlineKeyboardButton(text='Нет', callback_data=f'OrderInProgress:{order_id}'))

    return keyboard.as_markup()


async def accept_delete_order(order_id, tg_id):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='Да', callback_data=f'AcceptDeleteOrder:{order_id}'))

    customers = await db.get_customers_for_filter()
    if tg_id in customers:
        keyboard.add(InlineKeyboardButton(text='Нет', callback_data=f'AllCustomerOrders'))
    else:
        keyboard.add(InlineKeyboardButton(text='Нет', callback_data=f'back_to_moderation_menu'))

    return keyboard.as_markup()


def worker_status_selector(worker_id: str, order_id: int, current_status: str = None):
    """
    Клавиатура выбора статуса для исполнителя
    current_status может быть: None, 'NOT_OUT', 'EXTRA'
    """
    keyboard = InlineKeyboardBuilder()

    # Чекбоксы для статусов
    not_out_text = "🔴 Не вышел" if current_status != 'NOT_OUT' else "✅ Не вышел"
    extra_text = "🟡 Лишний" if current_status != 'EXTRA' else "✅ Лишний"

    keyboard.row(
        InlineKeyboardButton(
            text=not_out_text,
            callback_data=f'WorkerStatus:NOT_OUT:{worker_id}:{order_id}'
        ),
        InlineKeyboardButton(
            text=extra_text,
            callback_data=f'WorkerStatus:EXTRA:{worker_id}:{order_id}'
        )
    )

    # Кнопка "Назад" для возврата к началу
    keyboard.row(
        InlineKeyboardButton(
            text='🔙 К началу (Старт)',
            callback_data=f'CancelCommonHours:{order_id}'
        )
    )

    return keyboard.as_markup()
