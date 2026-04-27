from decimal import Decimal


def start_customer():
    return "<b>👋 Добро пожаловать в панель управления получателя услуг!</b>\n\n" \
           "У вас есть доступ к следующим функциям:\n\n" \
           "<b>⚙️ Управление заявками</b>\n" \
           "• Просмотр ваших заявок\n" \
           "• Создание новых заявок\n" \
           "• Изменение количества исполнителей, удаление уже размещенных заявок\n" \
           "• Завершение заявок, распределение единиц на каждого исполнителя и получение " \
           "финального PDF-отчёта\n\n" \
           "Используйте кнопки ниже для навигации ⬇️"


def orders():
    return "<b>📋 Управление заявками</b>\n" \
           "Выберите действие:"


def add_order_job():
    return "🛂 Выберите услугу:"


def add_order_date_button():
    return "🗓️ Выберите дату:"


def add_order_date():
    return "🗓️ Введите дату в формате ДД.ММ.ГГГГ\n" \
           "Например: 19.03.2025"


def add_order_shift():
    return "⌛ Период оказания услуг:"


def add_order_workers():
    return "👥 Введите лимит откликов по заявке:"


def accept_new_order(job, date, shift, workers, city):
    return "<b>Создать заявку со следующими данными?</b>\n" \
           f"🛂 <b>Услуга:</b> {job}\n" \
           f"🌆 <b>Город:</b> {city}\n" \
           f"🗓️ <b>Дата:</b> {date}\n" \
           f"⌛ <b>Период оказания услуг:</b> {shift}\n" \
           f"👥 <b>Лимит откликов по заявке:</b> {workers}"


def show_customer_order(
        order_id, job, date, day_shift, night_shift, workers, city, moderation, in_progress, workers_count,
        applications_count):
    shift = day_shift if day_shift else night_shift

    if moderation:
        status = 'На модерации'
    elif in_progress:
        status = 'Оказание услуг'
    else:
        status = 'Подбор исполнителей'

    return f"<b>Заявка №{order_id}</b>\n" \
           f"<blockquote><b>ℹ️ Статус:</b> {status}\n" \
           f"<b>🛂 Услуга:</b> {job}\n" \
           f"<b>🌆 Город:</b> {city}\n" \
           f"<b>🗓️ Дата:</b> {date}\n" \
           f"<b>⌛ Время:</b> {shift}\n" \
           f"<b>👥 Требуется исполнителей:</b> {workers}\n" \
           f"<b>👥 Утвержденных исполнителей: {workers_count}</b>\n" \
           f"<b>👥 Откликнувшихся исполнителей: {applications_count}</b></blockquote>"


def accept_delete_order():
    return "Вы уверены, что хотите удалить заявку?"


def confirmation_order_finish():
    return f"Вы уверены, что хотите закрыть заявку?"


def confirmation_common_hours() -> str:
    return f"Проставить всем одинаковое количество единиц?"


def request_common_hours() -> str:
    return f'Введите количество единиц, которое будет выставлено всем исполнителям:'


def confirmation_set_hours(
        order_workers: dict,
        workers_hours: dict
) -> str:
    text = 'Вы верно выставили единицы всем исполнителям?\n'
    workers_text = ''
    all_hours = 0
    all_workers = 0
    for key in order_workers:
        hours = workers_hours.get(key, '0')
        workers_text += f"{order_workers[key]['last_name']} " \
                        f"{order_workers[key]['first_name']} " \
                        f"{order_workers[key]['middle_name']}: {hours}\n"

        # Подсчёт только для WORKED (не Л и не 0)
        if hours != 'Л' and hours != '0':
            try:
                all_hours = Decimal(all_hours) + Decimal(hours)
                all_workers += 1
            except:
                pass
        elif hours == 'Л':
            # Лишний исполнитель не считается в общее количество
            pass

    text += (
     f'<blockquote>'
     f'{f"{workers_text[:4095 - (len(text) + 28):]}..." if len(text) + len(workers_text) + 25 > 4095 else workers_text}'
     f'</blockquote>'
    )
    text += f'Итого: {all_workers} человек; {all_hours} единиц'
    return text


def confirmation_set_common_hours(
        order_workers_count: int,
        common_hours: str
) -> str:
    return f'В этот период оказания услуг было {order_workers_count} человек. ' \
           f'Вы всем ставите по {common_hours} единиц, ' \
           f'общее количество единиц: ' \
           f'{Decimal(order_workers_count) * Decimal(common_hours.replace(",", "."))}. Верно?'


def delete_order_error():
    return "❗Не удалось удалить вашу заявку"


def order_deleted():
    return "✅ Заявка была успешно удалена"


def manager_deleted_order(order_id):
    return f"❗Вашу заявку №{order_id} удалил менеджер"


def customer_deleted_order(fio, order_id):
    return f"❗{fio} удалил заявку №{order_id}"


def notification_for_workers():
    return "❗Получатель услуг удалил заявку. Ваш отклик был удален, теперь вы можете взять новую заявку!"


def order_pdf():
    return f"⌛ Подождите немного. PDF-файл с исполнителями скоро будет сформирован"


def order_pdf_info():
    return f"✅ PDF-файл с исполнителями сформирован"


def worker_hours(last_name, first_name, middle_name):
    return f"⌛ Введите количество выполненных единиц для <b>{last_name} {first_name} {middle_name}</b>:"


def no_orders_customer():
    return "У вас нет еще ни одной заявки!"


def order_end(order_id):
    return f"✅ Вы выставили единицы всем исполнителям. Заявка №{order_id} закрыта!"


def order_added():
    return "✅ Заявка была успешно добавлена!"


def order_cities():
    return "🌆 Выберите город:"


def order_error():
    return "❗Не удалось сохранить заявку. Попробуйте еще раз"


def pdf_order_start_shift(order_id, date, day_shift, night_shift):
    time = day_shift if day_shift else night_shift
    return f"ℹ️ Набор исполнителей для вашей заявки №{order_id} закрыт.\n" \
           f"⌛ Ждите их {date} в {time.split('-')[0]}\n" \
           f"Управлять заявкой вы можете в:\nУправление заявками -> Ваши заявки"


def pdf_order_end_shift(order_id):
    return f"ℹ️ Заявка №{order_id} была закрыта."


def send_order_photo_start_shift(
        date: str,
        shift: str
) -> str:
    return f'📋 Список исполнителей (НПД), добровольно взявших заявку на {date} ({shift}): ' \
           'Ожидайте людей по данному списку.'


def validate_number_error():
    return ("⚠️ <b>Ошибка ввода</b>\n\n"
            "Допустимые значения — от 0,5 до 22 с шагом 0,5.\n"
            "Пример: 0.5, 1, 1.5, 2, …, 21.5, 22.\n\n"
            "👉 Если исполнитель взял заказ, но не вышел (вы его не видели) —\n"
            "нажмите 🔴 «Не вышел» выше.\n"
            "К нему будут применены санкции и снижен рейтинг.\n\n"
            "👉 Если исполнитель дошёл до вашей проходной, но оказался лишним —\n"
            "нажмите 🟡 «Лишний» выше.\n"
            "Исполнителю будет начислена компенсация и повышен рейтинг.")


def order_notification_before_the_end(
        order_id: int,
        order_status: str,
        order_job: str,
        order_city: str,
        order_date: str,
        order_time: str
) -> str:
    return f'⏳ Уважаемые коллеги!\n\n' \
           f'На вашем участке сейчас оказывают услуги наши исполнители (НПД). ' \
           f'Пожалуйста, не забудьте закрыть заявку в вашей панели ✅\n\n' \
           f'<b>Заявка №{order_id}</b>\n' \
           f'<blockquote>ℹ️ Статус: {order_status}\n' \
           f'📦 Услуга: {order_job}\n' \
           f'🏙 Город: {order_city}\n' \
           f'📅 Дата: {order_date}\n' \
           f'⏳ Время: {order_time}</blockquote>'


def order_notification_after_the_end(
        order_id: int,
        order_status: str,
        order_job: str,
        order_city: str,
        order_date: str,
        order_time: str
) -> str:
    return f'❗️❗️❗️ ВАЖНО ❗️❗️❗️\n\n' \
           f'⏳ Время выполнения Заявки истекло, но она до сих пор не закрыта!\n\n' \
           f'💸 Наши исполнители (НПД) не могут получить оплату за оказанные услуги ' \
           f'до тех пор, пока вы не закроете заявку в своей панели.\n\n' \
           f'🚨 Пожалуйста, немедленно закройте заявку, ' \
           f'чтобы мы могли произвести выплаты исполнителям!\n\n' \
           f'<b>Заявка №{order_id}</b>\n' \
           f'<blockquote>ℹ️ Статус: {order_status}\n' \
           f'📦 Услуга: {order_job}\n' \
           f'🏙 Город: {order_city}\n' \
           f'📅 Дата: {order_date}\n' \
           f'⏳ Время: {order_time}</blockquote>'


def request_self_collation_start_date() -> str:
    return '🗓️ Введите дату начала периода (ДД.ММ / ДД.ММ.ГГ / ДД.ММ.ГГГГ):'


def request_self_collation_end_date() -> str:
    return '🗓️ Введите дату окончания периода (ДД.ММ / ДД.ММ.ГГ / ДД.ММ.ГГГГ):'


def self_collation_end_date_lower_than_start_date_error() -> str:
    return '⚠️ Дата окончания не может быть раньше даты начала. Введите корректные даты:'


def self_collation_date_error() -> str:
    return '⚠️ Некорректный формат даты. Используйте ДД.ММ, ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def difference_is_more_than_31_days_error() -> str:
    return '⚠️ Период самосверки не может превышать 31 день. Введите корректные даты:'


def self_collation_wait() -> str:
    return '⏳ Формируем сверку… Пожалуйста, подождите'
