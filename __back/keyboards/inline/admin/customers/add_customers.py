from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton

import database as db


def customers_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить получателя услуг", callback_data='AddCustomer')],
            [InlineKeyboardButton(text="📋 Список получателей услуг", callback_data='AllCustomers')]
        ]
    )


async def customers_list():
    keyboard = InlineKeyboardBuilder()
    all_customers = await db.get_customers()

    for customer in all_customers:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👤 {customer.organization}',
                callback_data=f"Customer:{customer.id}"
            )
        )

    keyboard.add(InlineKeyboardButton(text="Назад", callback_data='CustomersMenu'))

    return keyboard.adjust(1).as_markup()


def customers_back():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data='CustomersMenu')]
        ]
    )


def customer_edit_menu(
        customer_id: int,
        auto_order_builder: bool,
        email_sending_enabled: bool = False,
        travel_compensation: int = None
) -> InlineKeyboardMarkup:
    keyboard = [
            [InlineKeyboardButton(text="🔄 Изменить период оказания услуг", callback_data=f'UpdateCustomerShift:{customer_id}')],
            [InlineKeyboardButton(
                text="👥 Представители получателя услуг",
                callback_data=f'CustomerAdminsMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text="👥 Корпоративные чаты",
                callback_data=f'CustomerGroupsMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text="👥 Представители исполнителя",
                callback_data=f'CustomerForemenMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text="🎁 Бонусные исполнители",
                callback_data=f'PremiumWorkersMenu:{customer_id}'
            )],
            [InlineKeyboardButton(text='🌆 Города', callback_data=f'UpdateCitiesCustomerMenu:{customer_id}')],
            [InlineKeyboardButton(text="🛂 Услуги", callback_data=f'OpenJobsMenu:{customer_id}')],
            [InlineKeyboardButton(text="📪 Почта", callback_data=f'CustomerEmailManagement:{customer_id}')],
            [InlineKeyboardButton(
                text=f"🚌 Компенсация{f' [{travel_compensation} ₽]' if travel_compensation else ''}",
                callback_data=f'SetTravelCompensation:{customer_id}'
            )],
            [InlineKeyboardButton(text="🎁 Акции", callback_data=f'CustomerPromotions:{customer_id}')],
            [InlineKeyboardButton(text="❗Удалить получателя услуг", callback_data=f'DeleteCustomer:{customer_id}')],
        ]

    if auto_order_builder:
        keyboard.append(
            [InlineKeyboardButton(text='Автозаявка ✅', callback_data=f'DisableAutoOrderBuilder:{customer_id}')]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton(text='Автозаявка ❌', callback_data=f'EnableAutoOrderBuilder:{customer_id}')]
        )

    # Добавляем чекбокс отправки на почту
    if email_sending_enabled:
        keyboard.append(
            [InlineKeyboardButton(text='✅ Отправка списка на почту', callback_data=f'DisableEmailSending:{customer_id}')]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton(text='❌ Отправка списка на почту', callback_data=f'EnableEmailSending:{customer_id}')]
        )

    keyboard.append(
        [InlineKeyboardButton(text="Назад", callback_data='AllCustomers')]
    )
    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def confirmation_delete_customer(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f'ConfirmDeleteCustomer:{customer_id}'),
             InlineKeyboardButton(text="Нет", callback_data=f'Customer:{customer_id}')]
        ]
    )


def save_costumer():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveCustomer')],
            [InlineKeyboardButton(text="🔄 Ввести другие данные", callback_data='AddCustomer')],
            [InlineKeyboardButton(text="❌ Отменить добавление", callback_data='CustomerAddCancel')]
        ]
    )
