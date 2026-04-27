from aiogram import html
from typing import Optional

import database as db


def start_manager():
    return ("👋 <b>Добро пожаловать в панель менеджера!</b>\n\n"
            "Управление заявками, исполнителями и коммуникациями.\n\n"
            "<blockquote>🧾 <b>Модерация заявок</b>\n"
            "Создание, ведение, допуск, перевод, отклики.\n\n"
            "👉 <b>Уведомление</b>\n"
            "Выбор города и массовая рассылка.\n\n"
            "📁 <b>Архив</b>\n"
            "Просмотр закрытых и возврат заявок.\n\n"
            "📞 <b>Прозвоны</b>\n"
            "Фиксация контакта и результата связи.\n\n"
            "📋 <b>Архив прозвонов</b>\n"
            "История и анализ коммуникаций.\n\n"
            "🔎 <b>СМЗ</b>\n"
            "Поиск, локация, телефон исполнителя.\n\n"
            "🚶 <b>СМЗ</b>\n"
            "Ручное добавление самозанятого без ссылки.</blockquote>"
    )


def orders_moderation():
    return "ℹ️ <b>Заявки рассортированы по статусу:</b>\n" \
           "🔴 МОДЕРАЦИЯ 🔴\n" \
           "🟢 ПОДБОР ИСПОЛНИТЕЛЕЙ 🟢\n" \
           "🟡 ОКАЗАНИЕ УСЛУГ 🟡"


def applications_moderation():
    return "🔧 Нажмите на исполнителя, чтоб увидеть больше информации о его отклике.\n\n" \
           "Исполнитель | Рейтинг"


async def application_info(application_id):
    application = await db.get_application(application_id=int(application_id))
    order = await db.get_order(order_id=application.order_id)
    worker = await db.get_user_real_data_by_id(user_id=application.worker_id)

    organization = await db.get_customer_organization(customer_id=order.customer_id)
    time = order.day_shift if order.day_shift else order.night_shift

    return f"Отклик от {worker.last_name} {worker.first_name} {worker.middle_name}\n" \
           f"<blockquote><b>📍 Город:</b> {order.city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>💼 Услуга:</b> {order.job_name}\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"<b>💵 Оплата:</b> {order.amount}₽</blockquote>\n\n" \
           "Выберите действие для этого отклика:"


def application_error():
    return "❗Не удалось выполнить действие. Заявка была удалена пользователем"


def approve_application():
    return "Вы уверены, что хотите одобрить заявку?"


def application_approved():
    return "✅ Заявка была успешно одобрена!"


def application_rejected():
    return "❎ Заявка была успешно отклонена!"


def new_order_notification():
    return "Появилась новая заявка! Установите для нее вознаграждение. Для этого перейдите в раздел\n\"Модерация заявок\""


def reject_application():
    return "Вы уверены, что хотите отклонить заявку?"


def no_orders_moderation():
    return "<b>🔧 Модерация заявок</b>\n" \
           "В данный момент заявок на модерацию нет"


def no_applications_moderation():
    return "🔧 Заявок на модерацию к этой заявке нет"


def no_orders_with_applications():
    return "🔧 В данный момент заявок с подбором исполнителей нет"


def no_orders_in_progress():
    return "🔧 В данный момент заявок с подбором исполнителей нет"


def add_order_amount():
    return "💵 Введите оплату для исполнителей (НПД) за единицу:"


def add_order_amount_in_button():
    return "ℹ️ Оставляем вознаграждение платформы?"


def accept_amount(amount, job, date, day_shift, night_shift, workers):
    time = day_shift if day_shift else night_shift
    return f"Сохранить вознаграждение в размере {amount}₽ для заявки?\n\n" \
           f'🛂 Услуга: <b>{job}</b>\n' \
           f'🗓️ Время: {date} | {time}\n' \
           f'👥 Требуется исполнителей (НПД): {workers}'


def order_moderation(organization, job, date, day_shift, night_shift, workers):
    time = day_shift if day_shift else night_shift
    return f'<b>🔴 МОДЕРАЦИЯ 🔴</b>\n' \
           f'<blockquote>👤 Получатель услуг: <b>{organization}</b>\n' \
           f'🛂 Услуга: <b>{job}</b>\n' \
           f'🗓️ Время: {date} | {time}\n' \
           f'👥 Требуется исполнителей (НПД): {workers}</blockquote>'


def amount_added():
    return "✅ Оплата была успешно добавлена!\n" \
           "Заявка опубликована"


def amount_error():
    return "❗Не удалось сохранить оплату. Попробуйте еще раз"


def ref_notification(last_name, first_name, middle_name, amount):
    return f"Один из рефералов исполнителя <b>{last_name} {first_name} {middle_name}</b> выполнил условия. " \
           f"Начислите исполнителю (НПД) бонус в размере {amount}₽"


def rejection_notification(last_name, first_name, middle_name):
    return f"❗️Исполнитель (НПД) <b>{last_name} {first_name} {middle_name}</b> отказался от оказания услуг по ранее подтверждённой Заявке.\n\n" \
       f"Вопрос о применении <b>договорной неустойки</b> (до 3 000 ₽) рассматривается в порядке и на условиях, предусмотренных договором, " \
       f"в том числе посредством <b>зачёта встречных однородных требований</b> (ст. 330, 410 ГК РФ) при наличии оснований."


def order_applications_info():
    return f"<b>🟢 ПОДБОР ИСПОЛНИТЕЛЕЙ 🟢</b>\n" \
           "Получатель услуг | Когда | Одобрено | Заявка | Откликов"


def orders_in_progress_info():
    return f"<b>🟡 ОКАЗАНИЕ УСЛУГ 🟡</b>\n" \
           "Получатель услуг | Когда | Исполнителей"


async def moderation_order_info(
        city, customer_id, job, date, day_shift, night_shift, amount, workers_count, order_workers, applications_count):
    time = day_shift if day_shift else night_shift
    organization = await db.get_customer_organization(customer_id)
    return f"<b>🟢 ПОДБОР ИСПОЛНИТЕЛЕЙ 🟢</b>\n" \
           f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>💼 Услуга:</b> {job}\n" \
           f"<b>🗓️ Дата:</b> {date}\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"<b>💵 Оплата:</b> {amount}₽</blockquote>\n" \
           f"<b>Исполнителей:</b> {workers_count} из {order_workers}\n" \
           f"<b>Откликов:</b> {applications_count}\n"


async def order_in_progress_info(
        city, customer_id, job, date, day_shift, night_shift, amount, workers_count, order_workers):
    time = day_shift if day_shift else night_shift
    organization = await db.get_customer_organization(customer_id)
    return f"<b>🟡 ОКАЗАНИЕ УСЛУГ 🟡</b>\n" \
           f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>💼 Услуга:</b> {job}\n" \
           f"<b>🗓️ Дата:</b> {date}\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"<b>💵 Оплата:</b> {amount}₽</blockquote>\n" \
           f"<b>Набрано исполнителей:</b> {workers_count} из {order_workers}\n"


async def notification_by_order(
        order_id, customer_id, date, day_shift, night_shift, workers_count
):
    time = day_shift if day_shift else night_shift
    organization = await db.get_customer_organization(customer_id)
    return f"ℹ️ Заявка №{order_id} набрала необходимое количество откликов от исполнителей ({workers_count})\n" \
           f"<blockquote><b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>🗓️ Дата:</b> {date}\n" \
           f"<b>🕒 Время:</b> {time}</blockquote>"


def workers_none_pdf():
    return "❗Чтобы сформировать PDF, должен быть хотя бы 1 одобренный исполнитель"


def workers_none_registration():
    return "❗Чтобы завершить регистрацию и отправить получателю услуг PDF, должен быть хотя бы 1 одобренный исполнитель"


def accept_complete_registration_order():
    return "Вы уверены, что хотите завершить прием заявок от исполнителей и отправить PDF с исполнителями получателю услуг?"


def registration_completed():
    return "✅ Прием заявок закрыт. Получателю услуг был отправлен PDF с исполнителями"


def registration_complete_error():
    return "❗Не удалось завершить регистрацию"


def accept_newsletter():
    return "Вы точно хотите сделать уведомление?"


def newsletter_city():
    return "🌆 Выберите город для уведомления:"


def newsletter_text(city):
    return f"✉️ Теперь отправьте сообщение для уведомления по городу «{city}»"


def newsletter_started():
    return "✅ Отправка уведомлений началась"


def newsletter_finished():
    return "✅ Отправка уведомлений завершилась"


def order_workers_info():
    return '👥 Список с одобренными исполнителями открыт. ' \
           'Здесь вы можете удалять исполнителей, для этого нажмите на нужного.\n\n' \
           'Исполнитель | Рейтинг'


def order_workers_none():
    return "ℹ️ Вы ещё не одобрили ни одного исполнителя"


def worker_info(full_name):
    return f"👤 Исполнитель (НПД) {html.bold(full_name)}"


def accept_delete_worker():
    return 'Вы уверены, что хотите удалить этого исполнителя?'


def order_worker_deleted():
    return '✅ Исполнитель был успешно удален'


def delete_worker_canceled():
    return 'ℹ️ Удаление исполнителя отменено'


def delete_order_worker_error():
    return '❗Не удалось удалить исполнителя. Возможно его уже удалил другой менеджер'


def delete_worker_notification():
    return f'❗Вы были удалены представителем исполнителя на участке, ' \
           f'попробуйте взять другую заявку'


def no_archive_orders(
        date: str
) -> str:
    return f'ℹ️ Заявки за <b>{date}</b> не найдены'


def archive_orders_info():
    return "ℹ️ В этом разделе вы можете посмотреть заявки в архиве и вернуть их на этап «Подбор исполнителей», " \
           "изменив количество исполнителей. Для этого нажмите на заявку.\n\n" \
           "Получатель услуг | дата | Д/Н | вышло людей / заявка"


def open_archive_order(
        order_id: int,
        city: str,
        organization: str,
        date: str,
        job: str,
        day_shift: Optional[str],
        night_shift: Optional[str],
        amount: str,
        real_workers_count: int,
        workers_count: int
) -> str:
    time = day_shift if day_shift else night_shift
    return f'<blockquote><b>Заявка №{order_id}</b>\n' \
           f'<b>📍 Город:</b> {city}\n' \
           f'<b>👥 Получатель услуг:</b> {organization}\n' \
           f'<b>📦 Услуга:</b> {job}\n' \
           f'<b>📅 Дата:</b> {date}\n' \
           f'<b>⏰ Период оказания услуг:</b> {time}\n' \
           f'<b>💰 Вознаграждение:</b> {amount}₽\n' \
           f'<b>👥 Исполнителей:</b> {real_workers_count} из {workers_count}\n</blockquote>'


def confirmation_update_archive_order_workers_count() -> str:
    return "Вы уверены что хотите обновить <b>требуемое количество исполнителей</b>?\n\n" \
           "ℹ️ Если вы обновите этот параметр, заявка вернется на этап «Подбор исполнителей». " \
           "Также этой заявке будет присвоен новый номер"


def archive_order_workers_updated() -> str:
    return '✅ Статус (Подбор исполнителей) и количество исполнителей для этой заявки успешно обновлены'


def manager_delete_order_worker_notification(
        worker_full_name: str,
        city: str,
        customer: str,
        job_name: str,
        date: str,
        day_shift: str,
        night_shift: str
) -> str:
    time = day_shift if day_shift else night_shift
    return '⚠️ <b>Поздний отказ</b>\n\n' \
           f'Исполнитель: {worker_full_name}\n\n' \
           'Отказ от Заявки менее чем за 12 часов до начала периода оказания услуг.\n\n' \
           'Обязательство по Заявке прекращено.\n\n' \
           'Заявка возвращена в поиск исполнителей.\n\n' \
           'Основание: договор + Правила Платформы + ст. 309, 310, 330, 393 ГК РФ'


def cancelled_order_card(
        city: str,
        customer: str,
        job_name: str,
        date: str,
        day_shift: str,
        night_shift: str,
) -> str:
    time = day_shift if day_shift else night_shift
    return (
        '<b>📌 Отменённая заявка</b>\n'
        f'<blockquote><b>📍 Город:</b> {city}\n'
        f'<b>👥 Получатель услуг:</b> {customer}\n'
        f'<b>💼 Услуга:</b> {job_name}\n'
        f'<b>📅 Дата и время:</b> {date} | {time}</blockquote>'
    )


def request_worker_last_name() -> str:
    return f'Введите реальную фамилию исполнителя:'


def choose_worker() -> str:
    return f'Выберите исполнителя, которого хотите добавить:'


def confirmation_add_to_order_workers(
        worker_full_name: str
) -> str:
    return f'Добавить исполнителя <b>{worker_full_name}</b> в заявку?'


def worker_added_to_order_workers() -> str:
    return f'✅ Исполнитель успешно добавлен'


def add_worker_to_order_workers_error() -> str:
    return f'❗Не удалось добавить исполнителя'


def request_to_change_city_for_manager(
        worker_full_name: str,
        old_city: str,
        new_city: str
) -> str:
    return f"<b>👤 {worker_full_name}</b> пытается изменить локацию:\n" \
           f"📍 {old_city} → 📍 {new_city}\n\n" \
           f"Разрешить смену локации?"


def city_for_worker_updated() -> str:
    return f'✅ Город успешно обновлен'


def request_was_handle_another_manager() -> str:
    return 'ℹ️ Этот запрос на смену локации уже был обработан другим менеджером'


def update_city_for_worker_error() -> str:
    return f'❗Не удалось обновить город'


def update_city_canceled() -> str:
    return '✅ Смена локации для исполнителя отменена'


def request_archive_date() -> str:
    return '🗓️ Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


def archive_date_error() -> str:
    return '❗Неверный формат даты. Введите дату в формате ДД.ММ или ДД.ММ.ГГ или ДД.ММ.ГГГГ:'


# ─── Прозвоны ────────────────────────────────────────────────────────────────

def call_campaigns_today(date: str) -> str:
    return f'<b>📞 Прозвоны — {date}</b>\n\nВыберите заявку:'


def no_call_campaigns_today(date: str) -> str:
    return f'📞 Прозвонов за {date} не найдено.'


def call_campaigns_archive(date: str) -> str:
    return f'<b>📋 Архив прозвонов — {date}</b>\n\nВыберите заявку:'


def no_call_campaigns_archive(date: str) -> str:
    return f'📋 Прозвонов за {date} не найдено.'


def request_call_archive_date() -> str:
    return '📋 Введите дату для просмотра архива прозвонов (ДД.ММ или ДД.ММ.ГГГГ):'


def call_campaign_workers_list() -> str:
    return '<b>📞 Исполнители по заявке</b>\n\n' \
           '⏳ <b>ждем</b> информацию от Партнера\n' \
           '🟢 <b>подтвердил</b>\n' \
           '🟡 <b>не отвечает после 2 звонков</b>\n' \
           '🔴 <b>отказался выходить</b>\n' \
           '🔵 <b>телефон не доступен / автоответчик</b>\n\n' \
           'Нажмите на исполнителя для просмотра телефонов:'


def call_worker_info(
    full_name: str,
    status_emoji: str,
    phone_tg: str,
    phone_real: str,
    call_phone: str
) -> str:
    def phone_link(phone: str) -> str:
        if not phone or phone == '—':
            return '—'
        normalized = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
        if not normalized:
            return phone
        return f'<a href="tel:{normalized}">{phone}</a>'

    return (
        f'<b>{full_name}</b> {status_emoji}\n\n'
        f'📱 Телефон (Telegram): {phone_link(phone_tg)}\n'
        f'📱 Телефон (реальный): {phone_link(phone_real)}\n'
        f'📞 Использован для прозвона: {phone_link(call_phone)}'
    )
