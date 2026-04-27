"""
Состояния FSM для бота исполнителя Max
Адаптировано из Telegram бота
"""
from maxapi.context import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации исполнителя"""
    request_city = State()              # Запрос выбора города
    request_phone_number = State()      # Запрос номера телефона (вход)
    verification_code = State()         # Ввод кода верификации (вход)
    # Новая регистрация: форма данных (как в TG боте)
    reg_last_name = State()             # Фамилия
    reg_first_name = State()            # Имя
    reg_middle_name = State()           # Отчество
    reg_inn = State()                   # ИНН
    reg_card = State()                  # Номер карты
    reg_phone = State()                 # Телефон (в конце формы)
    registration_code = State()         # Ввод SMS-кода при новой регистрации
    # Подписание договора
    sign_contract_code = State()        # Ввод PIN для подписания
    # Устаревшие состояния (используются в update_data_for_security)
    request_card_number = State()
    request_inn = State()
    phone_number_for_security = State()
    last_name_for_security = State()
    first_name_for_security = State()
    middle_name_for_security = State()
    birthday = State()
    request_gender = State()
    passport_series = State()
    passport_number = State()
    passport_date = State()
    passport_dept_code = State()
    passport_issued_by = State()


class SearchOrdersStates(StatesGroup):
    """Состояния поиска заявок"""
    browsing_customers = State()  # Просмотр списка получателей услуг
    viewing_orders = State()  # Просмотр заявок конкретного получателя
    confirmation_respond = State()  # Подтверждение отклика на заявку


class ApplicationsStates(StatesGroup):
    """Состояния управления заявками"""
    viewing_applications = State()  # Просмотр своих заявок
    removing_application = State()  # Удаление заявки


class ProfileStates(StatesGroup):
    """Состояния профиля исполнителя"""
    viewing_profile = State()  # Просмотр профиля
    updating_data = State()  # Обновление данных
    card_to_update = State()  # Ввод новой карты
    sign_contract_code_update_card = State()  # Код подписания договора при смене карты
    request_payment_amount = State()  # Ввод суммы выплаты из начислений
    payment_pin_confirm = State()  # Ввод 4 последних цифр ИНН для подтверждения выплаты
    receipt_url_input = State()  # Ожидание ссылки или фото QR-кода чека


class ChangeCityStates(StatesGroup):
    """Состояния смены города"""
    confirming_change = State()  # Подтверждение смены города
    choosing_city = State()  # Выбор нового города
    final_confirmation = State()  # Финальное подтверждение


class ReferralStates(StatesGroup):
    """Состояния реферальной системы"""
    viewing_referral = State()  # Просмотр реферальной информации


class ShoutStates(StatesGroup):
    """Состояния оповещения на объекте (для представителей)"""
    shout_menu = State()  # Меню оповещения
    enter_message = State()  # Ввод сообщения для оповещения
    viewing_stats = State()  # Просмотр статистики отправленных оповещений


class OrderForFriendStates(StatesGroup):
    """Состояния флоу «Заявка для друга»"""
    search_by_phone = State()   # Ожидание ввода номера телефона друга
    search_by_inn = State()     # Ожидание ввода ИНН друга
    code_for_order = State()    # Ожидание ввода SMS-кода подтверждения


class HelpStates(StatesGroup):
    """Состояния отправки обращения в поддержку"""
    enter_text = State()    # Ввод текста обращения
    enter_files = State()   # Загрузка файлов/фото


class ActStates(StatesGroup):
    """Состояния подписания акта выполненных работ"""
    pin_input = State()      # Ввод PIN (последние 4 цифры ИНН) для подписания


class ReceiptStates(StatesGroup):
    """Состояния ввода чека из «Мой налог»"""
    url_input = State()      # Ожидание ссылки или фото QR-кода чека
