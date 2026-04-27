from decimal import Decimal

from Schemas import WorkerChangeAmountSchema
from database import WalletPayment


def start_accountant() -> str:
    return "<b>👋 Добро пожаловать в панель управления кассира!</b>\n" \
           "ℹ️ В данном разделе формируются и отображаются документы по перечислению вознаграждений Исполнителям за оказанные услуги\n\n" \
           "Используйте кнопки ниже для навигации ⬇️"


def no_payments() -> str:
    return 'ℹ️ Ничего не найдено'


def payment_orders_info():
    return "Исполнитель (НПД) | Вознаграждение"


def wallet_payments_info():
    return "Получатель услуг | Дата | Д/Н"


def show_payment(
        workers: list[dict],
        total_amount: str,
) -> str:
    main = 'ФИО | Сумма\n'
    text = ''

    for worker in workers:
        text += f"{worker['full_name']} | {worker['amount']}₽\n"

    return f'<b>{main}</b><blockquote>{text}</blockquote><b>ИТОГО: {total_amount}₽</b>'


def no_suitable_org() -> str:
    return '❗️Оплата невозможна, так как баланс у всех юрлиц менее суммы ПП'


def choose_ip_for_payment() -> str:
    return 'ℹ️ Выберите юрлицо, с помощью которого хотите сделать отправку вознаграждения:'


def confirmation_create_payment(
        workers: list[dict],
        total_amount: Decimal,
        org_name: str,
) -> str:
    main = 'ФИО | Сумма\n'
    text = ''

    for worker in workers:
        text += f"{worker['full_name']} | {worker['amount']}₽\n"

    return (f'<b>{main}</b>'
            f'<blockquote>{text}</blockquote>'
            f'<b>ИТОГО: {total_amount}₽\n'
            f'{org_name}</b>\n\n'
            f'Подтвердить отправку вознаграждения?')


def confirmation_create_wallet_payment(
        wallet_payment: WalletPayment,
        org_name: str,
) -> str:
    return (f'<blockquote>{wallet_payment.worker.last_name} '
            f'{wallet_payment.worker.first_name} '
            f'{wallet_payment.worker.middle_name} | {wallet_payment.amount}₽\n'
            f'<b>{org_name}</b></blockquote>\n\n'
            f'<b>Подтвердить отправку вознаграждения?</b>')


def create_payment_canceled() -> str:
    return 'ℹ️ Отправка вознаграждения была отменена'


def no_jobs_fp_error() -> str:
    return ("❗️Невозможно отправить вознаграждение, так как отсутствуют услуги для вознаграждений. "
            "Сообщите об этом администратору")


def payment_created(
        payment_name: str,
) -> str:
    return f'✅ Вознаграждение {payment_name} создано. Всем кассирам будут приходить уведомления о его статусе'


def wallet_payment_created(
        wp_id: int,
) -> str:
    return f'✅ Вознаграждение из начислений №{wp_id} создано. Вам будут приходить уведомления о его статусе'


def api_registry_created(
        payment_name: str,
        registry_id_in_db: int | None = None,
        is_wallet_payment: bool = False,
) -> str:
    name = f'из начислений №{registry_id_in_db}' if is_wallet_payment else payment_name
    return f'ℹ️ Вознаграждение {name}. Создан платежный реестр'


def create_payment_error() -> str:
    return '❗️Не удалось создать вознаграждение'


def create_registry_api_error(
        payment_name: str,
        registry_id_in_db: int | None = None,
        is_wallet_payment: bool = False,
) -> str:
    name = f'из начислений №{registry_id_in_db}' if is_wallet_payment else payment_name
    return f'❗Вознаграждение {name}. Не удалось создать платежный реестр'


def create_registry_no_workers_error(
        payment_name: str,
) -> str:
    return f'❗Вознаграждение {payment_name}. Не удалось создать платежный реестр [Отсутствуют исполнители]'


def workers_skipped_no_card(payment_name: str, skipped: list[dict]) -> str:
    lines = '\n'.join(
        f'• {w["full_name"]} (ИНН {w["inn"]}) — {w["amount"]} руб.'
        for w in skipped
    )
    return (
        f'⚠️ <b>Выплата не отправлена</b>\n\n'
        f'<b>Получатель услуг:</b> {payment_name}\n'
        f'<b>Причина:</b> отсутствие карты\n\n'
        f'<b>Исполнители:</b>\n{lines}\n\n'
        f'💰 Средства переведены в «Начисления»\n'
        f'Остальной реестр отправлен в «Рабочие руки»\n'
        f'Исполнителям направлено уведомление на обновление карты'
    )


def payment_order_card(
        city: str,
        customer: str,
        job_name: str,
        date: str,
        day_shift: str,
        night_shift: str,
) -> str:
    time = day_shift if day_shift else night_shift
    return (
        '<b>📌 Карточка заявки</b>\n'
        f'<blockquote><b>📍 Город:</b> {city}\n'
        f'<b>👥 Получатель услуг:</b> {customer}\n'
        f'<b>💼 Услуга:</b> {job_name}\n'
        f'<b>📅 Дата и время:</b> {date} | {time}</blockquote>'
    )


def workers_skipped_conflict(payment_name: str, skipped: list[dict]) -> str:
    reason_map = {
        'card_number_mismatch': 'номер карты не совпадает',
    }
    lines = '\n'.join(
        (
            f'• {w["full_name"]} (ИНН {w["inn"]}) — {w["amount"]} руб.\n'
            f'  Платформа: {w.get("platform_method", {}).get("card", "empty")} | '
            f'РР: {w.get("rr_method", {}).get("card", "empty")} | '
            f'Конфликт: {reason_map.get(w.get("conflict_type"), "данные не совпадают")}'
        )
        for w in skipped
    )
    return (
        f'⚠️ <b>Выплата не отправлена</b>\n\n'
        f'<b>Получатель услуг:</b> {payment_name}\n'
        f'<b>Причина:</b> конфликт данных\n\n'
        f'<b>Исполнители:</b>\n{lines}\n\n'
        f'💰 Средства переведены в «Начисления»\n'
        f'Остальной реестр отправлен в «Рабочие руки»\n'
        f'Исполнителям направлено уведомление на обновление данных'
    )


def workers_skipped_rr_unavailable(payment_name: str, skipped: list[dict]) -> str:
    lines = '\n'.join(
        f'• {w["full_name"]} (ИНН {w["inn"]}) — {w["amount"]} руб.'
        for w in skipped
    )
    return (
        f'⚠️ <b>Выплата не отправлена</b>\n\n'
        f'<b>Получатель услуг:</b> {payment_name}\n'
        f'<b>Причина:</b> не удалось получить платёжные данные из РР\n\n'
        f'<b>Исполнители:</b>\n{lines}\n\n'
        f'💰 Средства переведены в «Начисления»\n'
        f'Остальной реестр отправлен в «Рабочие руки»\n'
        f'Исполнителям направлено уведомление о временной недоступности проверки'
    )


def create_registry_no_date_error(
        payment_name: str,
        registry_id_in_db: int | None = None,
        is_wallet_payment: bool = False,
) -> str:
    name = f'из начислений №{registry_id_in_db}' if is_wallet_payment else payment_name
    return f'❗Вознаграждение {name}. Не удалось отправить реестр в оплату [Дата]'


def create_registry_send_for_payment_error(
        payment_name: str,
        registry_id_in_db: int | None = None,
        is_wallet_payment: bool = False,
) -> str:
    name = f'из начислений №{registry_id_in_db}' if is_wallet_payment else payment_name
    return f'❗Вознаграждение {name}. Не удалось отправить реестр в оплату'


def registry_sent_for_payment(
        payment_name: str,
        registry_id_in_db: int | None = None,
        is_wallet_payment: bool = False,
) -> str:
    name = f'из начислений №{registry_id_in_db}' if is_wallet_payment else payment_name
    return f'✅ Вознаграждение {name}. Реестр отправлен в оплату'


def registry_report(
        payment_name: str,
        successful_payments_count: int,
        total_payments_count: int,
) -> str:
    return (
        f'<b>✅ Вознаграждение {payment_name}</b>\n'
        f'<blockquote>Всего вознаграждений исполнителям (НПД): {total_payments_count}\n'
        f'Из них успешно: {successful_payments_count}</blockquote>'
    )


def wallet_payment_successful_report(
        worker_full_name: str,
) -> str:
    return f'✅ Вознаграждение из кошелька {worker_full_name} успешно зачислено на карту.'


def wallet_payment_error_report(
        wp_id: int,
) -> str:
    return f'❗️Не удалось отправить вознаграждение из кошелька №{wp_id}'


def change_payment_amount(
        worker: WorkerChangeAmountSchema,
) -> str:
    return (f'<b>ФИО:</b> {worker.full_name}\n'
            f'<b>Предварительная сумма:</b> {worker.old_amount}\n\n'
            f'ℹ️ Введите новую сумму (чистыми):')


def new_amount_big_error() -> str:
    return '❗️Новая сумма слишком большая. Введите её еще раз:'


def new_amount_little_error() -> str:
    return '❗️Новая сумма слишком маленькая. Введите её еще раз:'


def change_amounts_no_workers_error() -> str:
    return '❗️Произошла ошибка: Отсутствуют исполнители'


def updating_payment_amounts() -> str:
    return '⌛ Суммы обновляются'


def update_payment_amounts_error() -> str:
    return '❗️Не удалось обновить суммы'


def num_error() -> str:
    return '❗️Введите целое число:'


def order_finish_accountant_notification() -> str:
    return 'ℹ️ Заявка закрыта. Создайте и проверьте реестр для начисления вознаграждений'


def new_wallet_payment_notification(
        date: str,
) -> str:
    return f'ℹ️ Появился новый запрос на выплату из начислений {date}'


def worker_chat_not_found(full_name: str, inn: str) -> str:
    return (
        f'⚠️ Не удалось отправить уведомление о выплате\n\n'
        f'<b>Исполнитель:</b> {full_name}\n'
        f'<b>ИНН:</b> {inn}\n\n'
        f'Причина: чат с исполнителем не найден (возможно, не запускал бот)\n'
        f'Выплата будет отправлена ему автоматически при создании реестра.'
    )


def no_show_card(full_name: str, order_date: str, event_id: int) -> str:
    """Карточка для кассира о невыходе исполнителя"""
    return (
        f"⚠️ <b>{full_name}</b>\n"
        f"принял Заявку и не приступил к оказанию услуг.\n\n"
        f"📅 Дата Заявки: <b>{order_date}</b>\n"
        f"🆔 ID события: <code>{event_id}</code>\n\n"
        f"Укажите сумму корректировки стоимости Заявок."
    )


def no_show_card_reviewed(full_name: str, order_date: str, amount: int, reviewed_by: str) -> str:
    """Карточка после проверки кассиром"""
    return (
        f"✅ <b>{full_name}</b>\n"
        f"принял Заявку и не приступил к оказанию услуг.\n\n"
        f"📅 Дата Заявки: {order_date}\n"
        f"💰 Установлена сумма корректировки: <b>{amount:,} ₽</b>\n"
        f"👤 Проверено: {reviewed_by}"
    )


def request_new_no_show_amount() -> str:
    """Запрос новой суммы договорной комиссии"""
    return (
        "✏️ Введите сумму корректировки:\n\n"
        "💡 Допустимый диапазон: от 1 до 3 000 ₽"
    )


def invalid_no_show_amount() -> str:
    """Ошибка при вводе недопустимой суммы"""
    return (
        "❌ Недопустимая сумма!\n\n"
        "Введите число от 1 до 3 000 ₽."
    )


def deduction_notification(dates_str: str, amount: int) -> str:
    """Уведомление исполнителю об изменении условий расчёта"""
    return (
        f"⚠️ Изменение условий расчёта\n\n"
        f"Согласно данным системы,\n"
        f"{dates_str}\n"
        f"зафиксировано непринятие к оказанию услуг по выбранным Заявкам.\n\n"
        f"💰 Размер корректировки стоимости Заявок: {amount:,} ₽.\n\n"
        f"Корректировка учитывается автоматически при расчёте вознаграждения."
    )


def receipts_request_date() -> str:
    return 'Введите дату для раздела «Чеки» в любом поддерживаемом формате:'


def receipts_info() -> str:
    return 'Дата | Исполнитель | Вознаграждение'


def receipt_status_label(status: str) -> str:
    mapping = {
        'missing': '🟡 нет чека',
        'ready': '🟢 чек есть',
        'sent': '🔵 отправлено в РР',
        'refused': '⚪ отказ от подписи',
    }
    return mapping.get(status, '🟡 нет чека')


def receipt_card(
        full_name: str,
        amount: str,
        service_name: str,
        inn: str,
        payer_name: str,
        status_label: str,
        receipt_url: str | None = None,
) -> str:
    lines = [
        '🧾 <b>Чек по акту</b>',
        '',
        f'<b>Исполнитель:</b> {full_name}',
        f'<b>Вознаграждение:</b> {amount} ₽',
        f'<b>Услуга:</b> {service_name}',
        f'<b>ИНН:</b> {inn}',
        f'<b>Плательщик:</b> {payer_name}',
        f'<b>Статус:</b> {status_label}',
    ]
    if receipt_url:
        lines.extend(['', f'<b>Ссылка на чек:</b> {receipt_url}'])
    return '\n'.join(lines)


def receipt_added_by_worker(full_name: str, amount: str) -> str:
    return (
        '🧾 <b>Получен чек от исполнителя</b>\n\n'
        f'{full_name} | {amount} ₽\n\n'
        'Проверьте чек и отправьте выплату в «Рабочие руки».'
    )


def act_refused_by_worker(full_name: str, amount: str) -> str:
    return f'{full_name} | {amount} ₽ | отказ от подписи'


def receipt_sent_to_rr(full_name: str, amount: str) -> str:
    return f'✅ Чек проверен. Выплата {full_name} | {amount} ₽ отправлена в «Рабочие руки».'


def receipt_replaced() -> str:
    return 'ℹ️ Чек переведён в ожидание нового документа от исполнителя.'
