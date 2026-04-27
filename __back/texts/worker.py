import html as html_module
from datetime import datetime
from decimal import Decimal

import database as db


def request_phone_number():
    return "📱 Введите ваш номер телефона:"


def request_worker_city() -> str:
    return '📍 Выберите вашу локацию:'


def confirmation_of_self_employment() -> str:
    return 'Вы уже являетесь самозанятым?'


def request_verification_code():
    return '🆔 Введите код, отправленный вам в Telegram:'


def request_registration_code() -> str:
    return '🆔 Введите код, отправленный вам на номер телефона:'


def request_registration_inn() -> str:
    return '🪪 Введите ваш ИНН:'


def registration_inn_error() -> str:
    return '❗ИНН должен содержать ровно 12 цифр. Проверьте и попробуйте ещё раз:'


def send_registration_message(
        code: str
) -> str:
    return f"[Рабочие руки] Код подтверждения: {code}"


def verification_code(code):
    return f'🆔 Код для входа в аккаунт: <code>{code}</code>'


def verification_code_error():
    return f'❗Введен неверный код или срок его действия уже истек. ' \
           f'Попробуйте войти в аккаунт позже'


def registration_code_error():
    return f'❗Введен неверный код или срок его действия уже истек. Запросить новый можно командой /start'


def code_error():
    return f'❗Введен неверный код или срок его действия уже истек'


def no_verification_code_error():
    return f'❗Код не найден, попробуйте войти в аккаунт еще раз'


def no_registration_code_error():
    return f'❗Код не найден. Запросите новый командой /start'


def send_manual_error() -> str:
    return '❗Не удалось загрузить инструкцию'


def smz_instruction_text() -> str:
    return (
        '📲 Стать самозанятым просто\n\n'
        'Смотрите картинку выше ☝🏻\n'
        'Там всё пошагово и понятно.\n\n'
        '1️⃣ Скачайте «Мой налог»\n'
        '2️⃣ Нажмите «Стать самозанятым»\n'
        '3️⃣ Подтвердите номер по SMS 📩\n'
        '4️⃣ Отсканируйте паспорт 📄\n'
        '5️⃣ Сделайте фото лица 🤳\n'
        '6️⃣ Подтвердите данные ✅\n\n'
        '🎉 Готово! Вы самозанятый.'
    )


def send_moy_nalog_manual() -> str:
    return '✅ Остался один шаг!\n\n' \
           '⏳ Сейчас мы проверяем ваш статус самозанятости в ФНС России. Подождите 3–5 минут\n\n' \
           'Как только поступит подтверждение — вам откроется доступ ко всему функционалу Платформы\n\n' \
           '📱 После входа на Платформу выполните шаги в приложении «Мой налог»:\n\n' \
           '• Откройте «…Прочие»\n' \
           '• Перейдите в «Партнёры»\n' \
           '• Найдите «Рабочие Руки»\n' \
           '• Нажмите «Разрешить доступ»\n\n' \
           'Если прошло 2-3 минуты жмите  👇'


def verification_completed():
    return '✅ Вы успешно вошли в свой аккаунт.\n' \
           'Используйте кнопки ниже для навигации ⬇️'


def account_notification():
    return 'ℹ️ Вы вошли в этот аккаунт с нового Telegram ID. ' \
           'Чтобы дальше пользоваться ботом, войдите в аккаунт снова. ' \
           'Для этого воспользуйтесь командой /start'


def phone_number_error():
    return "❗Номер телефона введен неверно. Попробуйте еще раз:"


def redirection_to_registration():
    return "⏳ Проверяем статус исполнителя (НПД)\n\n" \
           "📤 Мы отправили запрос партнёру ООО «Рабочие Руки» для проверки вашего статуса.\n\n" \
           "⏱ Ответ ещё не получен. Это нормально и возможно по двум причинам:\n\n" \
           "1️⃣ Прошло меньше 5 минут с момента отправки запроса\n\n" \
           "2️⃣ Вы ещё не заполнили данные и (или) не дали разрешение в приложении «Мой налог» партнёру «Рабочие Руки»\n\n" \
           "📝 Что нужно сделать:\n" \
           "👉 Заполните данные по ссылке\n" \
           "👉 В «Мой налог» дайте разрешение «Рабочие Руки»\n\n" \
           "🔗 https://algoritmplus.online/Contract \n\n" \
           "🔄 После этого проверьте статус кнопкой ниже\n\n" \
           "🔁 Если вы ошиблись номером телефона:\n" \
           "👉 нажмите «Меню»\n" \
           "👉 выберите «Рестарт бота / Обновление» или отправьте команду /start\n\n" \
           "💬 Нужна помощь? 👉 <a href='https://t.me/helpmealgoritm'>нажмите здесь</a>"


def no_self_employment() -> str:
    return ('⏳ <b>Ожидаем подтверждение…</b>\n\n'
            '🔗 Если вы уже перешли по ссылке:\n'
            'https://algoritmplus.online/Contract \n\n'
            '📲 И в приложении «<b>Мой налог</b>» дали согласие партнёру «<b>Рабочие руки</b>»,\n'
            '⏱️ подождите <b>до 5 минут</b>, после чего нажмите кнопку\n'
            '🔄 «<b>Проверить статус регистрации</b>»')


def confirmation_save_data_for_security(
        phone_number: str,
        last_name: str,
        first_name: str,
        middle_name: str
) -> str:
    return "✅ Город выбран!\n" \
           "Сохранить следующие данные для охраны?\n" \
           f"<blockquote>📱Номер телефона: {phone_number}\n" \
           f"👤Фамилия: {last_name}\n" \
           f"👤Имя: {first_name}\n" \
           f"👤Отчество: {middle_name}</blockquote>"


def first_name_for_security():
    return "Отправьте ваше Имя:"


def last_name_for_security():
    return "Отправьте вашу Фамилию:"


def middle_name_for_security():
    return "Теперь отправьте ваше Отчество:"


def confirmation_save_new_data_for_security(
        phone_number: str,
        last_name: str,
        first_name: str,
        middle_name: str
) -> str:
    return "Сохранить следующие данные для охраны?\n" \
           f"📱Номер телефона: {phone_number}\n" \
           f"👤ФИО: {last_name} {first_name} {middle_name}"


def restart_bot():
    return "✅ Бот перезапущен.\n" \
           "Используйте кнопки ниже для навигации ⬇️"


def rejoin_worker():
    return "С возвращением. Используйте кнопки ниже для навигации ⬇️"


def cmd_start_user():
    return (
        '👋 Добро пожаловать на Платформу «Алгоритм Плюс»\n\n'
        '📌 Платформа для самозанятых\n'
        'Вы сами выбираете заявки и оказываете услуги, когда удобно — без графиков и начальников\n\n'
        '💰 Вознаграждение — сразу после оказания услуг\n\n'
        '🔐 Уже проходили регистрацию?\n'
        '➡️ Просто войдите по номеру телефона\n\n'
        '🆕 Впервые на платформе?\n'
        '➡️ Пройдите регистрацию — это займёт пару минут\n\n'
        '👇 Выберите действие'
    )


def data_for_security(phone_number, last_name, first_name, middle_name):
    return f"📱Номер телефона: {phone_number}\n" \
           f"👤Фамилия: {last_name}\n" \
           f"👤Имя: {first_name}\n" \
           f"👤Отчество: {middle_name}"


def save_data_for_security(phone_number, last_name, first_name, middle_name):
    return (
        "Сохранить следующие данные для охраны?\n"
        f"📱Номер телефона: {phone_number}\n"
        f"👤Фамилия: {last_name}\n"
        f"👤Имя: {first_name}\n"
        f"👤Отчество: {middle_name}"
    )


def accept_save_new_data_for_security(phone_number, last_name, first_name, middle_name):
    return (
        "Сохранить следующие данные для охраны?\n"
        f"📱Номер телефона: {phone_number}\n"
        f"👤ФИО: {last_name} {first_name} {middle_name}"
    )


def update_data_for_security() -> str:
    return "✅ Ваши данные успешно обновлены!"


def request_birth_date() -> str:
    return "📅 Введите вашу дату рождения (ДД.ММ.ГГГГ):"


def referral(link, bonus, shifts, friends, completed):
    return "🎯 Бонусная программа\n\n" \
           f"👥 Всего привлечено друзей: {friends}\n" \
           f"✅ Из них выполнили условия: {completed}\n" \
           f"💰 Размер бонуса: {bonus}₽\n\n" \
           "🔗 Ваша реферальная ссылка:\n" \
           f"<code>{link}</code>\n\n" \
           f"ℹ️ Отправьте эту ссылку друзьям и получите <b>{bonus}₽ после успешного завершения {shifts} заявок</b>, принятых приглашённым пользователем."


def referral_panel_message_html(
    link: str,
    bonus: str,
    shifts: int,
    friends: int,
    completed: int,
) -> str:
    """Текст бонуса для веб-панели: структура и классы, без привязки к Telegram в формулировках."""
    lk = html_module.escape(link or '')
    b = html_module.escape(str(bonus))
    return (
        '<div class="panel-rich-text panel-rich-text--referral">'
        '<h3 class="panel-rich-h">Бонус за приглашения</h3>'
        '<ul class="panel-rich-list">'
        f'<li>Приглашено друзей: <strong>{int(friends)}</strong></li>'
        f'<li>Выполнили условия: <strong>{int(completed)}</strong></li>'
        f'<li>Размер бонуса: <strong>{b}₽</strong></li>'
        '</ul>'
        '<p class="panel-rich-p">Ваша персональная ссылка (скопируйте и отправьте другу):</p>'
        f'<pre class="panel-code" tabindex="0">{lk}</pre>'
        f'<p class="panel-rich-note">После того как приглашённый пользователь примет и успешно завершит '
        f'<strong>{int(shifts)}</strong> заявок на платформе, вы получите <strong>{b}₽</strong>.</p>'
        '</div>'
    )


def request_card() -> str:
    return '💳 Введите номер вашей карты:'


def card_number_error() -> str:
    return '❗Номер карты должен содержать только цифры. Попробуйте ещё раз:'


def luhn_check_error() -> str:
    return '❗Номер карты введён некорректно. Проверьте его и попробуйте ещё раз:'


def card_not_unique_error() -> str:
    return (
        '❗ Такой номер карты уже есть у другого исполнителя\n\n'
        '👉 Введите другой номер карты (уникальный)\n\n'
        '✏️ Остальные данные сохранятся — исправьте только карту\n\n'
        '🆘 Поддержка: https://t.me/helpmealgoritm'
    )


def reg_error_inn_exists() -> str:
    """ИНН уже есть в нашей локальной БД — предлагаем войти."""
    return (
        '<b>ИНН уже зарегистрирован</b>\n\n'
        '❗ С таким ИНН уже есть исполнитель на платформе\n'
        '👉 Нажмите /start и воспользуйтесь функцией «Войти»\n\n'
        '✏️ Повторно вводить данные не нужно\n\n'
        '🆘 Поддержка: https://t.me/helpmealgoritm'
    )


def reg_error_inn_rr_exists() -> str:
    """ИНН есть в глобальной базе РР, но не у нас — нужна ручная регистрация."""
    return (
        '❗️ Ваш ИНН уже есть в глобальной базе «Рабочие Руки»\n\n'
        '👉 Для продолжения обратитесь в службу поддержки — зарегистрируем вас вручную\n\n'
        '🆘 Поддержка: https://t.me/helpmealgoritm'
    )


def reg_error_phone_exists() -> str:
    return (
        '❗ Такой номер телефона уже зарегистрирован\n\n'
        '👉 Введите другой номер телефона\n\n'
        '✏️ Остальные данные сохранятся — исправьте только номер\n\n'
        '🆘 Поддержка: https://t.me/helpmealgoritm'
    )


def update_card_error():
    return '❗Не удалось обновить карту'


def preview_contract() -> str:
    return (
        '📄 <b>Для принятия Заявки необходимо заключить гражданско-правовой договор.</b>\n\n'
        'Ознакомьтесь с договором <b>(PDF выше)</b>.\n'
        'Подписание осуществляется вводом <b>4 цифр одного из ваших идентификаторов</b>.\n'
        'Способ выбирается случайно: <b>последние 4 цифры ИНН</b>, <b>день и месяц рождения</b>, <b>год рождения</b> или <b>последние 4 цифры паспорта</b>.\n\n'
        'Подписывая договор и принимая Заявку, вы подтверждаете, что:\n'
        ' • действуете добровольно, самостоятельно и в своих интересах;\n'
        ' • принимаете обязательство по оказанию услуг в рамках гражданско-правового договора;\n'
        ' • не состоите в трудовых отношениях с Платформой и/или третьими лицами по данной Заявке;\n'
        ' • ознакомлены и согласны с условиями Заявки и договора.\n\n'
        'Подтверждение распространяется сразу на <b>3 договора с юридическими лицами Платформы</b>.\n'
        'При выплате останется рабочим только договор выбранного юрлица.\n\n'
        '❗️Без подписания договора принятие Заявки невозможно.\n\n'
        'Подтвердить принятие Заявки?'
    )


def change_card_request_sign_contracts() -> str:
    return (
        'ℹ️ Банковская карта для получения вознаграждения указывается в тексте Договора оказания услуг.\n'
        'При изменении банковской карты автоматически заключаются <b>новые Договоры оказания услуг</b>.\n\n'
        'Для подтверждения введите <b>4 последние цифры вашего ИНН</b>:'
    )


def sign_contracts_for_card_wait() -> str:
    return 'ℹ️ Подписываем договоры и обновляем карту. Пожалуйста, подождите'


def sign_contracts_for_registration_wait() -> str:
    return 'ℹ️ Подписываем договоры, посмотреть их вы сможете в разделе "Обо мне". Пожалуйста, подождите'


def request_sign_contract(
        org_name: str = None,
) -> str:
    return (
        '📄 Вы подписываете договор с заказчиками\n\n'
        '🔐 Для подтверждения введите 4 последние цифры вашего ИНН'
    )


def contract_inn_error() -> str:
    return '❗Цифры не совпадают. Попробуйте ввести их еще раз:'


def create_contract_error() -> str:
    return '❗Не удалось создать договор'


def sign_contract_error() -> str:
    return '❗Не удалось подписать договор'


def contract_signed() -> str:
    return '✅ Договор подписан'


def contract_rejected() -> str:
    return 'ℹ️ Регистрация остановлена. Чтобы заново зарегистрироваться, воспользуйтесь командой /start'


def contract_rejected_gtrr() -> str:
    return 'ℹ️ Контракт не подписан. Переход на РР остановлен'


def update_card_reject_contract() -> str:
    return 'ℹ️ Смена карты остановлена, так как контракт не был подписан'


def send_contract_error() -> str:
    return '❗Не удалось отправить договор. Попробуйте позже'


def all_contracts_already_signed() -> str:
    return '✅ Договоры со всеми заказчиками уже подписаны\n\nЗавершаем регистрацию...'


def registration_user_completed():
    return "✅ <b>Регистрация пройдена</b>\n" \
           "Вам будут поступать <b>уведомления о новых заявках Заказчиков на оказание услуг.</b>\n\n"\
           "Используйте кнопки ниже для навигации ⬇️"


def rr_partner_connection_caption() -> str:
    return (
        '🎉 <b>Статус подтверждён!</b>\n\n'
        '☝🏻 Смотрите картинку выше — там всё пошагово, как подключить партнёра «Рабочие Руки»\n\n'
        '🚀 <b>Добро пожаловать!</b>\n'
        'Вам открыт доступ ко всему функционалу Платформы'
    )


def phone_for_security():
    return '✒️ Отправьте ваш номер телефона. Для этого нажмите на кнопку ниже.\n\n' \
           '💬 Если у вас возникнут проблемы, напишите в поддержку, перейдя по ссылке: ' \
           '[<a href="https://t.me/helpmealgoritm">нажмите здесь</a>]'


def try_register_again():
    return '❗Вы еще не зарегистрированы.\nЕсли вы подали документы, подождите пока регистрация завершиться.\n' \
           'После чего нажмитe на кнопку\n[🔄 Проверить статус регистрации] или перезапустите бота командой\n/start'


def callback_save_data_for_security(phone_number, last_name, first_name, middle_name):
    return "✅ Номер телефона подтвержден!\n\n" \
           "Сохранить следующие данные для охраны?\n" \
           f"📱Номер телефона: {phone_number}\n" \
           f"👤Фамилия: {last_name}\n" \
           f"👤Имя: {first_name}\n" \
           f"👤Отчество: {middle_name}\n"


def data_for_security_updated() -> str:
    return "✅ Ваши данные успешно обновлены!"


def update_data_for_security_error() -> str:
    return "❗Не удалось обновить данные. Попробуйте еще раз"


async def sending_order_to_users(city, customer_id, job, amount, date, day, day_shift, night_shift, job_fp):
    time = day_shift if day_shift else night_shift
    shift = '☀️<b>ДНЕВНОЙ ПЕРИОД</b>' if day_shift else '🌙<b>НОЧНОЙ ПЕРИОД</b>'
    organization = await db.get_customer_organization(customer_id)
    return "<b>Новая заявка</b>\n" \
           f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>📦 Услуга:</b> {job}\n" \
           f"<b>📅 Дата:</b> {date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>⏰ Период оказания услуг:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💰 Вознаграждение:</b> {amount}₽\n" \
           f"<b>ТЗ по услуге:</b> {job_fp}</blockquote>"


async def show_order_search(city, customer_id, job, amount, date, day, day_shift, night_shift, job_fp):
    time = day_shift if day_shift else night_shift
    shift = '☀️<b>ДНЕВНОЙ ПЕРИОД</b>' if day_shift else '🌙<b>НОЧНОЙ ПЕРИОД</b>'
    organization = await db.get_customer_organization(customer_id)
    return f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>📦 Услуга:</b> {job}\n" \
           f"<b>📅 Дата:</b> {date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>⏰ Период оказания услуг:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💰 Вознаграждение:</b> {amount}₽\n" \
           f"<b>ТЗ по услуге:</b> {job_fp}</blockquote>"


def customer_search_orders():
    return '🏢 Выберите Получателя услуг:'


def has_application_or_work_respond():
    return f"❗Вы не можете откликнуться, так как вы уже отправили заявку ранее или она уже одобрена.\n" \
           f"ℹ️ Больше информации в разделе \n«📝 Отклики»"


def no_orders_for_search():
    return f"ℹ️ В данный момент доступных заявок нет"


async def approved_user_application(city, customer_id, job, amount, date, day, day_shift, night_shift):
    time = day_shift if day_shift else night_shift
    shift = '☀️<b>ДНЕВНОЙ ПЕРИОД</b>' if day_shift else '🌙<b>НОЧНОЙ ПЕРИОД</b>'
    organization = await db.get_customer_organization(customer_id)
    return "<b>Ваша заявка подтверждена!</b>\n" \
           f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>📦 Услуга:</b> {job}\n" \
           f"<b>📅 Дата:</b> {date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>⏰ Период оказания услуг:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💰 Вознаграждение:</b> {amount}₽</blockquote>\n\n" \
           f"Дата и время оказания услуг: {date} с {time.split('-')[0]}"


async def rejected_user_application(city, customer_id, job, amount, date, day_shift, night_shift, day):
    time = day_shift if day_shift else night_shift
    shift = '<b>ДЕНЬ</b>' if day_shift else '<b>НОЧЬ</b>'
    organization = await db.get_customer_organization(customer_id)
    return "❗Ввиду большого количества откликнувшихся исполнителей (НПД) на данный момент, " \
           "Ваша запись была отклонена! Пробуйте взять заявку позднее\n" \
           f"<blockquote><b>📍 Город:</b> {city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>💼 Услуга:</b> {job}\n" \
           f"<b>🗓️ Дата:</b> {date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💵 Оплата:</b> {amount}₽</blockquote>"


def confirmation_respond_low_rating(
        rating: str,
        amount,
        total_orders: int,
        successful_orders: int,
        plus: int,
):
    am = int(Decimal(str(amount)) * Decimal('11'))

    return (f"<b>📊 Ваш рейтинг: {rating}</b>\n"
         f"Принято заявок: <b>{total_orders}</b> | Услуги оказаны: <b>{successful_orders}</b> | Не подтверждено: <b>{plus}</b>\n\n"
         f"📌 Подробная информация о показателе рейтинга доступна в разделе «Обо мне».\n\n"
         f"💰 Информация о возможном вознаграждении:\n\n"
         f"В качестве ориентировочной оценки Платформа отображает предполагаемый размер вознаграждения при оказании услуг по данной Заявке.\n\n"
         f"При условном объёме около 11 единиц ориентировочный размер вознаграждения может составить ≈ <b>{am}</b> ₽.\n\n"
         f"Указанные значения являются оценочными, не являются обязательством и зависят от фактически оказанного объёма услуг.\n\n"
         f"⚠️ Размер вознаграждения по Заявке может отличаться для разных Исполнителей и формируется автоматически Платформой с учётом показателя рейтинга, а также иных условий Заявки.\n\n"
         f"❗️ В случае принятия Заявки и последующего отказа от оказания услуг либо неприступления к их оказанию в согласованный период, могут применяться последствия, предусмотренные договором, включая договорную неустойку в размере 3 000 ₽, реализуемую в порядке, установленном договором, в том числе посредством зачёта встречных однородных требований, а также изменение показателя рейтинга.\n\n"
         f"✅ В случае если отклик по Заявке не был подтверждён, показатель рейтинга Исполнителя увеличивается на +1%.\n\n"
         f"🔘 Вы подтверждаете добровольное принятие Заявки на оказание услуг на указанных условиях, осознавая, что указанные значения носят оценочный характер, а оказание услуг осуществляется Исполнителем самостоятельно в рамках гражданско-правовых отношений, без возникновения трудовых отношений с Платформой или третьими лицами по данной заявке?")


def confirmation_respond_high_rating() -> str:
    return "Подтверждая принятие Заявки, Исполнитель подтверждает, что добровольно принимает на себя обязательство по оказанию услуг в рамках гражданско-правового договора, действует самостоятельно и осознанно, а также подтверждает отсутствие трудовых отношений с Платформой и (или) третьими лицами по данной Заявке.\n🔘 Вы подтверждаете принятие Заявки на оказание услуг на указанных условиях?"


def apply_preview_html_low_rating(
        rating: str,
        amount: str,
        total_orders: int,
        successful_orders: int,
        plus: int,
        coefficient: Decimal,
) -> str:
    """Фрагмент HTML для веб-модалки отклика: абзацы и списки, без эмодзи (обёртку даёт фронт)."""
    am = int((Decimal(amount) * coefficient) * Decimal('11'))
    r = html_module.escape(str(rating))
    return (
        f'<p class="panel-rich-h">Ваш рейтинг: {r}</p>'
        '<ul class="panel-rich-list">'
        f'<li>Принято заявок: <strong>{total_orders}</strong></li>'
        f'<li>Услуги оказаны: <strong>{successful_orders}</strong></li>'
        f'<li>Не подтверждено: <strong>{plus}</strong></li>'
        '</ul>'
        '<p class="panel-rich-p">Подробнее о показателе рейтинга — в разделе «Обо мне».</p>'
        '<p class="panel-rich-h">Вознаграждение</p>'
        '<p class="panel-rich-p">В качестве ориентировочной оценки Платформа отображает предполагаемый размер '
        'вознаграждения при оказании услуг по данной Заявке.</p>'
        f'<p class="panel-rich-p">При условном объёме около 11 единиц ориентировочный размер вознаграждения '
        f'может составить примерно <strong>{am}</strong>&nbsp;₽.</p>'
        '<p class="panel-rich-p">Указанные значения являются оценочными, не являются обязательством и зависят от '
        'фактически оказанного объёма услуг.</p>'
        '<blockquote>'
        'Размер вознаграждения по Заявке может отличаться для разных исполнителей и формируется автоматически '
        'Платформой с учётом показателя рейтинга и иных условий Заявки.'
        '</blockquote>'
        '<blockquote>'
        'В случае принятия Заявки и последующего отказа от оказания услуг либо неприступления к их оказанию в '
        'согласованный период могут применяться последствия, предусмотренные договором, включая договорную '
        'неустойку в размере 3&nbsp;000&nbsp;₽, реализуемую в порядке, установленном договором, в том числе '
        'посредством зачёта встречных однородных требований, а также изменение показателя рейтинга.'
        '</blockquote>'
        '<p class="panel-rich-p">Если отклик по Заявке не был подтверждён, показатель рейтинга исполнителя '
        'увеличивается на&nbsp;+1%.</p>'
        '<p class="panel-rich-meta"><strong>🔘</strong> Вы подтверждаете добровольное принятие Заявки на '
        'оказание услуг на указанных условиях, осознавая, что указанные значения носят оценочный характер, а '
        'оказание услуг осуществляется вами самостоятельно в рамках гражданско-правовых отношений, без '
        'возникновения трудовых отношений с Платформой или третьими лицами по данной заявке?</p>'
    )


def apply_preview_html_high_rating() -> str:
    return (
        '<p class="panel-rich-p">Подтверждая принятие Заявки, вы подтверждаете, что добровольно принимаете на себя '
        'обязательство по оказанию услуг в рамках гражданско-правового договора, действуете самостоятельно и '
        'осознанно, а также подтверждаете отсутствие трудовых отношений с Платформой и (или) третьими лицами по '
        'данной Заявке.</p>'
        '<p class="panel-rich-meta"><strong>🔘</strong> Вы подтверждаете принятие Заявки на оказание услуг '
        'на указанных условиях?</p>'
    )


def apply_preview_order_summary_html(
        city: str,
        organization: str,
        job: str,
        date: str,
        day: str,
        period_time: str,
        is_day_shift: bool,
        amount: str,
        job_fp: str | None,
        travel_compensation: int | None,
) -> str:
    """Карточка заявки для веб-модалки отклика (как blockquote в Telegram) + компенсация за проезд 🚌."""
    esc = html_module.escape
    shift = (
        '☀️ <strong>ДНЕВНОЙ ПЕРИОД</strong>' if is_day_shift else '🌙 <strong>НОЧНОЙ ПЕРИОД</strong>'
    )
    fp = f'<br><b>ТЗ по услуге:</b> {esc(job_fp)}' if job_fp else ''
    bus = ''
    inner = (
        f'<b>📍 Город:</b> {esc(city)}<br>'
        f'<b>👥 Получатель услуг:</b> {esc(organization)}<br>'
        f'<b>📦 Услуга:</b> {esc(job)}<br>'
        f'<b>📅 Дата:</b> {esc(date)}<br>'
        f'<b>{esc(day)}</b><br>'
        f'<b>⏰ Период оказания услуг:</b> {esc(period_time)}<br>'
        f'{shift}<br>'
        f'<b>💰 Вознаграждение:</b> {esc(amount)}&nbsp;₽'
        f'{fp}{bus}'
    )
    return f'<div class="apply-order-summary-wrap"><blockquote class="apply-order-summary__quote">{inner}</blockquote></div>'


async def apply_preview_html_for_friend(
        order_id: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        amount: str,
        travel_compensation: int | None = None,
) -> str:
    order = await db.get_order(order_id=order_id)
    dt_obj = datetime.strptime(order.date, '%d.%m.%Y')
    week = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
    time = order.day_shift if order.day_shift else order.night_shift
    shift = 'ДЕНЬ' if order.day_shift else 'НОЧЬ'
    organization = await db.get_customer_organization(order.customer_id)
    esc = html_module.escape
    label = f'{esc(first_name.strip())} {esc((last_name or "")[:1])}.{esc((middle_name or "")[:1])}.'.strip()
    inner = (
        f'<strong>Город:</strong> {esc(order.city)}<br>'
        f'<strong>Получатель услуг:</strong> {esc(organization)}<br>'
        f'<strong>Услуга:</strong> {esc(order.job_name)}<br>'
        f'<strong>Дата:</strong> {esc(order.date)}<br>'
        f'<strong>День недели:</strong> {esc(week[dt_obj.weekday()])}<br>'
        f'<strong>Время:</strong> {esc(time)}<br>'
        f'<strong>Период:</strong> {esc(shift)}<br>'
        f'<strong>Вознаграждение:</strong> {esc(amount)}&nbsp;₽'
    )
    return (
        '<p class="panel-rich-p">Данные друга подтверждены. Вы записываете исполнителя (НПД) '
        f'<strong>{label}</strong> на заявку:</p>'
        f'<blockquote>{inner}</blockquote>'
        '<p class="panel-rich-p">Согласно п.&nbsp;2 ст.&nbsp;6 ФЗ №422-ФЗ, он несёт ответственность за выполнение '
        'заявки. Если друг не выйдет на заявку, его рейтинг будет снижен. При злоупотреблениях доступ к функции '
        'может быть ограничен согласно правилам платформы. Финансовая ответственность не применяется (ст.&nbsp;307 '
        'ГК&nbsp;РФ).</p>'
    )


def has_date(date_time):
    return f"Записаться не получится, так как уже есть заявка на эту дату \"{date_time}\""


def send_respond():
    return "✅ Отклик по заявке успешно отправлен и находится на рассмотрении."


def no_respond_sent():
    return "❗Не удалось отправить ваш отклик"


async def reminder(order_id):
    order = await db.get_order(order_id=order_id)
    time = order.day_shift if order.day_shift else order.night_shift
    return "⏰ Напоминание по ранее подтверждённой Заявке\n\n" \
           f"По ранее подтверждённой вами Заявке период оказания услуг начинается {order.date} с {time}\n\n" \
           "Оказание услуг осуществляется Исполнителем добровольно и по его самостоятельному решению в рамках гражданско-правовых отношений.\n\n"


def delete_inactive_user_notification() -> str:
    return '⚠️ Мы заметили, что вы зарегистрировались более 48 часов назад и не взяли ни одной заявки.\n\n' \
           '🛡️ В рамках политики безопасности ваш аккаунт был удалён.\n\n' \
           '🔁 Повторно присоединиться к платформе можно через меню:\n' \
           'Старт → Выбор локации → Ввод номера телефона → Сохранить → Поиск заявок'


def order_in_progress_notification(
        order_time: str,
        order_date: str,
        worker_full_name: str,
) -> str:
    return "✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅\n" \
           f"🚨 <b>{worker_full_name}!</b>\n" \
           f"Уведомляем вас о том, что по ранее принятому вами заказу оказание услуг согласовано и подтверждено.\n\n" \
           f"Получатель услуг уведомлён и ожидает вас {order_date} в период {order_time} ⏰\n\n" \
           "❗Оказание услуг осуществляется вами добровольно. В случае изменения ваших обстоятельств " \
           "вы вправе отказаться от оказания услуг, воспользовавшись функцией Платформы «Управление заявкой», " \
           "до начала согласованного периода.\n\n" \
           "⚠️ Данное сообщение носит исключительно информационный характер и не устанавливает трудовых обязанностей, " \
           "режима рабочего времени либо подчинённости.\n" \
           "💳 Выплата вознаграждения производится после подтверждения факта оказания услуг.\n" \
           "✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅"


def user_ref_notification(last_name, first_name, middle_name, amount):
    return f"Ваш реферал: <b>{last_name} {first_name} {middle_name}</b> выполнил условия. " \
           f"Вам будет начислен бонус в размере {amount}₽"


async def user_applications(worker_id, order_id, customer_id, city, job, date, day_shift, night_shift, amount, day):
    has_application = await db.has_application(worker_id=worker_id, order_id=order_id)
    has_work = await db.has_work(worker_id=worker_id)

    time = day_shift if day_shift else night_shift
    organization = await db.get_customer_organization(customer_id)
    application_status = 'На модерации' if has_application else 'Одобрена'
    shift = '<b>ДЕНЬ</b>' if day_shift else '<b>НОЧЬ</b>'

    text = f"<b>Ваша заявка</b>\n" \
           f"<b>Статус:</b> {application_status}\n"

    if has_work:
        text += f"Напоминаем: ранее принятая вами Заявка на {date}, начало периода: {time.split('-')[0]}\n"

    text += f"<blockquote><b>📍 Город:</b> {city}\n" \
            f"<b>👥 Получатель услуг:</b> {organization}\n" \
            f"<b>💼 Услуга:</b> {job}\n" \
            f"<b>🗓️ Дата:</b> {date}\n" \
            f"<b>                  {day}</b>\n" \
            f"<b>🕒 Время:</b> {time}\n" \
            f"                       {shift}\n" \
            f"<b>💵 Оплата:</b> {amount}₽</blockquote>"

    return text


def accept_update_workers_count():
    return "Вы уверены что хотите обновить <b>лимит откликов по заявке</b>?"


def enter_workers_count():
    return "👤 Введите лимит откликов по заявке:"


def workers_count_updated():
    return "✅ Условия заявки успешно обновлены. Заявка опубликована и доступна на Платформе."


def application_none():
    return "Вы пока не откликнулись ни на одну заявку.\nДоступные заявки размещены в разделе «Поиск заявок»."


def remove_application():
    return "Вы уверены что хотите удалить свой отклик?"


def remove_worker():
    return (
        "❗<b>Заявка ранее была подтверждена вами.</b>\n\n"
        "Вы вправе самостоятельно отказаться от оказания услуг по данной Заявке до начала периода оказания услуг.\n\n"
        "<blockquote>Обратите внимание:\n\n"
        "в случае отказа после подтверждения Заявки стоимость доступных Заявок может быть временно скорректирована,\n"
        "а также может измениться информационный показатель рейтинга.\n\n"
        "Все решения об участии либо неучастии в Заявках принимаются вами самостоятельно.</blockquote>\n\n"
        "Вы подтверждаете своё решение?"
    )


def remove_worker_manager_app():
    return "ℹ️ Вы уверены что хотите отказаться от заявки?"


def application_removed():
    return "✅ Ваш отклик был успешно удален!"


def cant_delete_application():
    return "❗Вы не можете отказаться от Заявки, так как уже наступил период оказания услуг."


def first_rejection():
    return (
        "⚠️ <b>Отказ зафиксирован</b>\n\n"
        "Вы отказались от Заявки менее чем за 12 часов до начала периода оказания услуг.\n\n"
        "Это является отказом от исполнения принятого обязательства по Заявке.\n\n"
        "Обязательство по данной Заявке прекращено.\n\n"
        "В соответствии с договором и Правилами Платформы может быть применена договорная компенсация.\n\n"
        "Основание: ст. 309, 310, 330, 393 ГК РФ.\n\n"
        "❗ Заявка возвращена в поиск исполнителей."
    )


def order_worker_deleted_without_rejection():
    return "✅ Ваша заявка была успешно удалена!"


def not_first_rejection():
    return (
        "⚠️ <b>Доступ ограничен</b>\n\n"
        "Зафиксирован повторный отказ от Заявки менее чем за 12 часов до начала периода оказания услуг.\n\n"
        "Обязательства по принятым Заявкам прекращаются по факту отказа Исполнителя.\n\n"
        "В соответствии с Правилами Платформы доступ к новым Заявкам временно ограничен.\n\n"
        "📞 Просьба связаться со службой поддержки для дальнейшего сотрудничества:\n"
        "+7 (926) 300-09-02\n"
        "+7 (936) 309-03-04\n\n"
        "📄 Все отношения регулируются гражданско-правовым договором."
    )


def middleware_message_block():
    return "<blockquote>⛔ Доступ к откликам на новые Заявки временно ограничен в соответствии с Правилами Платформы.\n" \
           "📞 Пожалуйста, свяжитесь со <a href='https://t.me/helpmealgoritm'>службой поддержки</a> для уточнения " \
           "деталей и возможного восстановления доступа к платформе.</blockquote>"


def middleware_callback_block():
    return "⛔ Доступ к откликам на новые Заявки временно ограничен в соответствии с Правилами Платформы.\n" \
           "📞 Служба поддержки:\nhttps://t.me/helpmealgoritm"


def user_unblocked():
    return "✅ Доступ к функциям Платформы восстановлен."


def user_blocked():
    return "ℹ️ Доступ к отдельным функциям Платформы временно ограничен."


def accept_change_city(current_city):
    return f"🌆Ваш текущий город: <b>{current_city}</b>\n" \
           "Вы точно хотите изменить его?"


def choose_city():
    return "🌆 Выберите новый город:"


def confirmation_update_city(
        old_city: str,
        new_city: str
) -> str:
    return f"📍 {old_city} → 📍 {new_city}\n\n" \
           f"Смена локации осуществляется с учётом:\n" \
           "— Федерального закона № 152-ФЗ «О персональных данных»;\n" \
           "— ст. 139 Гражданского кодекса РФ (охрана коммерческой тайны);\n" \
           "— Федерального закона № 422-ФЗ «О налоге на профессиональный доход».\n\n" \
           "⚠️ До подтверждения менеджером ваша текущая локация останется прежней.\n" \
           "⚖️ Данное ограничение не препятствует вашему праву свободно выбирать заявки, " \
           "а направлено исключительно на защиту коммерческой тайны Платформы и Получателям услуг.\n\n" \
           "Вы уверены, что хотите сменить локацию?"


def request_to_change_city_sent() -> str:
    return '✅ Ваш запрос на смену локации успешно отправлен менеджеру'


def request_to_change_city_error() -> str:
    return '❗Не удалось отправить менеджеру запрос на смену локации'


def notification_city_changed(
        city: str
) -> str:
    return f"✅ Смена локации подтверждена. Ваша новая локация: 📍 {city}."


def notification_city_not_changed(
        city: str
) -> str:
    return f"❌ Смена локации отклонена менеджером.\n" \
           f"Ваша текущая локация остаётся: 📍 {city}.\n" \
           f"Попробуйте повторить попытку позднее или обратитесь в службу поддержки по телефонам: " \
           f"+7 (926) 300-09-02 или +7 (936) 309-03-04 ежедневно с 10:00 до 18:00. Спасибо за понимание."


def dates_none():
    return f'❗У получателя услуг нет заявок на другие даты'


def dates():
    return f"🗓️ Выберите дату, на которую хотите записаться:"


def delete_info():
    return f'❗Менеджер удалил одну из ваших заявок. Больше информации в разделе «📝 Управление заявкой»'


def forman_notification(customer):
    return f'ℹ️ Вы были назначены представителем исполнителя у «{customer}».\n\n' \
           f'У вас есть доступ к следующим функциям:\n\n' \
           f'<b>📣 Оповещение на объекте</b>\n' \
           f'• Отправка уведомления всем исполнителям, кто находится вместе с вами на заявке\n\n' \
           f'<b>👤 Удалить исполнителя</b>\n' \
           f'• Удаление уже одобренных исполнителей, когда заявка находится в подборе исполнителей\n\n' \
           f'Эти функции будут доступны после того, как вы возьмете любую заявку у «{customer}»'


def forman_delete_notification(customer):
    return f'ℹ️ Вы были удалены из представителей исполнителя у «{customer}»'


def foreman_no_order(customer):
    return f'❗Функция доступна после подтверждения вашей заявки по Получателю услуг «{customer}».'


def shout_menu():
    return '📣 Оповещение на объекте. Выберите действие:'


def request_shout_message():
    return '📝 Напишите и отправьте информационное сообщение, которое увидят Исполнители, находящиеся на объекте в период оказания услуг по заявке.\n\n' \
           '🚫 Не создавайте «рабочие» чаты/группы с Исполнителями в мессенджерах. Для взаимодействия используйте функционал Платформы. В случае нарушений могут применяться меры, предусмотренные гражданско-правовым договором (включая договорную неустойку), в порядке, установленном договором.\n\n' \
           '📞 При необходимости в конце сообщения можно указать номер телефона для обратной связи.'


def customer_request_shout_message():
    return '📝 Напишите и отправьте информационное сообщение, которое увидят Исполнители, находящиеся на объекте в период оказания услуг по заявке.\n\n' \
           '🚫 Не создавайте «рабочие» чаты/группы с Исполнителями в мессенджерах. Для взаимодействия используйте функционал Платформы.'


def shout_text(sender_full_name, text):
    return f'‼️ Важное сообщение\n' \
           f'📣 Представитель Платформы (контактное лицо): <b>{sender_full_name}</b> сообщает: \n<blockquote>{text}\n</blockquote>' \
           f'ℹ️ Сообщение носит информационный характер.\nПосле прочтения нажмите: \n«✅ Ознакомился ✅»'


def customer_shout_text(sender_full_name, text):
    return f'‼️ Важное сообщение\n' \
           f'📣 Получатель услуг: <b>{sender_full_name}</b> сообщает: \n<blockquote>{text}\n</blockquote>' \
           f'ℹ️ Сообщение носит информационный характер.\nПосле прочтения нажмите: \n«✅ Ознакомился ✅»'


def shout_start():
    return 'ℹ️ Отправка уведомления началась'


def shout_finish(shout_id, workers_count):
    contacts = 'контакту' if str(workers_count)[-1] == '1' else 'контактам'
    return f'📣 Уведомление №{shout_id}\n' \
           f'📤 Сообщение доставлено: \n{workers_count} {contacts}\n\n' \
           f'Подробнее: \n«📊 Статистика»'


def send_shout_error():
    return '❗Не удалось отправить уведомление'

def shout_workers_count_error():
    return '❗Невозможно сделать уведомление. На заявке только вы'


def customer_shout_workers_count_error():
    return '❗Невозможно отправить уведомление: по данной заявке сейчас нет Исполнителей на объекте.'


def shout_stat():
    return f'<b>📊 Статистика</b>\n' \
           f'Нажмите на номер уведомления, у которого вы хотите посмотреть статистику:'


def shout_stat_none():
    return f'<b>📊 Статистика</b>\n' \
           f'У вас нет еще ни одного уведомления!'


def customer_shout_stat_none():
    return f'<b>📊 Статистика</b>\n' \
           f'У вас нет еще ни одного уведомления на этой заявке!'


def show_shout_stat(shout_id, views, workers_count):
    workers_contacts = 'контакту' if str(workers_count)[-1] == '1' else 'контактам' \
        if str(workers_count)[-1] != '0' else 'контактов'
    views_contacts = 'контакт' if str(views)[-1] == '1' else 'контакта' \
        if str(views)[-1] in ['2', '3', '4'] else 'контактов'
    return f'📣 Уведомление №{shout_id}\n' \
           f'📤 Сообщение доставлено:\n{workers_count} {workers_contacts}\n' \
           f'👁️ Прочитано: {views} {views_contacts}'


def order_in_progress_error():
    return '❗Невозможно воспользоваться данной функцией, так как статус заявки \n«Оказание услуг»'


def delete_workers_menu():
    return 'ℹ️ Выберите исполнителя, которого хотите удалить:'


def delete_workers_none():
    return 'ℹ️ Нет исполнителей, которых можно удалить'


def confirmation_delete_worker(worker_full_name):
    return f'Вы уверены, что хотите удалить <b>{worker_full_name}</b>'


def delete_worker_error():
    return '❗Не удалось удалить исполнителя'


def send_delete_worker():
    return 'ℹ️ Заявка на удаление исполнителя отправлена менеджеру на рассмотрение'


def order_error():
    return 'ℹ️ Заявка не существует'


def manager_confirmation_delete_worker(worker_full_name, customer):
    return f'ℹ️ Представитель исполнителя у «{customer}» удалил {worker_full_name}. Вы подтверждаете?'


async def about_worker(
        user_id: int,
        rating: str
) -> str:
    user_rating = await db.get_user_rating(user_id=user_id)
    if not user_rating:
        await db.set_rating(user_id=user_id)
        user_rating = await db.get_user_rating(user_id=user_id)

    user = await db.get_user_by_id(user_id=user_id)
    user_real = await db.get_user_real_data_by_id(user_id=user_id)

    return f'<blockquote><b>📱 Телефон из реестра:</b> {user.phone_number}\n' \
           f'<b>👤 ФИО из реестра:</b>' \
           f'\n{user.last_name} {user.first_name} {user.middle_name}\n' \
           f'<b>📞 Актуальный телефон:</b> {user_real.phone_number}\n' \
           f'<b>👤 Актуальное ФИО:</b>' \
           f'\n{user_real.last_name} {user_real.first_name} {user_real.middle_name}\n' \
           f'<b>💳 Карта:</b> {user.card if user.card else "Отсутствует"}\n' \
           f'<b>🪙 Начислено:</b> {user.balance if user.balance else "0"}₽\n' \
           f'<b>📍 Локация:</b> {user.city}\n' \
           f'<b>📊 Рейтинг:</b> ~{rating}\n' \
           f'📨 Подано заявок: {user_rating.total_orders}\n' \
           f'✅ Услуги оказаны по {user_rating.successful_orders} заявкам.</blockquote>'


def foreman_applications_menu() -> str:
    return 'ℹ️ В этом разделе вы можете посмотреть список исполнителей, ' \
           'которые откликнулись на заявку:'


def foreman_pdf_info() -> str:
    return 'ℹ️ PDF с исполнителями скоро будет сформирован'


def foreman_no_order_applications() -> str:
    return 'ℹ️ К этой заявке нет откликов'


def update_worker_info() -> str:
    return 'ℹ️ Выберите, что хотите обновить:'


def request_new_card() -> str:
    return '💳 Введите новый номер карты:'


def same_card_error() -> str:
    return '❗Новая карта должна отличаться от старой. Попробуйте ещё раз:'


def bank_card_updated() -> str:
    return '✅ Карта была успешно обновлена'


def no_worker() -> str:
    return '❗ Вы не зарегистрированы. Используйте /start для регистрации.'


def erase_worker_info_warning() -> str:
    return "⚖️ Внимание!\n\n" \
           "В соответствии с Федеральным законом № 152-ФЗ «О персональных данных», " \
           "Вы инициируете удаление своих персональных данных из Платформы.\n\n" \
           "<b>Будут удалены:</b>\n" \
           "<blockquote>👤 Фамилия, имя, отчество\n" \
           "📱 Номер телефона\n" \
           "💬 Telegram ID</blockquote>\n\n" \
           "❗️При этом в Платформе сохраняются обезличенные и обязательные к хранению сведения:\n" \
           "📁 История ранее принятых и оказанных услуг\n" \
           "⭐ Показатель рейтинга\n\n" \
           "Эти сведения сохраняются исключительно для исполнения и подтверждения гражданско-правовых обязательств перед Получателями услуг, а также для проведения проверок и сверок в рамках Федерального закона № 422-ФЗ «О налоге на профессиональный доход».\n\n" \
           "Сохранение указанных сведений:\n" \
            "— не предоставляет доступ к функционалу Платформы;\n" \
            "— не означает наличие трудовых отношений;\n" \
            "— не препятствует удалению персональных данных.\n\n" \
            "Вы подтверждаете удаление персональных данных?\n"


def worker_data_erased() -> str:
    return "<b>✅ Профиль деактивирован.</b>\n\n" \
           "Вы прекратили использование Платформы и инициировали удаление своих данных.\n\n" \
           "В Платформе сохранены только сведения, которые подлежат хранению в соответствии с требованиями законодательства РФ и условиями ранее заключённых гражданско-правовых договоров:\n\n" \
           "📁 История оказанных услуг\n" \
           "⭐ Показатель рейтинга\n\n" \
           "Указанные сведения используются исключительно для исполнения прав и обязанностей сторон по заключённым договорам и не предоставляют доступ к функционалу Платформы.\n\n" \
           "Для повторного использования Платформы вы можете пройти регистрацию заново на этом или другом устройстве."


def user_deleted() -> str:
    return '<b>⚠️ Ваш профиль был удалён администратором.</b>\n\n' \
           'Все ваши отклики, записи и история <b>удалены</b>. ' \
           'Чтобы снова пользоваться платформой, пройдите <b>регистрацию с самого начала</b>.'


def user_tg_id_erased() -> str:
    return '<b>📲 Ваш Telegram-аккаунт отвязан от платформы.</b>\n\n' \
           'Ваши отклики, записи и история <b>сохранились</b>.' \
           'Теперь вы можете заново войти с <b>этого или другого устройства</b> — ' \
           'просто выберите локацию и введите свой номер телефона.'


def user_rating_erased() -> str:
    return 'ℹ️ Ваш новый рейтинг 100%, сейчас он был обнулен менеджером Платформы.'


def foreman_delete_order_worker_notification(
        worker_full_name: str,
        phone_number: str,
        city: str,
        customer: str,
        job_name: str,
        date: str,
        day_shift: str,
        night_shift: str
) -> str:
    time = day_shift if day_shift else night_shift
    return '❗️ <b>Исполнитель отказался от оказания услуг по ранее принятой заявке</b>\n\n' \
           f'👤 <b>Исполнитель:</b> {worker_full_name}, {phone_number}\n' \
           'Исполнитель отказался от выполнения услуг в статусе «Оказание услуг» по вашей заявке.\n\n' \
           '<b>Заявка:</b>\n' \
           f'<blockquote><b>📍 Город:</b> {city}\n' \
           f'<b>👥 Получатель услуг:</b> {customer}\n' \
           f'<b>💼 Услуга:</b> {job_name}\n' \
           f'<b>📅 Дата и время:</b> {date} | {time}</blockquote>\n\n' \
           '⚠️ Заявка возвращена в раздел «Подбор исполнителей».\n\n' \
           '💬 Если у вас есть кто-то на примете (в запасе), можете порекомендовать ему взять данную заявку.'


def user_notification_for_add_to_order_workers(
        order: db.Order,
        customer: str,
        worker_full_name: str,        day: str
) -> str:
    time = order.day_shift if order.day_shift else order.night_shift
    shift = '<b>ДЕНЬ</b>' if order.day_shift else '<b>НОЧЬ</b>'
    return f'👤 Уважаемый <b>{worker_full_name}</b>!\n\n' \
           'ℹ️ Решением менеджера и представителем Исполнителя, с Вашего устного согласия, ' \
           'за Вас взята Заявка:\n' \
           f"<blockquote><b>📍 Город:</b> {order.city}\n" \
           f"<b>👥 Получатель услуг:</b> {customer}\n" \
           f"<b>💼 Услуга:</b> {order.job_name}\n" \
           f"<b>🗓️ Дата:</b> {order.date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💵 Оплата:</b> {order.amount}₽</blockquote>\n\n" \
           '<b>Если вы не согласны участвовать:</b>\n' \
           '1️⃣ Зайдите в раздел <b>“Работа с заявками”</b>.\n' \
           '2️⃣ Найдите эту Заявку и выберите <b>“Отказаться”</b>.\n' \
           '✅ Важно: Отказ на данную Заявку <b>не повлияет</b> на ваш рейтинг, ' \
           'не влечет договорных компенсаций или других последствий.'


def order_for_friend_confirmation() -> str:
    return '<blockquote>⚠️ Вы оформляете заявку для другого исполнителя (НПД), ' \
           'зарегистрированного и подписавшего договор с платформой.\n' \
           'Согласно п. 2 ст. 6 ФЗ №422-ФЗ, самозанятые обязаны оказывать услуги лично.\n' \
           'Оформление заявки возможно только с согласия друга и при его регистрации в НПД.\n' \
           'Передача данных без согласия или несанкционированный доступ к чужому телефону ' \
           'нарушает ст. 6 и ст. 9 ФЗ №152-ФЗ «О персональных данных».\n' \
           'Убедитесь, что вы получили согласие друга на использование его данных.\n' \
           'Все действия логируются. При злоупотреблениях доступ к функции может быть ' \
           'ограничен согласно правилам платформы.</blockquote>'


def choose_method_search_friend() -> str:
    return 'Выберите способ, как найти друга:'


def request_worker_phone_number() -> str:
    return '📞 Введите номер телефона исполнителя (НПД):'


def request_worker_inn() -> str:
    return '🪪 Введите ИНН исполнителя (НПД):'


def worker_search() -> str:
    return '🔍 Ищем исполнителя (НПД)'


def order_for_friend_worker_not_found() -> str:
    return '❌ Исполнитель не подписал Договор. Предложите ему пройти регистрацию'


def choose_friend_city() -> str:
    return '🌆 Выберите город вашего друга, в котором он будет оказывать услуги:'


def request_code_for_order(
        first_name: str,
        middle_name: str,
        last_name: str
) -> str:
    return f'🆔 Введите код, отправленный исполнителю (НПД) ' \
           f'<b>{first_name} {last_name[:1]}.{middle_name[:1]}.</b> ' \
           f'на номер телефона:'


def code_text_for_message(
        code: str
) -> str:
    return f'[Алгоритм Плюс] Код {code} для подтверждения заявки'


def code_for_order_error():
    return f'❗Введен неверный код. Введите его еще раз:'


def code_for_order_attempts_error():
    return f'ℹ️ Код введен неверно слишком много раз. Попробуйте заново записать друга'


def too_many_attempts_for_code() -> str:
    return '❗Превышен лимит отправки кода для этого исполнителя (НПД). Попробуйте завтра'


def the_code_has_expired_error() -> str:
    return 'ℹ️ Срок действия кода истек. Попробуйте заново'


async def confirmation_respond_for_friend(
        order_id: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        amount: str
) -> str:
    order = await db.get_order(
        order_id=order_id
    )
    dt_obj = datetime.strptime(order.date, '%d.%m.%Y')
    week = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']

    time = order.day_shift if order.day_shift else order.night_shift
    shift = '<b>ДЕНЬ</b>' if order.day_shift else '<b>НОЧЬ</b>'
    organization = await db.get_customer_organization(order.customer_id)

    return f'✅ Данные друга подтверждены. Вы записываете исполнителя (НПД) ' \
           f'<b>{first_name} {last_name[:1]}.{middle_name[:1]}</b>. на заявку:\n' \
           f"<blockquote><b>📍 Город:</b> {order.city}\n" \
           f"<b>👥 Получатель услуг:</b> {organization}\n" \
           f"<b>💼 Услуга:</b> {order.job_name}\n" \
           f"<b>🗓️ Дата:</b> {order.date}\n" \
           f"<b>                  {week[dt_obj.weekday()]}</b>\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💵 Оплата:</b> {amount}₽</blockquote>\n" \
           'Согласно п. 2 ст. 6 ФЗ №422-ФЗ, он несет ответственность за выполнение заявки.\n' \
           'Если друг не выйдет на заявку, его рейтинг будет снижен.\n' \
           'При злоупотреблениях доступ к функции может быть ограничен согласно правилам платформы.\n' \
           'Финансовая ответственность не применяется (ст. 307 ГК РФ).'


def cancel_respond_order_for_friend() -> str:
    return 'ℹ️ Запись друга на заявку отменена'


def choose_customer() -> str:
    return '🏢 Выберите нужного получателя услуг:'


def supervisor_orders_info():
    return f"<b>ℹ️ Выберите нужную заявку</b>\n\n" \
           "Когда | Одобрено | Заявка | Откликов"


def supervisor_no_orders() -> str:
    return 'ℹ️ У этого получателя услуг в данный момент нет ни одной заявки'


def supervisor_order_actions() -> str:
    return 'ℹ️ Выберите действие для этой заявки'


def supervisor_applications() -> str:
    return 'ℹ️ Список исполнителей, откликнувшихся на заявку, открыт\n\n' \
           'Исполнитель | Рейтинг'


def supervisor_no_applications() -> str:
    return 'ℹ️ На этой заявке еще нет откликов'


def supervisor_no_order_workers() -> str:
    return 'ℹ️ На этой заявке еще нет одобренных исполнителей'


def supervisor_confirmation_add_order_worker(
        full_name: str
) -> str:
    return f'Добавить нового исполнителя <b>{full_name}</b> на эту заявку?'


def supervisor_worker_added() -> str:
    return '✅ Исполнитель успешно добавлен'


def supervisor_add_worker_error() -> str:
    return '❗Не удалось добавить исполнителя'


def supervisor_notification_for_add_to_order_workers(
        order: db.Order,
        customer: str,
        worker_full_name: str,
        day: str
) -> str:
    time = order.day_shift if order.day_shift else order.night_shift
    shift = '<b>ДЕНЬ</b>' if order.day_shift else '<b>НОЧЬ</b>'
    return f'👤 Уважаемый <b>{worker_full_name}</b>!\n\n' \
           'ℹ️ Супервайзером, с Вашего устного согласия, за Вас взят Заказ:\n' \
           f"<blockquote><b>📍 Город:</b> {order.city}\n" \
           f"<b>👥 Заказчик:</b> {customer}\n" \
           f"<b>💼 Услуга:</b> {order.job_name}\n" \
           f"<b>🗓️ Дата:</b> {order.date}\n" \
           f"<b>                  {day}</b>\n" \
           f"<b>🕒 Время:</b> {time}\n" \
           f"                      {shift}\n" \
           f"<b>💵 Оплата:</b> {order.amount}₽</blockquote>\n\n" \
           '<b>Если вы не согласны со взятым заказом:</b>\n' \
           '1️⃣ Зайдите в раздел <b>“Работа с заказом”</b>.\n' \
           '2️⃣ Найдите этот Заказ и выберите <b>“Отказаться”</b>.\n' \
           '✅ Важно: Отказ на данный Заказ <b>не повлияет</b> на ваш рейтинг, ' \
           'не влечет договорных компенсаций или других последствий.'


def payment_notification(
        order_date: str,
        order_shift: str,
        customer: str,
        order_amount: str,
) -> str:
    return ('⏳ В случае бездействия, пакет документов будет автоматически подписан через 10 минут\n'
            f'Заказ: {order_date} | {order_shift} | {customer}\n'
            f'Вам начислена выплата: {order_amount}₽\n'
            'Получить её сейчас?')


def wallet_payment_notification(
        amount: str,
        card: str,
) -> str:
    return (f'<b>Выплата в обработке 💳</b>\n'
            f'Вознаграждение {amount}₽ будет отправлено на карту {card} через партнёра ООО «Рабочие руки».\n'
            f'Поступление — до 10 минут.')


def payment_sent_to_balance() -> str:
    return '✅ Выплата начислена успешно на ваш баланс'


def update_worker_balance_error() -> str:
    return '❗Произошла неизвестная ошибка'


def request_worker_pin_code() -> str:
    return 'Введите 4 последние цифры вашего ИНН:'


def wait_payment() -> str:
    return 'ℹ️ Ожидайте, выплата скоро будет начислена'


def payment_paid() -> str:
    return '✅ Выплата успешно начислена'


def payment_error_it_sent_to_balance() -> str:
    return 'ℹ️ Не удалось сделать выплату. Она была начислена на ваш баланс'


def payment_stopped_no_card() -> str:
    return (
        '⚠️ Выплата не отправлена\n\n'
        'В системе отсутствует способ получения выплаты.\n\n'
        'Пожалуйста, укажите данные:\n'
        'Меню → Старт → Обо мне → Обновить данные → Банковская карта\n\n'
        '💰 Средства уже зачислены в «Начисления»'
    )


def payment_stopped_conflict() -> str:
    return (
        '⚠️ Выплата не отправлена\n\n'
        'Обнаружено расхождение платёжных данных.\n\n'
        'Пожалуйста, обновите данные:\n'
        'Меню → Обо мне → Банковская карта\n\n'
        '💰 Средства зачислены в «Начисления»'
    )


def payment_stopped_rr_unavailable() -> str:
    return (
        '⚠️ Выплата не отправлена\n\n'
        'Не удалось проверить платёжные данные в «Рабочих руках».\n\n'
        '💰 Средства зачислены в «Начисления»\n\n'
        'Если данные карты у вас уже заполнены, повторите попытку позже.'
    )


def payment_not_paid_critical_error(
        payment_id: int,
        is_wallet_payment: bool = False,
) -> str:
    return f'❗Не удалось совершить выплату {"из кошелька" if is_wallet_payment else ""}(№{payment_id})'


def low_balance_error() -> str:
    return (
        '❗️ Сумма начисленного вознаграждения, доступного к выплате, менее 2600 ₽.\n'
        'Формирование выплаты временно невозможно.'
    )


def request_amount_for_payment() -> str:
    return 'ℹ️ Введите сумму для вывода:'


def go_to_rr_warning() -> str:
    return ("📢 <b>Уважаемые коллеги!</b>\n\n"
            "С <b>1 января 2026</b> года выплаты на Платформе «Алгоритм Плюс» осуществляются через партнёра <b>ООО «Рабочие Руки»</b>.\n\n"
            "Для получения вознаграждения необходимо:\n"
            "1️⃣ Ввести в боте <b>ИНН, номер банковской карты</b> для получения выплат и <b>номер телефона</b>.\n"
            "2️⃣ Подождать 3–5 минут.\n"
            "3️⃣ Зайти в приложение <b>«Мой налог»</b>:\n"
            "правый нижний угол → <b>…Прочее</b> → <b>Партнёры</b>.\n"
            "4️⃣ Вверху появится запрос от <b>«Рабочие Руки»</b> — <b>подключите партнёра</b>.\n\n"
            "✅ После подключения выплаты будут поступать <b>на указанную вами карту</b>.")


# ========== Уведомления о дополнительном вознаграждении ==========

def premium_unconditional_notification(bonus_amount: str) -> str:
    """Уведомление о безусловном дополнительном вознаграждении"""
    return (
        "🎉 Вы закреплены за данным Получателем услуг.\n"
        f"💰 К вашему начислению добавлено дополнительное вознаграждение: <b>+{bonus_amount} ₽</b>"
    )


def premium_conditional_notification(completion_percent: str, bonus_amount: str) -> str:
    """Уведомление об условном дополнительном вознаграждении"""
    return (
        "📊 Заявка закрыта.\n"
        "🎉 Вы закреплены за данным Получателем услуг.\n"
        f"✅ Фактическое исполнение Заявки: <b>{completion_percent}%</b>.\n"
        f"💰 Размер дополнительного вознаграждения: <b>{bonus_amount} ₽</b>."
    )


# --- SMS-верификация телефона ---

def phone_verify_call_block() -> str:
    return (
        "📲 <b>Подтверждение номера телефона</b>\n\n"
        "Чтобы взять заявку, введите <b>ваш действующий номер телефона</b>, который сейчас у вас в руках.\n"
        "На него придёт <b>SMS с кодом.</b>\n\n"
        "🔐 Введите код в чат — после этого доступ к заявкам автоматически восстановится.\n\n"
        "⚠️ Ограничение введено, так как мы не смогли с вами связаться (не ответили или телефон был недоступен).\n"
        "Проводим актуализацию номера для подтверждения связи и выплат.\n\n"
        "📌 Формат ввода любой:\n"
        "8903… / 903… / 7903… / +7903…\n\n"
        "Введите номер ниже 👇"
    )


def phone_verify_regular() -> str:
    return (
        "📱 <b>Подтверждение номера телефона</b>\n\n"
        "Для продолжения работы с заявками актуализируйте свои данные: "
        "введите ваш номер телефона. Вам будет отправлен SMS-код для подтверждения."
    )


def phone_verify_enter_phone() -> str:
    return "📞 Введите ваш номер телефона (например, 79991234567):"


def phone_verify_sms_sent(phone: str) -> str:
    return (
        f"📨 SMS с кодом подтверждения отправлен на номер <b>{phone}</b>.\n\n"
        "Введите 4-значный код из SMS:"
    )


def phone_verify_code_error() -> str:
    return "❗ Неверный код. Попробуйте ещё раз или введите номер телефона заново:"


def phone_verify_success() -> str:
    return "✅ Номер телефона успешно подтверждён!"


def phone_verify_phone_error() -> str:
    return "❗ Неверный формат номера. Введите номер в формате 79991234567:"


def contracts_sending_info() -> str:
    return "ℹ️ Договоры скоро будут отправлены"


def contracts_sending_error() -> str:
    return "⌛ Договоры уже отправляются"


def contract_required_for_order() -> str:
    return (
        '📄 <b>Для отклика на заявку необходимо подписать договор.</b>\n\n'
        'Ознакомьтесь с документом выше и введите <b>4 последние цифры вашего ИНН</b> для подписания.\n\n'
        'Введите цифры:'
    )


def contract_signed_proceed() -> str:
    return '✅ Договор подписан. Ваш отклик отправлен!'


def contract_reject_order() -> str:
    return 'ℹ️ Подписание отменено. Отклик не отправлен.'


def extra_worker_notification_with_compensation(amount: int) -> str:
    """Уведомление исполнителю EXTRA с компенсацией"""
    return (
        "💰 <b>Начислена компенсация</b>\n\n"
        "Вы прибыли на объект, однако оказались сверх лимита заявки по техническим причинам Платформы.\n\n"
        f"В качестве компенсации Платформы за понесённые транспортные расходы вам начислено <b>{amount} ₽</b>.\n"
        "Сумма зачислена в ваш кошелёк и станет доступна к выводу после достижения общего баланса 2 600 ₽.\n\n"
        "📈 В качестве бонуса к рейтингу вам дополнительно начислено <b>+1%</b>.\n\n"
        "Приносим извинения за доставленные неудобства и благодарим за ваш выход 🤝"
    )


def extra_worker_notification_without_compensation() -> str:
    """Уведомление исполнителю EXTRA без компенсации"""
    return (
        "ℹ️ <b>Информация по заказу</b>\n\n"
        "Вы прибыли на объект, однако оказались сверх лимита заявки по техническим причинам Платформы.\n"
        "Приносим извинения за доставленные неудобства.\n\n"
        "📈 В качестве бонуса к рейтингу вам дополнительно начислено <b>+1%</b>.\n\n"
        "Спасибо за ваш выход и ответственность 🤝"
    )

def request_help_text() -> str:
    return (
        "🆘 СВЯЗЬ С РУКОВОДСТВОМ 🆘\n\n"
        "Здесь вы можете обратиться напрямую\n"
        "к руководству платформы «Алгоритм Плюс».\n\n"
        "Вы можете написать по ЛЮБЫМ вопросам:\n"
        "— выплаты и деньги\n"
        "— документы и договор\n"
        "— заказы и смены\n"
        "— жалобы и просьбы\n"
        "— обжалование удержаний и решений платформы\n"
        "— спорные ситуации на объекте Заказчика\n"
        "— любые сомнения и проблемы\n\n"
        "✍️ Просто напишите сообщение и отправьте его.\n"
        "📎 Затем при необходимости приложите фото или файл.\n\n"
        "Ваше обращение будет рассмотрено руководством платформы.\n"
        "Связь с вами осуществляется по телефону,\n"
        "указанному при подписании договора.\n"
    )


def request_help_files_or_photos() -> str:
    return 'ℹ️ Теперь отправьте по очереди до трех файлов/фото или нажмите на кнопку "Пропустить":'


def help_photo_saved(
        request_more: bool = True,
) -> str:
    txt = '. Отправьте еще файл/фото или нажмите на кнопку "Пропустить":' if request_more else ''
    return f'✅ Фото добавлено{txt}'


def help_file_saved(
        request_more: bool = True,
) -> str:
    txt = '. Отправьте еще файл/фото или нажмите на кнопку "Пропустить":' if request_more else ''
    return f'✅ Файл добавлен{txt}'


def confirmation_send_help_message() -> str:
    return 'ℹ️ Отправить обращение?'


def sending_help_message() -> str:
    return 'ℹ️ Ваше обращение отправляется'


def cancel_send_help_message() -> str:
    return 'ℹ️ Отправка обращения отменена'


def help_message_to_group(
        real_full_name: str,
        real_phone_number: str,
        tg_id: int,
        max_id: int,
        city: str,
        total_orders: int,
        successful_orders: int,
        rating: str,
        help_text: str,
) -> str:
    date = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M")
    return (
        f"🆘 <b>ОБРАЩЕНИЕ ИСПОЛНИТЕЛЯ</b> 🆘\n\n"
        f"👤 <b>ФИО:</b> {real_full_name}\n"
        f"📞 <b>Телефон:</b> {real_phone_number}\n"
        f"🆔 <b>Telegram ID:</b> {tg_id}\n"
        f"🆔 <b>Max ID:</b> {max_id}\n\n"
        f"📍 <b>Город заказов:</b> {city}\n\n"
        f"📦 <b>Взято заказов:</b> {total_orders}\n"
        f"✅ <b>Успешно выполнено:</b> {successful_orders}\n"
        f"⭐️ <b>Рейтинг:</b> {rating}\n\n"
        f"💬 <b>Сообщение:</b>\n"
        f"<blockquote>{help_text}</blockquote>\n\n"
        f"🕒 <b>Дата и время:</b> {date}\n"
    )


def help_message_caption(
        full_name: str,
) -> str:
    return f'📎 Вложение от исполнителя <b>{full_name}</b>'


def help_message_sent() -> str:
    return (
        '✅ Ваше обращение направлено руководству платформы.\n\n'
        'Связь с вами будет осуществлена по телефону, указанному при регистрации.'
    )


def send_help_message_error() -> str:
    return '❗Не удалось отправить обращение'


def help_request_limit_reached() -> str:
    return (
        '⚠️ Лимит обращений исчерпан.\n\n'
        'Вы можете отправить не более 4 обращений в сутки.\n'
        'Следующее обращение будет доступно позже.'
    )


# ── Акты выполненных работ ─────────────────────────────────────────────────────

def act_sign_request(amount: str, date: str, pin_hint: str) -> str:
    return (
        f'📋 <b>Акт</b>\n\n'
        f'💰 Вознаграждение: <b>{amount} ₽</b>\n'
        f'📅 Дата акта: <b>{date}</b>\n\n'
        f'Ознакомьтесь с актом и подпишите его, введя {pin_hint}.\n\n'
        f'⏳ Если в течение 10 минут вы не заявите возражений, акт будет считаться подписанным автоматически.'
    )


def act_signed() -> str:
    return '✅ Акт подписан'


def act_auto_signed() -> str:
    return '✅ Акт считается подписанным автоматически'


def act_refused() -> str:
    return 'ℹ️ Вы отказались от подписания акта. Вознаграждение переведено в «Начисления».'


def act_sign_pin_error() -> str:
    return '❗ Неверный код. Попробуйте ещё раз:'


def act_accrual_notification() -> str:
    return (
        'Уведомление\n\n'
        'Вам начислено вознаграждение за оказанные услуги.\n\n'
        '👉 Обо мне → Выплаты → Акт\n\n'
        'Если в течение 10 минут вы не заявите возражений, акт будет считаться подписанным автоматически.'
    )


# ── Чеки из «Мой налог» ────────────────────────────────────────────────────────

def receipt_instruction() -> str:
    return (
        'Для получения выплаты оформите чек в приложении «Мой налог».\n\n'
        '👉 Обо мне → Выплаты → Чеки\n'
        '1. Откройте «Мой налог»\n'
        '2. Нажмите «Продажа»\n'
        '3. Вставьте услугу\n'
        '4. Вставьте сумму\n'
        '5. Выберите «ЮЛ/ИП»\n'
        '6. Вставьте ИНН\n'
        '7. Нажмите «Выдать чек»\n'
        '8. Нажмите отправить и скопируйте ссылку, передайте её нам, нажав на «Отправить ссылку»\n'
        '9. Или сделайте скрин чека и нажмите «Отправить скриншот»\n\n'
        'После этого:\n'
        '👉 отправьте ссылку\n'
        'или\n'
        '👉 отправьте скриншот\n\n'
        'Услуга:\n<code>{service_name}</code>\n\n'
        'Сумма:\n<code>{amount} ₽</code>\n\n'
        'ИНН:\n<code>{inn}</code>'
    )


def receipt_instruction_no_copy(service_name: str, inn: str, amount: str) -> str:
    return (
        'Для получения выплаты оформите чек в приложении «Мой налог».\n\n'
        '👉 Обо мне → Выплаты → Чеки\n'
        '1. Откройте «Мой налог»\n'
        '2. Нажмите «Продажа»\n'
        '3. Вставьте услугу\n'
        '4. Вставьте сумму\n'
        '5. Выберите «ЮЛ/ИП»\n'
        '6. Вставьте ИНН\n'
        '7. Нажмите «Выдать чек»\n'
        '8. Отправьте нам ссылку на чек\n'
        '9. Или отправьте скриншот чека\n\n'
        'Услуга:\n<code>{service_name}</code>\n\n'
        'Сумма:\n<code>{amount} ₽</code>\n\n'
        'ИНН:\n<code>{inn}</code>'
    ).format(amount=amount, service_name=service_name, inn=inn)


def request_receipt_url() -> str:
    return (
        '🧾 <b>Передайте чек</b>\n\n'
        'Отправьте ссылку на чек из «Мой налог» или скриншот/фото QR-кода.'
    )


def receipt_url_invalid() -> str:
    return '❗ Ссылка не похожа на чек из «Мой налог». Пожалуйста, проверьте и попробуйте снова:'


def receipt_qr_not_found() -> str:
    return (
        '❗ QR-код на фото не обнаружен.\n\n'
        'Попробуйте сделать более чёткий скриншот или отправьте ссылку текстом:'
    )


def receipt_qr_invalid() -> str:
    return (
        '❗ QR-код не содержит ссылку на чек из «Мой налог».\n\n'
        'Убедитесь, что это QR именно с чека в приложении, или отправьте ссылку текстом:'
    )


def receipt_saved() -> str:
    return '✅ Ссылка на чек принята'


def receipt_saved_for_review() -> str:
    return (
        '✅ Чек получен.\n\n'
        'Кассир проверит ИНН, сумму, услугу и плательщика.\n'
        'После проверки выплата будет отправлена в «Рабочие руки».'
    )


def receipt_rejected() -> str:
    return (
        '⚠️ Ваш чек отклонён.\n'
        'Предоставьте новый после аннулирования.'
    )
