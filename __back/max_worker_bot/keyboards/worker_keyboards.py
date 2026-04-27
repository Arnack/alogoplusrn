"""
Клавиатуры для бота исполнителя Max
Адаптировано из Telegram бота с использованием maxapi
"""
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

# Импорт кнопок из maxapi
from maxapi.types.attachments.buttons import (
    CallbackButton,
    LinkButton,
    MessageButton,
    RequestContactButton
)

from typing import List
import database as db


# ==================== ГЛАВНОЕ МЕНЮ ====================

def user_main_menu():
    """Главное меню исполнителя"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="👤 Обо мне", payload="about_me"),
        CallbackButton(text="🔍 Поиск заявок", payload="search_orders")
    )
    builder.row(
        CallbackButton(text="🆘 СВЯЗЬ С РУКОВОДСТВОМ", payload="contact_support"),
        CallbackButton(text="📝 Управление заявкой", payload="manage_applications")
    )
    builder.row(
        CallbackButton(text="💼 Заявка для друга", payload="order_for_friend")
    )
    return builder.as_markup()


def foreman_main_menu():
    """Главное меню для представителя исполнителя"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="👤 Обо мне", payload="about_me"),
        CallbackButton(text="🔍 Поиск заявок", payload="search_orders")
    )
    builder.row(
        CallbackButton(text="🆘 СВЯЗЬ С РУКОВОДСТВОМ", payload="contact_support"),
        CallbackButton(text="📝 Управление заявкой", payload="manage_applications")
    )
    builder.row(
        CallbackButton(text="📣 Оповещение на объекте", payload="shout_on_site"),
        CallbackButton(text="💼 Заявка для друга", payload="order_for_friend")
    )
    return builder.as_markup()


# ==================== РЕГИСТРАЦИЯ ====================

def entry_choice_max():
    """Выбор: войти или зарегистрироваться"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='🔑 Войти', payload='EntryLoginMax'),
        CallbackButton(text='📝 Регистрация', payload='EntryRegisterMax'),
    )
    return builder.as_markup()


def are_you_self_employed_max():
    """Опрос: вы самозанятый?"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='✅ Да', payload='RegYesSMZMax'),
        CallbackButton(text='❌ Нет', payload='RegNoSMZMax'),
    )
    return builder.as_markup()


def became_self_employed_max():
    """Кнопка «Я стал самозанятым»"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='✅ Я стал самозанятым', payload='RegBecameSMZMax'),
    )
    return builder.as_markup()


def skip_patronymic_max():
    """Кнопка пропуска отчества"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='➡️ Нет отчества', payload='RegSkipPatronymicMax'),
    )
    return builder.as_markup()


async def cities_keyboard():
    """Клавиатура выбора городов"""
    cities = await db.get_cities()
    builder = InlineKeyboardBuilder()

    for city in cities:
        builder.row(
            CallbackButton(text=f"📍 {city.city_name}", payload=f"RegCity:{city.city_name}")
        )

    return builder.as_markup()


def check_registration_keyboard(phone_number: str):
    """Клавиатура проверки статуса регистрации"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(
            text="🔄 Проверить статус регистрации",
            payload=f"CheckRegistration:{phone_number}"
        )
    )
    return builder.as_markup()


def gender_selection_keyboard():
    """Клавиатура выбора пола"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='👨 Мужской', payload='RegGenderMax:M'),
        CallbackButton(text='👩 Женский', payload='RegGenderMax:F'),
    )
    return builder.as_markup()


def accept_save_data_for_security():
    """Клавиатура подтверждения сохранения данных для охраны"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Сохранить", payload="SaveDataForSecurity")
    )
    builder.row(
        CallbackButton(text="✏️ Изменить данные", payload="NewDataForSecurity")
    )
    return builder.as_markup()


def registration_permission_request(api_worker_id: int):
    """Кнопка «Я дал разрешение» после инструкции Мой налог"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='✅ Я дал разрешение', payload=f'RegGavePermission:{api_worker_id}')
    )
    return builder.as_markup()


def request_phone_number_keyboard():
    """Клавиатура запроса номера телефона"""
    builder = InlineKeyboardBuilder()
    builder.row(
        RequestContactButton(text="📱 Отправить номер телефона")
    )
    return builder.as_markup()


def sign_api_contract_max():
    """Кнопки подписания/отказа от договора"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='📝 Подписать договор', payload='SignContractMax'),
        CallbackButton(text='❌ Отказаться', payload='RejectContractMax'),
    )
    return builder.as_markup()


# ==================== ПОИСК ЗАЯВОК ====================

async def customer_search_orders(customers: List[int], items: int, page: int):
    """
    Клавиатура выбора получателя услуг для поиска заявок

    Args:
        customers: Список ID получателей услуг
        items: Количество элементов на странице
        page: Номер текущей страницы
    """
    builder = InlineKeyboardBuilder()

    # Вычисляем диапазон элементов для текущей страницы
    start = (page - 1) * 5
    end = min(start + 5, len(customers))

    # Добавляем кнопки получателей услуг
    for customer_id in customers[start:end]:
        organization = await db.get_customer_organization(customer_id)
        builder.row(
            CallbackButton(
                text=f"🏢 {organization}",
                payload=f"CustomerSearchOrders:{customer_id}"
            )
        )

    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            CallbackButton(text="⬅️ Назад", payload="BackCustomerSearchOrders")
        )
    if end < len(customers):
        nav_buttons.append(
            CallbackButton(text="Вперед ➡️", payload="ForwardCustomerSearchOrders")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


async def show_order_for_search(page: int, orders, order_id: int):
    """
    Клавиатура для просмотра конкретной заявки в поиске

    Args:
        page: Номер текущей страницы
        orders: Список заявок
        order_id: ID текущей заявки
    """
    builder = InlineKeyboardBuilder()
    count = len(orders)

    # Кнопка отклика на заявку
    builder.row(
        CallbackButton(text="Взять заявку", payload=f"RespondToOrder:{order_id}")
    )

    # Навигация по заявкам (как в Telegram)
    if count == 1:
        pass  # Нет навигации, если одна заявка
    elif page == 1:
        builder.row(
            CallbackButton(text=f"{page}/{count}", payload="OrderCounter"),
            CallbackButton(text="▶️ Вперед", payload="SearchOrderForward")
        )
    elif page == count:
        builder.row(
            CallbackButton(text="Назад ◀️", payload="SearchOrderBack"),
            CallbackButton(text=f"{page}/{count}", payload="OrderCounter")
        )
    else:
        builder.row(
            CallbackButton(text="Назад ◀️", payload="SearchOrderBack"),
            CallbackButton(text=f"{page}/{count}", payload="OrderCounter"),
            CallbackButton(text="▶️ Вперед", payload="SearchOrderForward")
        )

    # Кнопка "Назад"
    builder.row(
        CallbackButton(text="Назад", payload="BackToCustomerSearchOrders")
    )

    return builder.as_markup()


def respond_to_an_order(order_id: int):
    """Клавиатура для отклика на заявку из уведомления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Взять заявку", payload=f"RespondToOrder:{order_id}")
    )
    return builder.as_markup()


async def way_to_work(customer_id: int, city: str):
    """Клавиатура 'Как добраться' для подтверждения заявки"""
    city_id = await db.get_customer_city_id(customer_id=customer_id, city=city)
    city_way = await db.get_customer_city_way(city_id=city_id) if city_id else None
    if city_way:
        builder = InlineKeyboardBuilder()
        builder.row(
            CallbackButton(text="‼️ℹ️📍🚍", payload=f"WorkerShowCityWay:{customer_id}:{city}")
        )
        return builder.as_markup()
    return None


def confirmation_respond_keyboard(order_id: int):
    """Клавиатура подтверждения отклика на заявку"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Подтверждаю", payload=f"ConfirmRespond:{order_id}")
    )
    builder.row(
        CallbackButton(text="❌ Отмена", payload="BackToSearchOrders")
    )
    return builder.as_markup()


# ==================== УПРАВЛЕНИЕ ЗАЯВКАМИ ====================

async def remove_application(order_id: int, worker_id: int, page: int, count: int, state):
    """
    Клавиатура управления заявкой исполнителя

    Args:
        order_id: ID заявки
        worker_id: ID исполнителя
        page: Номер текущей страницы
        count: Общее количество заявок
        state: Состояние FSM
    """
    builder = InlineKeyboardBuilder()

    # Получаем данные заявки
    application_id = await db.get_worker_application_id(order_id=order_id, worker_id=worker_id)
    order_worker = await db.get_order_worker(worker_id=worker_id, order_id=order_id)

    # Если заявка на модерации
    if application_id:
        builder.row(
            CallbackButton(text="❌ Удалить отклик", payload=f"RemoveApplication:{application_id}")
        )
    # Если заявка одобрена
    elif order_worker:
        builder.row(
            CallbackButton(text="⚠️ Отказаться от заявки", payload=f"RemoveWorker:{order_worker.id}")
        )

        # Кнопка маршрута для заявки
        order = await db.get_order(order_id=order_id)
        city_id = await db.get_customer_city_id(customer_id=order.customer_id, city=order.city)
        city_way = await db.get_customer_city_way(city_id=city_id) if city_id else None
        if city_way:
            builder.row(
                CallbackButton(text="🗺️ Маршрут", payload=f"WorkerShowCityWay:{order.customer_id}:{order.city}")
            )

    # Навигация по заявкам
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            CallbackButton(text="⬅️", payload="UserApplicationsBack")
        )

    nav_buttons.append(
        CallbackButton(text=f"{page}/{count}", payload="AppCounter")
    )

    if page < count:
        nav_buttons.append(
            CallbackButton(text="➡️", payload="UserApplicationsForward")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    return builder.as_markup()


def accept_remove_application(application_id: int):
    """Клавиатура подтверждения удаления отклика"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Да, удалить", payload=f"ConfirmRemoveApplication:{application_id}"),
        CallbackButton(text="❌ Отмена", payload="Reject")
    )
    return builder.as_markup()


def confirmation_remove_worker(worker_id: int):
    """Клавиатура подтверждения отказа от заявки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Да, отказаться", payload=f"ConfirmRemoveWorker:{worker_id}")
    )
    builder.row(
        CallbackButton(text="❌ Отмена", payload="Reject")
    )
    return builder.as_markup()


# ==================== ПРОФИЛЬ ====================

async def about_worker_keyboard(worker_id: int, api_worker_id: int = 0):
    """Клавиатура информации о работнике (идентична Telegram боту)"""
    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(text="💰 Получить вознаграждение", payload="CreateWorkerPayment")
    )
    builder.row(
        CallbackButton(text="📁 Подписанные договоры", payload=f"GetWorkerContracts:{api_worker_id}")
    )
    builder.row(
        CallbackButton(text="🎁 Акции", payload="OpenPromotions")
    )
    builder.row(
        CallbackButton(text="💵 Получить бонус", payload="GetBonus")
    )
    builder.row(
        CallbackButton(text="📑 Правила", payload="BotRules")
    )
    builder.row(
        CallbackButton(text="🔄 Обновить данные", payload="UpdateWorkerInfo")
    )
    builder.row(
        CallbackButton(text="❌ Удалить данные", payload="EraseWorkerInfo")
    )

    return builder.as_markup()


def act_sign_keyboard(act_id: int):
    """Клавиатура подписания/отказа от акта выполненных работ"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='✅ Подписать', payload=f'SignAct:{act_id}'),
        CallbackButton(text='❌ Отказаться', payload=f'RefuseAct:{act_id}'),
    )
    return builder.as_markup()


def confirmation_payment_keyboard(order_id: int):
    """Клавиатура подтверждения/отмены выплаты (аналог Telegram)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text='✅ Да', payload=f'WorkConfirmPayment:{order_id}'),
        CallbackButton(text='❌ Нет', payload=f'WorkCancelPayment:{order_id}'),
    )
    return builder.as_markup()


def promotions_keyboard(promos, participations: dict):
    """Клавиатура акций"""
    builder = InlineKeyboardBuilder()
    for p in promos:
        part = participations.get(p.id)
        if part:
            progress = (
                f'{part.current_streak}/{p.n_orders}'
                if p.type == 'streak'
                else f'{part.period_completed}/{p.n_orders}'
            )
            label = f'✅ {p.name} [{progress}]'
        else:
            label = f'🎁 {p.name}'
        builder.row(CallbackButton(text=label, payload=f'WorkerPromo:{p.id}'))
    if participations:
        builder.row(CallbackButton(text='❌ Отказаться от всех акций', payload='WorkerCancelAllPromos'))
    builder.row(CallbackButton(text='🔙 Назад', payload='BackToAboutMe'))
    return builder.as_markup()


# ==================== СМЕНА ГОРОДА ====================

def accept_change_city_keyboard():
    """Клавиатура подтверждения смены города"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Да", payload="AcceptChangeCity"),
        CallbackButton(text="❌ Нет", payload="RejectChangeCity")
    )
    return builder.as_markup()


async def choose_city_keyboard(current_city: str):
    """Клавиатура выбора нового города"""
    cities = await db.get_cities()
    builder = InlineKeyboardBuilder()

    for city in cities:
        if city.city_name != current_city:
            builder.row(
                CallbackButton(text=f"📍 {city.city_name}", payload=f"ChooseCity:{city.city_name}")
            )

    builder.row(
        CallbackButton(text="🔙 Назад", payload="BackToAboutMe")
    )

    return builder.as_markup()


def confirmation_change_city_keyboard(new_city: str):
    """Клавиатура финального подтверждения смены города"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Подтвердить смену", payload=f"ConfirmChangeCity:{new_city}")
    )
    builder.row(
        CallbackButton(text="❌ Отмена", payload="RejectChangeCity")
    )
    return builder.as_markup()


# ==================== РЕФЕРАЛЬНАЯ СИСТЕМА ====================

def referral_keyboard():
    """Клавиатура реферальной системы"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="🔙 Назад", payload="BackToAboutMe")
    )
    return builder.as_markup()


# ==================== ОПОВЕЩЕНИЕ НА ОБЪЕКТЕ ====================

async def shout_menu_keyboard(worker_id: int):
    """Меню оповещения на объекте для представителя"""
    builder = InlineKeyboardBuilder()

    # Получаем получателей услуг, где работник является представителем
    foreman_customers = await db.get_foreman_customers(worker_id=worker_id)

    for customer_id in foreman_customers:
        organization = await db.get_customer_organization(customer_id)
        builder.row(
            CallbackButton(
                text=f"📣 {organization}",
                payload=f"ShoutCustomer:{customer_id}"
            )
        )

    return builder.as_markup()


def shout_actions_keyboard(customer_id: int):
    """Клавиатура действий оповещения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="📝 Отправить оповещение", payload=f"SendShout:{customer_id}")
    )
    builder.row(
        CallbackButton(text="📊 Статистика", payload=f"ShoutStats:{customer_id}")
    )
    builder.row(
        CallbackButton(text="🔙 Назад", payload="BackToShoutMenu")
    )
    return builder.as_markup()


# ==================== ПРОЧЕЕ ====================

def support_keyboard():
    """Клавиатура поддержки"""
    builder = InlineKeyboardBuilder()
    builder.row(
        LinkButton(text="💬 Поддержка Telegram", url="https://t.me/helpmealgoritm")
    )
    return builder.as_markup()


def back_to_menu_keyboard():
    """Кнопка возврата в главное меню (профиль)"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Назад", payload="BackToAboutMe")
    )
    return builder.as_markup()


# ==================== ОБНОВЛЕНИЕ И УДАЛЕНИЕ ДАННЫХ ====================

async def choose_update_keyboard():
    """Клавиатура выбора что обновить"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="💳 Банковская карта", payload="UpdateWorkerBankCard")
    )
    builder.row(
        CallbackButton(text="👤 Данные для охраны", payload="UpdateFullNameForSecurity")
    )
    builder.row(
        CallbackButton(text="🌆 Город", payload="UpdateWorkerCity")
    )
    builder.row(
        CallbackButton(text="Назад", payload="BackToAboutMe")
    )
    return builder.as_markup()


async def erase_worker_info_keyboard():
    """Клавиатура подтверждения удаления данных"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Да", payload="ConfirmEraseWorkerData"),
        CallbackButton(text="Нет", payload="BackToAboutMe")
    )
    return builder.as_markup()


# ==================== ПОМОЩЬ / ПОДДЕРЖКА ====================

def help_skip():
    """Клавиатура пропуска загрузки файлов в обращении"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Пропустить", payload="skip_help_files")
    )
    return builder.as_markup()


def confirmation_send_help_message():
    """Клавиатура подтверждения отправки обращения"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="✅ Да", payload="SendHelpMessage"),
        CallbackButton(text="❌ Нет", payload="CancelSendHelpMessage")
    )
    return builder.as_markup()


# ==================== ЗАЯВКА ДЛЯ ДРУГА ====================

def order_for_friend_confirmation():
    """Клавиатура подтверждения начала процесса заявки для друга"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Продолжить", payload="ContinueOrderForFriend"),
        CallbackButton(text="Отменить", payload="CancelOrderForFriend")
    )
    return builder.as_markup()


def methods_search_friend():
    """Клавиатура выбора метода поиска друга"""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Номер телефона", payload="SearchWorkerByPhone"),
        CallbackButton(text="ИНН", payload="SearchWorkerByInn")
    )
    return builder.as_markup()


async def cities_for_order_for_friend():
    """Клавиатура выбора города для заявки друга"""
    builder = InlineKeyboardBuilder()
    cities = await db.get_cities_name()

    for city in cities:
        builder.add(
            CallbackButton(text=city, payload=f"CityForFriend:{city}")
        )

    builder.adjust(2)
    return builder.as_markup()
