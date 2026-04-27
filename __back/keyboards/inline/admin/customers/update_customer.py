from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from typing import List, Optional
from math import ceil

import database as db


class DeleteJobFPCallbackData(
    CallbackData, prefix='DeleteJobFP'
):
    job_id: Optional[int] = None
    customer_id: int
    menu_page: int
    action: str


def update_customer_shift(customer_id, day_shift, night_shift):
    day = day_shift if day_shift else 'нет'
    night = night_shift if night_shift else 'нет'
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'День [{day}]', callback_data=f'UpdateDayShift:{customer_id}'),
             InlineKeyboardButton(text=f'Ночь [{night}]', callback_data=f'UpdateNightShift:{customer_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')]
        ]
    )


def update_customer_city(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'✏️ Редактировать город', callback_data=f'UpdateCustomerCities:{customer_id}')],
            [InlineKeyboardButton(text=f'➕ Добавить город', callback_data=f'AddCustomerCity:{customer_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')]
        ]
    )


def customer_admins_menu(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Добавить представителя',
                callback_data=f'NewCustomerAdmin:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='❌ Удалить представителя',
                callback_data=f'DeleteCustomerAdminsMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=f'Customer:{customer_id}'
            )]
        ]
    )


def customer_groups_menu(
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Добавить чат',
                callback_data=f'NewCustomerGroup:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='❌ Удалить чат',
                callback_data=f'DeleteCustomerGroupsMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=f'Customer:{customer_id}'
            )]
        ]
    )


def customer_foremen_menu(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='➕ Добавить представителя',
                callback_data=f'NewCustomerForeman:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='❌ Удалить представителя',
                callback_data=f'DeleteCustomerForemenMenu:{customer_id}'
            )],
            [InlineKeyboardButton(
                text='Назад',
                callback_data=f'Customer:{customer_id}'
            )]
        ]
    )


async def customer_cities(customer_id):
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_customer_cities(customer_id=customer_id)

    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city.city, callback_data=f'UpdateCustomerCity:{city.id}'))

    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'UpdateCitiesCustomerMenu:{customer_id}'))

    return keyboard.as_markup()


def choose_customer_city_update(
        city_id: int,
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📍 Способ добраться', callback_data=f'UpdateCustomerCityWay:{city_id}')],
            [InlineKeyboardButton(text='🌆 Название', callback_data=f'UpdateCustomerCityName:{city_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'UpdateCustomerCities:{customer_id}')]
        ]
    )


def add_city_way(
        city_id: int
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Добавить', callback_data=f'AddCityWay:{city_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'UpdateCustomerCity:{city_id}')]
        ]
    )


def confirmation_update_city_way(
        city_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmUpdateCityWay:{city_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'UpdateCustomerCity:{city_id}')]
        ]
    )


def update_city_way(
        city_id: int
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📍 Посмотреть', callback_data=f'ShowCityWay:{city_id}')],
            [InlineKeyboardButton(text='🔄 Обновить', callback_data=f'UpdateCityWay:{city_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'UpdateCustomerCity:{city_id}')]
        ]
    )


def confirmation_update_day_shift(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewDayShift'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'UpdateCustomerShift:{customer_id}')]
        ]
    )


def confirmation_update_night_shift(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewNightShift'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'UpdateCustomerShift:{customer_id}')]
        ]
    )


def confirmation_save_job(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewJob'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_save_city(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewCity'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_update_city(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='UpdateNewCity'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_save_customer_admin(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewCustomerAdmin'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_save_customer_group(
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewCustomerGroup'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_save_customer_foreman(customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewCustomerForeman'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirmation_save_new_amount(
        customer_id: int,
        job_id: int
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data=f'SaveNewCustomerJobAmount:{job_id}'),
             InlineKeyboardButton(text="❌ Отменить", callback_data=f'Customer:{customer_id}')]
        ]
    )


async def delete_customer_admins(customer_id):
    keyboard = InlineKeyboardBuilder()
    customer_admins = await db.get_customer_admins(customer_id=customer_id)

    for customer_admin in customer_admins:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👤 {customer_admin.admin_full_name}',
                callback_data=f'DeleteCustomerAdmin:{customer_admin.id}'
            )
        )

    keyboard.adjust(1)

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'CustomerAdminsMenu:{customer_id}'))

    return keyboard.as_markup()


async def delete_customer_groups(
        customer_id: int
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    customer_groups = await db.get_customer_groups(
        customer_id=customer_id
    )

    for group in customer_groups:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👥 {group.group_name}',
                callback_data=f'DeleteCustomerGroup:{group.id}'
            )
        )

    keyboard.adjust(1)

    keyboard.row(
        InlineKeyboardButton(
            text='Назад', callback_data=f'CustomerGroupsMenu:{customer_id}'
        )
    )

    return keyboard.as_markup()


async def delete_customer_foremen(customer_id):
    keyboard = InlineKeyboardBuilder()
    customer_foremen = await db.get_customer_foremen(customer_id=customer_id)

    for customer_foreman in customer_foremen:
        keyboard.add(
            InlineKeyboardButton(
                text=f'👤 {customer_foreman.full_name}',
                callback_data=f'DeleteCustomerForeman:{customer_foreman.id}'
            )
        )

    keyboard.adjust(1)

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'CustomerForemenMenu:{customer_id}'))

    return keyboard.as_markup()


def confirmation_delete_customer_admin(admin_id, customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmDeleteCustomerAdmin:{admin_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'DeleteCustomerAdminsMenu:{customer_id}')]
        ]
    )


def confirmation_delete_customer_group(
        group_id: int,
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmDeleteCustomerGroup:{group_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'DeleteCustomerGroupsMenu:{customer_id}')]
        ]
    )


def confirmation_delete_customer_foreman(foreman_id, customer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Да', callback_data=f'ConfirmDeleteCustomerForeman:{foreman_id}'),
             InlineKeyboardButton(text='Нет', callback_data=f'DeleteCustomerForemenMenu:{customer_id}')]
        ]
    )


def customer_jobs_menu(
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить услугу", callback_data=f'NewCustomerJob:{customer_id}')],
            [InlineKeyboardButton(text='🔄 Обновить оплату', callback_data=f'UpdateCustomerJobAmount:{customer_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')]
        ]
    )


def jobs_for_payment_menu(
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить услугу", callback_data=f'NewJobForPayment:{customer_id}')],
            [InlineKeyboardButton(text='❌ Удалить услугу', callback_data=f'DeleteJobForPaymentMenu:{customer_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')]
        ]
    )


def no_jobs_por_payment(
        customer_id: int
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data=f'OpenPaymentJobsMenu:{customer_id}')],
        ]
    )


def delete_jobs_for_payment_menu(
        jobs: list[db.JobForPayment],
        menu_page: int,
        customer_id: int,
        items_on_page: int = 8,
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    total_pages = ceil(len(jobs) / items_on_page)
    items = menu_page * items_on_page

    for index in range(items - items_on_page, len(jobs)):
        if index >= items or index > len(jobs):
            break

        keyboard.row(
            InlineKeyboardButton(
                text=jobs[index].name,
                callback_data=DeleteJobFPCallbackData(
                    job_id=jobs[index].id,
                    action='ConfDelJobFP',
                    menu_page=menu_page,
                    customer_id=customer_id,
                ).pack()
            )
        )

    if items_on_page >= items >= len(jobs):
        pass
    elif items == items_on_page:
        keyboard.row(
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=DeleteJobFPCallbackData(
                    action='ForwardDelJobFP',
                    menu_page=menu_page,
                    customer_id=customer_id,
                ).pack()
            )
        )
    elif items >= len(jobs):
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=DeleteJobFPCallbackData(
                    action='BackDelJobFP',
                    menu_page=menu_page,
                    customer_id=customer_id,
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            )
        )
    else:
        keyboard.row(
            InlineKeyboardButton(
                text="Назад ◀️", callback_data=DeleteJobFPCallbackData(
                    action='BackDelJobFP',
                    menu_page=menu_page,
                    customer_id=customer_id,
                ).pack()
            ),
            InlineKeyboardButton(
                text=f'{menu_page}/{total_pages}', callback_data="None"
            ),
            InlineKeyboardButton(
                text="▶️ Вперед", callback_data=DeleteJobFPCallbackData(
                    action='ForwardDelJobFP',
                    menu_page=menu_page,
                    customer_id=customer_id,
                ).pack()
            )
        )

    return keyboard.as_markup()


def confirmation_delete_job_fp(
        menu_page: int,
        customer_id: int,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Да', callback_data=DeleteJobFPCallbackData(
                        action='ConfirmDeleteJobFP',
                        menu_page=menu_page,
                        customer_id=customer_id,
                    ).pack()
                ),
                InlineKeyboardButton(
                    text='Нет', callback_data=DeleteJobFPCallbackData(
                        action='BackToDelJobFP',
                        menu_page=menu_page,
                        customer_id=customer_id,
                    ).pack()
                ),
            ]
        ]
    )


def customer_jobs_to_update(
        customer_id: int,
        jobs: List[db.CustomerJob]
) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    for job in jobs:
        keyboard.add(
            InlineKeyboardButton(
                text=job.job,
                callback_data=f'UpdateAmount:{job.id}'
            )
        )

    keyboard.adjust(2)
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data=f'OpenJobsMenu:{customer_id}'))

    return keyboard.as_markup()


def customer_email_management_menu(customer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Редактировать email', callback_data=f'EditCustomerEmails:{customer_id}')],
            [InlineKeyboardButton(text='Назад', callback_data=f'Customer:{customer_id}')]
        ]
    )


def confirm_save_customer_emails(customer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Сохранить', callback_data=f'SaveCustomerEmails:{customer_id}'),
             InlineKeyboardButton(text='❌ Отменить', callback_data=f'Customer:{customer_id}')]
        ]
    )
