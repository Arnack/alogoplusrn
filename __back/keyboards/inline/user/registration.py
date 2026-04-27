from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db


def entry_choice() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔑 Войти', callback_data='EntryLogin')],
            [InlineKeyboardButton(text='📝 Регистрация', callback_data='EntryRegister')],
        ]
    )


def are_you_self_employed() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Да', callback_data='RegYesSMZ'),
                InlineKeyboardButton(text='❌ Нет', callback_data='RegNoSMZ'),
            ]
        ]
    )


def skip_patronymic() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Нет отчества', callback_data='RegSkipPatronymic')]
        ]
    )


def became_self_employed_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Я стал самозанятым', callback_data='RegBecameSMZ')]
        ]
    )


async def cities_for_registration():
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city, callback_data=f'RegCity:{city}'))

    return keyboard.adjust(2).as_markup()


async def cities_for_login():
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city, callback_data=f'LoginCity:{city}'))

    return keyboard.adjust(2).as_markup()


def check_registration(phone_number):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Проверить статус регистрации",
                callback_data=f'CheckRegistration:{phone_number}',
            )]
        ]
    )


def confirmation_save_data_for_security():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveDataForSecurity')],
            [InlineKeyboardButton(text="🔄 Ввести другие данные", callback_data='NewDataForSecurity')]
        ]
    )


def confirmation_update_data_for_security():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data='SaveNewDataForSecurity')],
            [InlineKeyboardButton(text="🔄 Ввести другие данные", callback_data='UpdateDataForSecurity')]
        ]
    )


def confirmation_became_self_employment(
        api_worker_id: int,
        go_to_rr: bool = False,
) -> InlineKeyboardMarkup:
    prefix = 'GTRR' if go_to_rr else 'Reg'
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='Я стал самозанятым',
                    callback_data=f'{prefix}GavePermission:{api_worker_id}'
                )
            ]
        ]
    )


def registration_permission_request(
        api_worker_id: int,
        go_to_rr: bool = False,
) -> InlineKeyboardMarkup:
    prefix = 'GTRR' if go_to_rr else 'Reg'
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='🔄 Проверить ещё раз', callback_data=f'{prefix}GavePermission:{api_worker_id}'
            )]
        ]
    )


def gender_selection() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='👨 Мужской', callback_data='RegGender:M'),
                InlineKeyboardButton(text='👩 Женский', callback_data='RegGender:F'),
            ]
        ]
    )


def sign_api_contract(
        go_to_rr: bool = False,
) -> InlineKeyboardMarkup:
    postfix = 'GTRR' if go_to_rr else ''
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✍️ Подписать договор', callback_data=f'SignContract{postfix}'),
             InlineKeyboardButton(text='❌ Отказаться', callback_data=f'RejectContract{postfix}')]
        ]
    )
