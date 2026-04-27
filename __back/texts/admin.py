from typing import Optional
from decimal import Decimal


def start_admin():
    return ("👋 <b>Добро пожаловать в панель администратора!\n\n"
            "Здесь вы полностью управляете платформой:</b>\n"
            "<blockquote>👥 <b>Менеджеры</b> — добавить, удалить, посмотреть менеджеров\n"
            "🏢 <b>Получатели услуг</b> — внести и изменить данные получателя услуг\n"
            "👤 <b>Исполнители (НПД)</b> — заблокировать / разблокировать, изменить рейтинг, посмотреть сколько в системе\n"
            "📦 <b>Заявки</b> — создать или закрыть заявку от имени любого получателя услуг\n"
            "🦺 <b>Координаторы</b> — добавить координатора (из исполнителей)\n"
            "💳 <b>Кассиры</b> — добавить кассира, контроль выплат\n"
            "⚙️ <b>Настройки</b> — настроить бонусную систему и почту\n"
            "📊 <b>Математика</b> — увидеть экономию платформы за счёт рейтинга\n"
            "📄 <b>Сформировать сверку</b> — сверка за 31 день по любому получателю услуг</blockquote>\n\n"
            "⬇️ Используйте кнопки ниже")


def show_chat_id(
        chat_id: int
) -> str:
    return f'🆔 Телеграм ID чата: <code>{chat_id}</code>'


def admin_settings(shifts, bonus):
    return "<b>⚙️ Настройки</b>\n\n" \
           "В этом разделе вы настраиваете <b>бонусную систему</b> и <b>служебные почтовые адреса</b>.\n\n" \
           "<blockquote>📝 <b>Количество выходов</b> — укажите необходимое количество заявок для получения бонуса\n" \
           "💸 <b>Размер бонуса</b> — задайте сумму бонуса\n" \
           "📬 <b>Наша почта</b> — добавьте корпоративные e-mail адреса\n" \
           "🧳 <b>Главное меню</b> — вернуться в основное меню</blockquote>\n\n\n" \
           "⬇️ Используйте кнопки ниже"


def update_shifts():
    return "ℹ️ Введите новое количество выходов:"


def update_bonus():
    return "ℹ️ Введите новый размер бонуса:"


def number_error():
    return "❗Введите целое число:"


def save_settings():
    return "✅ Настройки успешно обновлены!"


def customers():
    return "<b>👥 Управление получателями услуг</b>\n" \
           "Выберите действие:"


def managers():
    return "<b>👥 Управление менеджерами</b>\n" \
           "Выберите действие:"


def accountants():
    return "<b>👥 Управление кассирами</b>\n" \
           "Выберите действие:"


def supervisors():
    return "<b>👥 Управление координаторами</b>\n" \
           "Выберите действие:"


def customers_none():
    return "📋 Список получателей услуг пуст"


def managers_none():
    return "📋 Список менеджеров пуст"


def no_accountants():
    return "📋 Список кассиров пуст"


def no_supervisors():
    return "📋 Список координаторов пуст"


def customers_list():
    return "📋 Список получателей услуг открыт. Нажмите на него, " \
           "чтобы увидеть больше информации о нем:"


def confirmation_delete_customer():
    return "👤 Вы уверены что хотите удалить получателя услуг? "


def managers_list():
    return "📋 Список менеджеров открыт. Нажмите на менеджера, " \
           "чтобы увидеть больше информации о нем:"


def accountants_list():
    return "📋 Список кассиров открыт. Нажмите на кассира, " \
           "чтобы увидеть больше информации о нем:"


def supervisors_list():
    return "📋 Список координаторов открыт. Нажмите на координатора, " \
           "чтобы увидеть больше информации о нем:"


def customer_info(organization, admins, foremen, customer_cities, jobs, customer_day_shift, customer_night_shift):
    text = f"<b>Информация по получателю услуг</b>\n" \
           f"🏢 <b>Организация:</b> {organization}\n"

    if len(admins) > 1:
        text += f"👥 <b>Представители получателя услуг:</b> {', '.join(admins)}\n"
    elif not admins:
        text += f"👥 <b>Представители получателя услуг:</b> Нет\n"
    else:
        text += f"👤 <b>Представитель получателя услуг:</b> {admins[0]}\n"

    if len(foremen) > 1:
        text += f"👥 <b>Представители исполнителя:</b> {', '.join(foremen)}\n"
    elif not foremen:
        text += f"👥 <b>Представители исполнителя:</b> Нет\n"
    else:
        text += f"👤 <b>Представитель исполнителя:</b> {foremen[0]}\n"

    if len(customer_cities) > 1:
        text += f"🌆 <b>Города:</b> {', '.join(customer_cities)}\n"
    else:
        text += f"🌆 <b>Город:</b> {customer_cities[0]}\n"

    if len(jobs) > 1:
        text += f"🛂 <b>Услуги:</b> " \
                f"{', '.join(f'{job.job} ({job.amount.amount}₽)' if job.amount else f'{job.job}' for job in jobs)}\n"
    else:
        text += f"🛂 <b>Услуга:</b> " \
                f"{f'{jobs[0].job} ({jobs[0].amount.amount}₽)' if jobs[0].amount else f'{jobs[0].job}'}\n"

    if customer_day_shift:
        text += f"☀️ <b>День:</b> {customer_day_shift}\n"
    else:
        text += f"☀️ <b>День:</b> Нет\n"

    if customer_night_shift:
        text += f"🌙 <b>Ночь:</b> {customer_night_shift}"
    else:
        text += f"🌙 <b>Ночь:</b> Нет\n"
    return text


def manager_info(name, manager_id):
    return f"<b>Информация по менеджеру</b>\n" \
           f"👤 Имя: {name}\n" \
           f"🆔 ID: {manager_id}"


def accountant_info(
        full_name: str,
        tg_id: int
) -> str:
    return f"<b>Информация по кассиру</b>\n" \
           f"👤 Имя: {full_name}\n" \
           f"🆔 ID: {tg_id}"


def supervisor_info(
        full_name: str,
        tg_id: int
) -> str:
    return f"<b>Информация по координатору</b>\n" \
           f"👤 Имя: {full_name}\n" \
           f"🆔 ID: {tg_id}"


def add_customer_organization():
    return "🏢 Введите название получателя услуг (организации):"


def add_customer_cities():
    return "🌆 Введите названия городов (по очереди), в которых есть получатель услуг:"


def no_cities():
    return "🌆 Вы не ввели еще ни один город! Введите название города:"


def add_city_more():
    return "🌆 Введите название города. Если закончили нажмите на кнопку [Далее]:"


def add_city_way_description():
    return "✏️ Введите способ добраться (описание):"


def enter_city_way_description():
    return "✏️ Сначала введите способ добраться:"


def add_city_way_photo():
    return "🌅 Отправьте фото для способа добраться (максимум 2) или нажмите на кнопку " \
           "[Пропустить]:"


def confirmation_save_city_way() -> str:
    return 'Сохранить новый способ добраться?'


def add_city_way_photo_more():
    return "🌅 Отправьте ещё одно фото или нажмите на кнопку [Далее]:"


def city_way_added() -> str:
    return f'✅ Способ добраться был успешно добавлен'


def city_way_updated() -> str:
    return f'✅ Способ добраться был успешно обновлен'


def add_city_way_error() -> str:
    return f'❗Не удалось добавить способ добраться'


def add_customer_jobs():
    return "🛂 Введите названия услуг (по очереди), которые есть у получателя услуг:"


def add_jobs_more():
    return "🛂 Введите название услуги. Если закончили нажмите на кнопку [Далее]:"


def no_jobs():
    return "🛂 Вы не ввели еще ни одной услуги! Введите название:"


def add_job_amount() -> str:
    return "💵 Введите оплату для услуги:"


def enter_job_amount() -> str:
    return "💵 Сначала введите оплату для услуги:"


def add_customer_admin_fio():
    return "👤 Введите ФИО представителя получателя услуг:"


def request_group_name():
    return "👥 Введите название чата:"


def add_customer_admin_tg_id():
    return "🆔 Введите телеграм ID представителя получателя услуг:"


def request_group_any_message():
    return "🆔 Введите телеграм ID чата:"


def enter_tg_id():
    return "🆔 Сначала введите телеграм ID представителя:"


def add_admins_more():
    return "👤 Введите ФИО представителя получателя услуг. Если закончили нажмите на кнопку [Далее]:"


def none_admins():
    return "👤 Вы не добавили еще ни одного представителя! Введите ФИО:"


def add_customer_foreman_full_name():
    return "👤 Введите ФИО представителя исполнителя:"


def add_customer_foreman_tg_id():
    return "🆔 Введите телеграм ID представителя исполнителя:"


def enter_foreman_tg_id():
    return "🆔 Сначала введите телеграм ID представителя исполнителя:"


def add_foremen_more():
    return "👤 Введите ФИО представителя исполнителя. Если закончили нажмите на кнопку [Далее]:"


def no_foremen():
    return "👤 Вы не добавили еще ни одного представителя исполнителя! Введите ФИО:"


def day_shift():
    return "⌛ Введите время для <b>Дневного периода оказания услуг</b> в формате ЧЧ:ММ-ЧЧ:ММ\n" \
           "Например: 07:30-19:00\n" \
           "Если ее нет, нажмите на кнопку [Пропустить]"


def night_shift():
    return "⌛ Введите время для <b>Ночного периода оказания услуг</b> в формате ЧЧ:ММ-ЧЧ:ММ\n" \
           "Например: 19:00-06:00\n" \
           "Если ее нет, нажмите на кнопку [Пропустить]"


def add_id_error():
    return "🆔 Введите число:"


def confirmation_add_new_customer(
        organization: str,
        admins: dict,
        foremen: dict,
        _customer_cities: dict,
        jobs: dict,
        customer_day_shift: Optional[str],
        customer_night_shift: Optional[str]
):
    text = "<b>Сохранить следующие данные?</b>\n" \
           f"🏢 <b>Организация:</b> {organization}\n" \
           f"🆔 <b>Представители получателя услуг:</b> " \
           f"{', '.join(f'{full_name} ({tg_id})' for full_name, tg_id in admins.items())}\n" \
           f"👤 <b>Представители исполнителя:</b> " \
           f"{', '.join(f'{full_name} ({tg_id})' for full_name, tg_id in foremen.items())}\n" \
           f"🌆 <b>Города:</b> {', '.join(_customer_cities)}\n" \
           f"🛂 <b>Услуги:</b> {', '.join(f'{job_name} ({amount}₽)' for job_name, amount in jobs.items())}\n"

    if customer_day_shift:
        text += f"☀️ <b>День:</b> {customer_day_shift}\n"
    else:
        text += f"☀️ <b>День:</b> Нет\n"

    if customer_night_shift:
        text += f"🌙 <b>Ночь:</b> {customer_night_shift}"
    else:
        text += f"🌙 <b>Ночь:</b> Нет\n"
    return text


def customer_added():
    return "✅ Получатель услуг был успешно добавлен!"


def add_customer_error():
    return "❗Не удалось добавить получателя услуг"


def manager_added():
    return "✅ Менеджер был успешно добавлен!"


def accountant_added():
    return "✅ Кассир был успешно добавлен!"


def supervisor_added():
    return "✅ Координатор был успешно добавлен!"


def add_accountant_error():
    return "❗Не удалось добавить кассира"


def add_supervisor_error():
    return "❗Не удалось добавить координатора"


def add_manager_id():
    return "🆔 Введите телеграм ID менеджера:"


def request_accountant_tg_id():
    return "🆔 Введите телеграм ID кассира:"


def request_supervisor_tg_id():
    return "🆔 Введите телеграм ID координатора:"


def add_manager_full_name():
    return "👤 Введите ФИО менеджера:"


def request_accountant_full_name():
    return "👤 Введите ФИО кассира:"


def request_supervisor_full_name():
    return "👤 Введите ФИО координатора:"


def accept_new_manager(manager, name):
    return "<b>Сохранить нового менеджера?</b>\n" \
           f"Имя: {name}\n" \
           f"🆔 ID менеджера: {manager}"


def confirmation_add_new_accountant(
        tg_id: int | str,
        full_name: str
) -> str:
    return "<b>Сохранить нового кассира?</b>\n" \
           f"Имя: {full_name}\n" \
           f"🆔 ID кассира: {tg_id}"


def confirmation_add_new_supervisor(
        tg_id: int | str,
        full_name: str
) -> str:
    return "<b>Сохранить нового координатора?</b>\n" \
           f"Имя: {full_name}\n" \
           f"🆔 ID координатора: {tg_id}"


def customer_deleted():
    return "✅ Получатель услуг был успешно удален!"


def confirmation_delete_accountant():
    return f'ℹ️ Вы уверены, что хотите удалить кассира?'


def confirmation_delete_supervisor():
    return f'ℹ️ Вы уверены, что хотите удалить координатора?'


def manager_deleted():
    return "✅ Менеджер был успешно удален!"


def accountant_deleted():
    return "✅ Кассир был успешно удален!"


def supervisor_deleted():
    return "✅ Координатор был успешно удален!"


def customer_cities():
    return "<b>🌆 Управление городами получателя услуг</b>\n" \
           "Выберите действие:"


def add_city():
    return "🌆 Введите название нового города:"


def confirmation_save_city(city, organization):
    return f"Сохранить город \"{city}\" для «{organization}»?"


def new_city_added():
    return "✅ Город был успешно добавлен!"


def save_city_error():
    return '❗ Не удалось сохранить новый город'


def customer_cities_list():
    return "🌆 Нажмите на город, который хотите отредактировать:"


def choose_customer_city_update():
    return "ℹ️ Выберите, что хотите обновить в этом городе:"


def update_city():
    return "🌆 Введите новое название города:"


def city_updated():
    return "✅ Город был успешно обновлен!"


def update_city_error():
    return '❗ Не удалось обновить город'


def confirmation_update_city_for_customer(city, organization):
    return f"Сохранить город \"{city}\" для «{organization}»?"


def block_worker_fio():
    return "👤 Введите реальное Ф.И.О. исполнителя (НПД) <b>без ошибок</b>\n(Пример: Иванов Иван Иванович):"


def blocked_workers_info() -> str:
    return 'ℹ️ Нажмите на исполнителя, которого хотите разблокировать:'


def no_blocked_workers() -> str:
    return 'ℹ️ В боте нет еще ни одного заблокированного пользователя'


def confirmation_unblock_user(last_name, first_name, middle_name):
    return f"Вы уверены, что хотите разблокировать исполнителя (НПД) <b>{last_name} {first_name} {middle_name}</b>?"


def confirmation_block_user(
        full_name: str
) -> str:
    return f"Вы уверены, что хотите заблокировать исполнителя (НПД) <b>{full_name}</b>?"


def search_worker_by_full_name_error():
    return f'❗<b>Неправильный формат ввода.</b> ' \
           f'<blockquote>Между фамилией, именем и отчеством обязательно должны быть пробелы.</blockquote> ' \
           f'Введите Ф.И.О. еще раз:'


def worker_unblocked():
    return "✅ Исполнитель (НПД) был успешно разблокирован!"


def worker_blocked():
    return "✅ Исполнитель (НПД) был успешно заблокирован!"


def block_worker_error():
    return "❗Не удалось заблокировать исполнителя (НПД)"


def unblock_worker_error():
    return "❗Не удалось разблокировать исполнителя (НПД)"


def unblock_cancel():
    return "ℹ️ Разблокирование исполнителя (НПД) было отменено"


def block_cancel():
    return "ℹ️ Блокирование исполнителя (НПД) было отменено"


def worker_not_found():
    return "ℹ️ Исполнитель (НПД) не найден.\nПоиск отменен"


def stats(workers_count):
    return "<b>📊 Статистика</b>\n" \
           f"<blockquote>👥 Зарегистрировано исполнителей (НПД): {workers_count}</blockquote>"


def workers_pdf():
    return f"⌛ Подождите немного. PDF-файл с исполнителями (НПД) скоро будет сформирован"


def update_customer_shift():
    return 'Выберите какой период оказания услуг хотите изменить:'


def update_customer_day_shift():
    return "⌛ Введите время для <b>Дневного периода оказания услуг</b> в формате ЧЧ:ММ-ЧЧ:ММ\n" \
           "Например: 07:30-19:00"


def update_customer_night_shift():
    return "⌛ Введите время для <b>Ночного периода оказания услуг</b> в формате ЧЧ:ММ-ЧЧ:ММ\n" \
           "Например: 19:00-06:00"


def time_error():
    return '❗Неверный формат. Введите время в следующем виде: ЧЧ:ММ-ЧЧ:ММ\n' \
           'Например: 07:30-19:00'


def confirmation_save_day_shift(organization, time):
    return f'Обновить дневной период оказания услуг [{time}] для «{organization}»?'


def confirmation_save_night_shift(organization, time):
    return f'Обновить ночной период оказания услуг [{time}] для «{organization}»?'


def day_shift_updated():
    return '✅ Дневной период оказания услуг был успешно обновлен'


def night_shift_updated():
    return '✅ Ночной период оказания услуг был успешно обновлен'


def update_day_shift_error():
    return '❗Не удалось обновить дневной период оказания услуг'


def update_night_shift_error():
    return '❗Не удалось обновить ночной период оказания услуг'


def add_customer_job():
    return "🛂 Введите название услуги:"


def customer_jobs_menu() -> str:
    return "<b>🛂 Управление услугами получателя</b>\n" \
           "Выберите действие:"


def jobs_for_payment_menu() -> str:
    return "<b>🛂 Управление услугами для вознаграждений</b>\n" \
           "Выберите действие:"


def delete_job_for_payment_menu() -> str:
    return "<b>🛂 Выберите услугу, которую хотите удалить:</b>"


def confirmation_delete_job_fp() -> str:
    return 'ℹ️ Вы уверены, что хотите удалить услугу?'


def no_jobs_por_payment() -> str:
    return 'ℹ️ Список услуг для вознаграждений пуст'


def job_fp_deleted() -> str:
    return '✅ Услуга успешно удалена'


def delete_job_fp_error() -> str:
    return '❗Не удалось удалить услугу'


def customer_job_to_update() -> str:
    return "ℹ️ Выберите услугу, к которой хотите обновить оплату:"


def request_new_amount() -> str:
    return "💵 Введите новую оплату для услуги:"


def confirmation_save_new_amount(
        job_name: str,
        new_amount: str
) -> str:
    return f'Сохранить новую оплату в размере {new_amount}₽ для {job_name}?'


def new_amount_saved() -> str:
    return "✅ Новая оплата для услуги успешно сохранена"


def save_amount_error() -> str:
    return "❗Не удалось сохранить новую оплату для услуги"


def confirmation_save_job(
        organization: str,
        job: str,
        amount: str
) -> str:
    return f'Сохранить новую услугу \"{job} ({amount}₽)\" для «{organization}»?'


def new_job_added():
    return '✅ Новая услуга была успешно добавлена'


def save_job_error():
    return '❗Не удалось сохранить новую услугу'


def add_customer_admin_ftio():
    return "🛂 Введите название услуги:"


def customer_admins():
    return "<b>👥 Управление представителями получателя услуг</b>\n" \
           "Выберите действие:"


def customer_groups():
    return "<b>👥 Управление корпоративными чатами</b>\n" \
           "Выберите действие:"


def customer_foremen():
    return "<b>👥 Управление представителями исполнителя</b>\n" \
           "Выберите действие:"


def confirmation_save_customer_admin(admin_fio, admin_id, organization):
    return f'👤 Сохранить нового представителя \"{admin_fio} ({admin_id})\" для «{organization}»?'


def confirmation_save_customer_group(
        group_name: str,
        organization: str
) -> str:
    return f'👤 Сохранить новый корпоративный чат \"{group_name}\" для «{organization}»?'


def confirmation_save_customer_foreman(admin_fio, admin_id, organization):
    return f'👤 Сохранить нового представителя исполнителя \"{admin_fio} ({admin_id})\" для «{organization}»?'


def new_customer_admin_added():
    return '✅ Новый представитель получателя услуг был успешно добавлен'


def new_customer_group_added():
    return '✅ Новый корпоративный чат был успешно добавлен'


def new_customer_foreman_added():
    return '✅ Новый представитель исполнителя был успешно добавлен'


def save_customer_admin_error():
    return '❗Не удалось сохранить нового представителя для получателя услуг'


def save_customer_group_error():
    return '❗Не удалось сохранить новую корпоративную группу'


def save_customer_foreman_error():
    return '❗Не удалось сохранить нового представителя исполнителя'


def delete_customer_admins_menu():
    return 'ℹ️ Выберите представителя, которого хотите удалить:'


def delete_customer_representative_menu():
    return 'ℹ️ Выберите представителя, которого хотите удалить:'


def delete_customer_group_menu():
    return 'ℹ️ Выберите корпоративный чат, который хотите удалить:'


def confirmation_delete_customer_admin(fio):
    return f'ℹ️ Вы уверены, что хотите удалить представителя получателя услуг <b>{fio}</b>?'


def confirmation_delete_customer_group(
        group_name: str
) -> str:
    return f'ℹ️ Вы уверены, что хотите удалить корпоративную группу <b>{group_name}</b>?'


def confirmation_delete_customer_foreman(full_name):
    return f'ℹ️ Вы уверены, что хотите удалить представителя исполнителя <b>{full_name}</b>?'


def customer_admin_deleted():
    return '✅ Представитель получателя услуг был успешно удален'


def customer_group_deleted():
    return '✅ Корпоративный чат был успешно удален'


def customer_foreman_deleted():
    return '✅ Представитель исполнителя был успешно удален'


def delete_customer_admin_error():
    return '❗Не удалось удалить представителя получателя услуг'


def delete_customer_group_error():
    return '❗Не удалось удалить корпоративный чат'


def delete_customer_foreman_error():
    return '❗Не удалось удалить представителя исполнителя'


def admin_city_way_caption(
        description: str
) -> str:
    return f'<b>Информация:\n</b>' \
           f'<blockquote>{description}</blockquote>'


def no_customer_city_way() -> str:
    return f'❗У получателя услуг в этом городе еще нет способа добраться'


def customer_city_way() -> str:
    return f'ℹ️ Выберите действие:'


def confirmation_update_city_way() -> str:
    return f'ℹ️ Вы уверены, что хотите обновить способ добраться? Старый способ будет удален'


def worker_account_menu() -> str:
    return 'Выберите действие с аккаунтом исполнителя (НПД):'


def request_last_name() -> str:
    return '👤 Введите реальную фамилию исполнителя (НПД) <b>без ошибок</b>:'


def request_worker_phone_number() -> str:
    return '📞 Введите номер телефона исполнителя (НПД):'


def request_worker_tg_id() -> str:
    return '🆔 Введите Telegram ID исполнителя (НПД):'


def confirmation_delete_worker(
        full_name: str
) -> str:
    return f"Вы уверены, что хотите <b>безвозвратно</b> удалить исполнителя (НПД) " \
           f"<b>{full_name}</b>?"


def confirmation_erase_worker_tg_id(
        full_name: str
) -> str:
    return f"Вы уверены, что хотите стереть идентификаторы входа (Telegram ID, Max ID, веб-IP) " \
           f"исполнителя (НПД) <b>{full_name}</b>?"


def confirmation_erase_worker_rating(
        full_name: str,
        rating: str,
        total_orders: int,
        successful_orders: int
) -> str:
    return f"Текущий рейтинг исполнителя (НПД) <b>{full_name}</b>: " \
           f"{total_orders}/{successful_orders} — {rating}"


def request_new_total_orders() -> str:
    return f'Введите новое количество взятых заявок:'


def new_total_orders_error() -> str:
    return '❗️Новое количество взятых заявок должно быть не меньше старого. ' \
           'Введите еще раз:'


def confirmation_update_total_orders(
        full_name: str,
        rating: str
) -> str:
    return f'После ввода нового значения «взятых заявок» рейтинг исполнителя <b>{full_name}</b> изменится ' \
           f'и будет составлять {rating}. Вы согласны?'


def worker_deleted() -> str:
    return '✅ Исполнитель (НПД) был успешно удален'


def worker_erased() -> str:
    return '✅ Идентификаторы входа исполнителя (НПД) были успешно стёрты'


def worker_rating_updated() -> str:
    return '✅ Рейтинг исполнителя (НПД) был успешно обновлен'


def update_worker_rating_error() -> str:
    return '❗Не удалось обновить рейтинг исполнителя (НПД)'


def erase_worker_tg_id_error() -> str:
    return '❗Не удалось стереть идентификаторы входа исполнителя (НПД)'


def delete_worker_error() -> str:
    return '❗Не удалось удалить исполнителя (НПД)'


def request_start_date() -> str:
    return '📅 Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def request_end_date() -> str:
    return '📅 Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def date_error() -> str:
    return '❗Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def difference_is_more_than_36_days_error():
    return '❗Разница в конечной и начальной дате не должна превышать 36 дней. Введите дату еще раз:'


def end_date_lower_than_start_date_error() -> str:
    return '❗Конечная дата не должна быть больше начальной. Введите дату еще раз:'


def select_customer() -> str:
    return '👤 Выберите получателя услуг, с которым будет сформирована сверка:'


def collation_pdf() -> str:
    return f"⌛ Подождите немного. Сверка скоро будет сформирована"


def create_collation_error() -> str:
    return '❗Не удалось сформировать сверку'

def create_collation_error_no_orders() -> str:
    return '❗В выбранном диапазоне нет заявок для формирования сверки'

def show_saving(
        start_date: str,
        end_date: str,
        data: dict
) -> str:
    text = f'{start_date} - {end_date}\n\n'

    result_total_sum = Decimal('0')
    result_saving_sum = Decimal('0')
    result_saving = Decimal('0')

    for customer in data:
        text += f'{customer} | ' \
                f'{round(Decimal(data[customer]["total_sum"]), 2)} | ' \
                f'{round(Decimal(data[customer]["saving_sum"]), 2)} | ' \
                f'{round(Decimal(data[customer]["saving"]), 2)}\n'

        result_total_sum += Decimal(data[customer]["total_sum"])
        result_saving_sum += Decimal(data[customer]["saving_sum"])
        result_saving += Decimal(data[customer]["saving"])

    text += f'Итого | ' \
            f'{round(result_total_sum, 2)} | ' \
            f'{round(result_saving_sum, 2)} | ' \
            f'{round(result_saving, 2)}'
    return f'<blockquote>{text}</blockquote>'


def show_saving_error(
        start_date: str,
        end_date: str
) -> str:
    return f'❗В диапазоне с {start_date} по {end_date} ничего не найдено'


def request_choose_category() -> str:
    return 'ℹ️ Выберите категорию:'


def request_choose_action() -> str:
    return "ℹ️ Выберите действие:"


def request_new_rules(
        rules_for: str
) -> str:
    return f'Введите новые правила для ' \
           f'{"исполнителей" if rules_for == "workers" else "представителей исполнителя"}:'


def confirmation_update_rules(
        rules_for: str
) -> str:
    return f'Изменить правила для {"исполнителей" if rules_for == "workers" else "представителей исполнителя"}?'


def rules_updated(
    rules_for: str
) -> str:
    return f'✅ Правила для {"исполнителей" if rules_for == "workers" else "представителей исполнителя"} ' \
           f'успешно обновлены'


def update_rules_error(
    rules_for: str
) -> str:
    return f'❗Не удалось обновить правила для ' \
           f'{"исполнителей" if rules_for == "workers" else "представителей исполнителя"}'


def rules_notification_start() -> str:
    return 'ℹ️ Отправка уведомлений началась'


def rules_notification() -> str:
    return f'ℹ️ Правила платформы обновлены. Ознакомьтесь в разделе Обо мне → Правила'


def request_manual_pic() -> str:
    return 'ℹ️ Отправьте изображение с инструкцией как файл:'


def registration_pic_saved() -> str:
    return '✅ Изображение успешно обновлено'


def save_registration_pic_error() -> str:
    return '❗Не удалось обновить изображение'


def jobs_fp_menu() -> str:
    return '🛂 <b>Наименование услуг</b>\nВыберите действие:'


def jobs_fp_xlsx() -> str:
    return f"⌛ Подождите немного. xlsx-файл с услугами скоро будет сформирован"


def jobs_fp_xlsx_error() -> str:
    return '❗Невозможно сформировать xlsx-файл, так как нет еще ни одной услуги'


def request_jobs_fp_xlsx() -> str:
    return 'ℹ️ Отправьте xlsx-файл с услугами:'


def xlsx_file_error() -> str:
    return '❗Отправьте файл в формате .xlsx:'


def jobs_fp_updating() -> str:
    return 'ℹ️ Услуги обновляются'


def jobs_fp_updated() -> str:
    return ('✅ <b>Услуги успешно обновлены</b>\n'
            '<blockquote>⚠️ <b>Важно!</b>\n'
            '1. Когда снова будете обновлять услуги, старайтесь не менять их порядок в xlsx-файле. '
            'Если это сделать, у Исполнителя (НПД) в течение года может повториться одна и та же услуга\n'
            '2. Чтобы добавить новые услуги, обновите xlsx-файл, который отправляли ранее. '
            'Иначе, если вы отправите новый файл, старые услуги будут заменены на новые</blockquote>')


def update_jobs_fp_error() -> str:
    return '❗Не удалось обновить услуги'


def choose_worker_to_search() -> str:
    return f'Выберите нужного исполнителя (НПД):'


def platform_emails_menu() -> str:
    return ('📪 <b>Внутренние email адреса платформы</b>\n\n'
            'Здесь вы можете указать email адреса, на которые будут дублироваться '
            'все списки исполнителей (НПД), отправляемые получателями услуг.\n\n'
            'Формат ввода: адреса через точку с запятой\n'
            'Пример: finance@algoritm.plus; director@algoritm.plus')


def current_platform_emails(emails: Optional[str]) -> str:
    if emails:
        return f'<b>Текущие email адреса:</b>\n{emails}'
    return '<b>Email адреса не указаны</b>'


def enter_platform_emails() -> str:
    return ('ℹ️ Введите email адреса через точку с запятой (;)\n\n'
            'Пример:\nfinance@algoritm.plus; director@algoritm.plus')


def platform_emails_updated() -> str:
    return '✅ Email адреса успешно обновлены!'


def platform_emails_update_error() -> str:
    return '❌ Ошибка при обновлении email адресов'


def email_validation_error(message: str) -> str:
    return f'❌ Ошибка валидации:\n{message}'


def customer_email_management_info(
    organization: str,
    email_addresses: Optional[str],
    email_sending_enabled: bool
) -> str:
    emails_text = email_addresses if email_addresses else '<i>Не указаны</i>'
    status_text = '✅ Включена' if email_sending_enabled else '❌ Выключена'

    return (f'📪 <b>Управление email для получателя услуг</b>\n'
            f'<b>Организация:</b> {organization}\n\n'
            f'<b>Email адреса:</b>\n{emails_text}\n\n'
            f'<b>Отправка списков на почту:</b> {status_text}')


def enter_customer_emails() -> str:
    return ('ℹ️ <b>Введите email адреса получателя услуг</b>\n\n'
            'Формат: адреса через точку с запятой (;)\n\n'
            'Пример:\nsecurity@company.ru; manager@company.ru')


def customer_emails_saved() -> str:
    return '✅ Email адреса получателя услуг сохранены!'


def customer_email_sending_enabled() -> str:
    return '✅ Отправка списков на почту включена!'


def customer_email_sending_disabled() -> str:
    return '❌ Отправка списков на почту выключена!'


def customer_email_addresses_display(email_addresses: Optional[str]) -> str:
    if email_addresses:
        return f'📧 <b>Email адреса:</b>\n{email_addresses}'
    return '📧 <b>Email адреса не указаны</b>'


def admin_delete_worker_notification():
    """Уведомление исполнителю при удалении администратором"""
    return (
        "ℹ️ По данной Заявке обновлён список Исполнителей,"
        "поэтому ваше участие в Заявке отменено.\n"
        "Если нужна помощь — обратитесь в службу поддержки."
    )


# ========== Исполнители с дополнительным вознаграждением ==========

def premium_workers_menu():
    return (
        "<b>🎁 Бонусные исполнители</b>\n\n"
        "В этом разделе вы управляете исполнителями с дополнительным вознаграждением "
        "для данного Получателя услуг.\n\n"
        "<blockquote>➕ <b>Закрепить исполнителя</b> — назначить дополнительное вознаграждение "
        "конкретному исполнителю\n"
        "📋 <b>Список закреплённых</b> — просмотреть всех закреплённых исполнителей\n"
        "❌ <b>Открепить исполнителя</b> — отменить дополнительное вознаграждение</blockquote>\n\n"
        "⬇️ Используйте кнопки ниже"
    )


def enter_premium_worker_last_name():
    return "📝 Введите фамилию исполнителя для поиска:"


def premium_worker_not_found(last_name: str):
    return (
        f"❌ Исполнитель с фамилией '<b>{last_name}</b>' не найден в системе.\n\n"
        "Убедитесь, что исполнитель зарегистрирован на платформе."
    )


def select_premium_worker():
    return "👥 Найдены следующие исполнители. Выберите нужного:"


def select_bonus_type(last_name: str, first_name: str, middle_name: str):
    return (
        f"👤 <b>{last_name} {first_name} {middle_name}</b>\n\n"
        "💰 Выберите тип дополнительного вознаграждения:\n\n"
        "<blockquote><b>Безусловное вознаграждение</b> — фиксированная сумма за каждую закрытую Заявку, "
        "независимо от процента исполнения\n\n"
        "<b>Условное вознаграждение</b> — сумма зависит от процента исполнения Заявки "
        "(можно задать до 4 условий)</blockquote>"
    )


def enter_unconditional_bonus_amount():
    return (
        "💰 Введите фиксированную сумму безусловного вознаграждения (в рублях):\n\n"
        "Пример: 500 или 500,00"
    )


def enter_condition_percent(condition_num: int):
    return (
        f"📊 <b>Условие {condition_num}</b>\n\n"
        "Введите минимальный процент исполнения Заявки для получения вознаграждения:\n\n"
        "Примеры: 95 или 95,50"
    )


def enter_condition_amount(condition_num: int):
    return (
        f"💰 <b>Условие {condition_num}</b>\n\n"
        "Введите сумму вознаграждения при достижении этого порога (в рублях):\n\n"
        "Пример: 300 или 300,00"
    )


def add_more_conditions():
    return (
        "✅ Условие добавлено.\n\n"
        "Хотите добавить ещё одно условие или завершить настройку?"
    )


def confirm_premium_worker(
    last_name: str,
    first_name: str,
    middle_name: str,
    bonus_type: str,
    amount: str = None,
    conditions: list = None
):
    text = f"👤 <b>{last_name} {first_name} {middle_name}</b>\n\n"

    if bonus_type == 'unconditional':
        text += (
            f"💰 <b>Безусловное вознаграждение:</b> {amount} ₽\n\n"
            "Исполнитель будет получать эту сумму за каждую закрытую Заявку."
        )
    else:
        text += "📊 <b>Условное вознаграждение:</b>\n\n"
        sorted_conditions = sorted(
            conditions,
            key=lambda x: float(x['percent'].replace(',', '.'))
        )
        for i, cond in enumerate(sorted_conditions, 1):
            text += f"{i}. При исполнении ≥ {cond['percent']}% → вознаграждение {cond['amount']} ₽\n"
        text += "\nИсполнитель получит вознаграждение за максимальный достигнутый порог."

    text += "\n\n✅ Закрепить исполнителя?"
    return text


def invalid_amount_format():
    return (
        "❌ Неверный формат суммы. Введите число (можно с десятичной частью через точку или запятую):\n\n"
        "Примеры: 500, 500.50, 500,50"
    )


def invalid_percent_format():
    return (
        "❌ Неверный формат процента. Введите число от 0 до 100 (можно с десятичной частью):\n\n"
        "Примеры: 95, 95.5, 95,50"
    )


def premium_worker_added():
    return "✅ Исполнитель успешно закреплён!"


def premium_worker_add_error():
    return "❌ Ошибка при закреплении исполнителя. Попробуйте снова."


def no_premium_workers():
    return (
        "📋 Список закреплённых исполнителей пуст.\n\n"
        "Закрепите исполнителей через меню."
    )


def premium_workers_list():
    return (
        "📋 <b>Закреплённые исполнители</b>\n\n"
        "💰 — Безусловное вознаграждение\n"
        "📊 — Условное вознаграждение\n\n"
        "Нажмите на исполнителя для просмотра деталей:"
    )


def select_premium_worker_to_delete():
    return "❌ Выберите исполнителя для открепления:"


def confirm_delete_premium_worker():
    return (
        "⚠️ Вы уверены, что хотите открепить этого исполнителя?\n\n"
        "Все настройки дополнительного вознаграждения будут удалены."
    )


def premium_worker_deleted():
    return "✅ Исполнитель откреплён."


def premium_worker_delete_error():
    return "❌ Ошибка при открeплении исполнителя."


def set_travel_compensation_request():
    return (
        "🚌 <b>Компенсация Платформы за проезд</b>\n\n"
        "Введите сумму компенсации (в рублях), которая будет начисляться исполнителям "
        "со статусом 🟡 «Лишний».\n\n"
        "Эта сумма будет применяться только к тем исполнителям, которые прибыли на объект, "
        "но оказались сверх лимита заявки.\n\n"
        "Пример: 200"
    )


def travel_compensation_error():
    return "❌ Ошибка: введите положительное целое число."


def travel_compensation_saved(amount: int):
    return f"✅ Сумма компенсации установлена: {amount} ₽"


def help_command_warning() -> str:
    return "ℹ️ Используйте эту команду в группе"


def help_group_set() -> str:
    return "✅ Группа для обратной связи успешно обновлена"


def set_help_group_error() -> str:
    return "❗Не удалось обновить группу для обратной связи"
