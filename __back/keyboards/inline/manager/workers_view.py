from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
import database as db


async def cities_for_workers():
    """Клавиатура выбора города для просмотра самозанятых"""
    keyboard = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        keyboard.add(InlineKeyboardButton(text=city, callback_data=f'WorkersViewCity:{city}'))

    # Размещаем города в 2 столбца
    keyboard.adjust(2)

    # Добавляем кнопку поиска по всем участкам отдельной строкой
    keyboard.row(InlineKeyboardButton(text='🔍 Поиск смз по всем участкам', callback_data='WorkersViewSearchAll'))

    return keyboard.as_markup()


def workers_menu():
    """Главное меню самозанятых (после выбора города)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📄 Сформировать PDF', callback_data='WorkersViewPDF')],
            [InlineKeyboardButton(text='📋 Люди', callback_data='WorkersViewPeople')]
        ]
    )


def workers_list_keyboard(workers: List[db.User], page: int = 0, total_pages: int = 1):
    """
    Клавиатура со списком самозанятых (пагинация 20 человек на страницу, 2 столбца)

    Args:
        workers: Список самозанятых для отображения
        page: Текущая страница (начиная с 0)
        total_pages: Общее количество страниц
    """
    keyboard = InlineKeyboardBuilder()

    # Добавляем кнопки с самозанятыми (формат: ФАМИЛИЯ И.О.)
    for worker in workers:
        # Формируем текст: ФАМИЛИЯ И.О.
        first_initial = worker.first_name[0] if worker.first_name else ''
        middle_initial = worker.middle_name[0] if worker.middle_name else ''

        if middle_initial:
            button_text = f'{worker.last_name.upper()} {first_initial}.{middle_initial}.'
        else:
            button_text = f'{worker.last_name.upper()} {first_initial}.'

        keyboard.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f'WorkersViewPerson:{worker.id}'
        ))

    # Размещаем в 2 столбца
    keyboard.adjust(2)

    # Добавляем навигацию если страниц больше одной
    if total_pages > 1:
        nav_buttons = []

        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text='◀️ Назад', callback_data=f'WorkersViewPeoplePage:{page - 1}'))

        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text='Вперёд ▶️', callback_data=f'WorkersViewPeoplePage:{page + 1}'))

        if nav_buttons:
            keyboard.row(*nav_buttons)

    return keyboard.as_markup()


def search_results_keyboard(workers: List[db.User], search_query: str):
    """
    Клавиатура с результатами поиска по фамилии

    Args:
        workers: Список найденных самозанятых
        search_query: Фамилия для поиска
    """
    keyboard = InlineKeyboardBuilder()

    for worker in workers:
        # Полное ФИО для результатов поиска
        full_name = f'{worker.last_name} {worker.first_name}'
        if worker.middle_name:
            full_name += f' {worker.middle_name}'

        keyboard.add(InlineKeyboardButton(
            text=full_name,
            callback_data=f'WorkersViewSearchResult:{worker.id}:{search_query}'
        ))

    # Каждый результат на отдельной строке
    keyboard.adjust(1)

    return keyboard.as_markup()


def search_results_keyboard_with_city(workers: List[db.User], search_query: str):
    """
    Клавиатура с результатами поиска по фамилии с указанием города

    Args:
        workers: Список найденных самозанятых
        search_query: Фамилия для поиска
    """
    keyboard = InlineKeyboardBuilder()

    for worker in workers:
        # Полное ФИО с городом для результатов поиска
        full_name = f'{worker.last_name} {worker.first_name}'
        if worker.middle_name:
            full_name += f' {worker.middle_name}'

        # Добавляем город в скобках
        button_text = f'{full_name} ({worker.city})'

        keyboard.add(InlineKeyboardButton(
            text=button_text,
            callback_data=f'WorkersViewSearchAllResult:{worker.id}:{search_query}'
        ))

    # Каждый результат на отдельной строке
    keyboard.adjust(1)

    return keyboard.as_markup()
