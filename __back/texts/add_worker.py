def request_last_name() -> str:
    """Запрос фамилии"""
    return '👤 <b>Шаг 1 из 10: Фамилия</b>\n\n' \
           'Введите фамилию исполнителя:'


def request_first_name() -> str:
    """Запрос имени"""
    return '👤 <b>Шаг 2 из 10: Имя</b>\n\n' \
           'Введите имя исполнителя:'


def request_middle_name() -> str:
    """Запрос отчества"""
    return '👤 <b>Шаг 3 из 10: Отчество</b>\n\n' \
           'Введите отчество исполнителя или нажмите кнопку "Пропустить", если отчества нет:'


def request_inn() -> str:
    """Запрос ИНН"""
    return '🪪 <b>Шаг 4 из 10: ИНН</b>\n\n' \
           'Введите ИНН исполнителя (12 цифр) или нажмите "Пропустить":\n\n' \
           'ℹ️ <i>ИНН необязателен, но если он указан, должен состоять из 12 цифр</i>'


def inn_validation_error() -> str:
    """Ошибка валидации ИНН"""
    return '❗<b>ИНН должен состоять из 12 цифр</b>\n\n' \
           'Попробуйте еще раз или нажмите "Пропустить":'


def inn_already_registered_rr() -> str:
    """ИНН уже есть в глобальной базе РР"""
    return '❗ Ваш ИНН уже есть в глобальной базе «Рабочие Руки»\n\n' \
           '👉 Для продолжения обратитесь в службу поддержки\n\n' \
           'Введите другой ИНН или нажмите "Пропустить":'


def inn_already_exists_platform() -> str:
    """ИНН уже есть на платформе (в локальной БД)"""
    return '❗ С таким ИНН уже есть исполнитель на платформе\n\n' \
           '👉 Скажите ему пусть воспользуется функцией «Войти»\n\n' \
           'Введите другой ИНН или нажмите "Пропустить":'


def request_phone_number() -> str:
    """Запрос номера телефона"""
    return '📱 <b>Шаг 5 из 10: Номер телефона</b>\n\n' \
           'Введите номер телефона исполнителя или нажмите "Пропустить":\n\n' \
           'ℹ️ <i>Можно вводить в любом формате:\n' \
           '• 89031234567\n' \
           '• 79031234567\n' \
           '• 9031234567\n' \
           '• 8 (903) 123-45-67\n\n' \
           'Система автоматически приведет номер к нужному формату</i>'


def phone_already_registered() -> str:
    """Телефон уже зарегистрирован"""
    return '❗ Такой номер телефона уже зарегистрирован\n\n' \
           '👉 Введите другой номер телефона или Исполнитель прямо сейчас может «Войти» на Платформу\n\n' \
           'Введите другой телефон или нажмите "Пропустить":'


def phone_incomplete_warning(phone: str) -> str:
    """Предупреждение о неполном номере телефона"""
    return f'⚠️ <b>Номер телефона неполный</b>\n\n' \
           f'Введенный номер: <code>{phone}</code>\n\n' \
           f'Данные все равно будут сохранены, но отправка в "Рабочие Руки" не произойдет.\n' \
           f'Продолжаем?'


def request_card_number() -> str:
    """Запрос номера карты"""
    return '💳 <b>Шаг 6 из 10: Номер карты</b>\n\n' \
           'Введите номер банковской карты исполнителя (16 цифр) или нажмите "Пропустить":'


def card_number_validation_error() -> str:
    """Ошибка валидации номера карты"""
    return '❗<b>Номер карты должен состоять из 16 цифр</b>\n\n' \
           'Попробуйте еще раз или нажмите "Пропустить":'


def card_already_used() -> str:
    """Карта уже используется другим исполнителем"""
    return '❗ Такой номер карты уже есть у другого исполнителя\n\n' \
           '👉 Запросите другой номер карты (уникальный)\n\n' \
           'Введите другой номер карты или нажмите "Пропустить":'


def request_birthday() -> str:
    """Запрос даты рождения"""
    return '🎂 <b>Шаг 7 из 10: Дата рождения</b>\n\n' \
           'Введите дату рождения исполнителя в формате <b>ДД.ММ.ГГГГ</b> или нажмите "Пропустить":\n\n' \
           'ℹ️ <i>Например: 15.03.1990</i>'


def birthday_validation_error() -> str:
    """Ошибка валидации даты рождения"""
    return '❗<b>Неверный формат даты</b>\n\n' \
           'Введите дату в формате <b>ДД.ММ.ГГГГ</b> (например: 15.03.1990)\n\n' \
           'Попробуйте еще раз или нажмите "Пропустить":'


def request_passport_series() -> str:
    """Запрос серии паспорта"""
    return '🪪 <b>Шаг 8 из 10: Серия паспорта</b>\n\n' \
           'Введите серию паспорта (4 цифры, например: <b>4515</b>) или нажмите "Пропустить паспорт":'


def passport_series_validation_error() -> str:
    """Ошибка валидации серии паспорта"""
    return '❗<b>Серия паспорта должна состоять из 4 цифр</b>\n\n' \
           'Попробуйте еще раз или нажмите "Пропустить паспорт":'


def request_passport_number() -> str:
    """Запрос номера паспорта"""
    return '🪪 <b>Шаг 9 из 10: Номер паспорта</b>\n\n' \
           'Введите номер паспорта (6 цифр, например: <b>123456</b>):'


def passport_number_validation_error() -> str:
    """Ошибка валидации номера паспорта"""
    return '❗<b>Номер паспорта должен состоять из 6 цифр</b>\n\n' \
           'Попробуйте еще раз:'


def request_passport_date() -> str:
    """Запрос даты выдачи паспорта"""
    return '🪪 <b>Шаг 10 из 10: Дата выдачи паспорта</b>\n\n' \
           'Введите дату выдачи паспорта в формате <b>ДД.ММ.ГГГГ</b>:\n\n' \
           'ℹ️ <i>Например: 20.05.2015</i>'


def passport_date_validation_error() -> str:
    """Ошибка валидации даты выдачи паспорта"""
    return '❗<b>Неверный формат даты</b>\n\n' \
           'Введите дату в формате <b>ДД.ММ.ГГГГ</b> (например: 20.05.2015)\n\n' \
           'Попробуйте еще раз:'


def request_telegram_id() -> str:
    """Запрос Telegram ID"""
    return '💬 <b>Дополнительно: Telegram ID</b>\n\n' \
           'Введите Telegram ID исполнителя или нажмите "Пропустить":\n\n' \
           'ℹ️ <i>Telegram ID необязателен, но позволит исполнителю ' \
           'пользоваться платформой без номера телефона</i>'


def telegram_id_validation_error() -> str:
    """Ошибка валидации Telegram ID"""
    return '❗<b>Telegram ID должен быть числом</b>\n\n' \
           'Попробуйте еще раз или нажмите "Пропустить":'


def confirm_worker_data(
        last_name: str,
        first_name: str,
        middle_name: str,
        inn: str,
        phone_number: str,
        card_number: str,
        telegram_id: str,
        birthday: str = '',
        passport_series: str = '',
        passport_number: str = '',
        passport_date: str = '',
) -> str:
    """Подтверждение данных самозанятого перед сохранением"""
    middle_name_text = middle_name if middle_name else '<i>не указано</i>'
    inn_text = inn if inn else '<i>не указан</i>'
    phone_text = phone_number if phone_number else '<i>не указан</i>'
    card_text = card_number if card_number else '<i>не указан</i>'
    tg_id_text = telegram_id if telegram_id else '<i>не указан</i>'
    birthday_text = birthday if birthday else '<i>не указана</i>'

    has_passport = passport_series and passport_number and passport_date
    if has_passport:
        passport_text = f'{passport_series} {passport_number}, выдан {passport_date}'
    elif passport_series or passport_number or passport_date:
        parts = []
        if passport_series:
            parts.append(f'серия {passport_series}')
        if passport_number:
            parts.append(f'номер {passport_number}')
        if passport_date:
            parts.append(f'выдан {passport_date}')
        passport_text = ', '.join(parts)
    else:
        passport_text = '<i>не указан</i>'

    is_valid_phone = phone_number and len(phone_number) == 12 and phone_number.startswith('+7')

    text = '✅ <b>Проверьте данные перед сохранением:</b>\n\n' \
           f'👤 <b>Фамилия:</b> {last_name}\n' \
           f'👤 <b>Имя:</b> {first_name}\n' \
           f'👤 <b>Отчество:</b> {middle_name_text}\n' \
           f'🪪 <b>ИНН:</b> {inn_text}\n' \
           f'📱 <b>Телефон:</b> {phone_text}\n' \
           f'💳 <b>Номер карты:</b> {card_text}\n' \
           f'🎂 <b>Дата рождения:</b> {birthday_text}\n' \
           f'🪪 <b>Паспорт:</b> {passport_text}\n' \
           f'💬 <b>Telegram ID:</b> {tg_id_text}\n\n'

    if inn and is_valid_phone:
        text += '🔄 <b>Данные будут отправлены в "Рабочие Руки"</b>\n' \
                '✅ Указан ИНН и корректный номер телефона\n\n'
    else:
        text += 'ℹ️ <b>Данные НЕ будут отправлены в "Рабочие Руки"</b>\n'
        if not inn:
            text += '• Не указан ИНН\n'
        if not is_valid_phone:
            text += '• Телефон неполный или не указан\n'
        text += '\n'

    if phone_number or telegram_id:
        text += '✅ <b>Исполнитель сможет пользоваться платформой</b>\n'
        if phone_number:
            text += '• Указан номер телефона\n'
        if telegram_id:
            text += '• Указан Telegram ID\n'
    else:
        text += 'ℹ️ <b>Исполнитель будет доступен только для ручного назначения</b>\n' \
                '• Не указан ни телефон, ни Telegram ID\n'

    return text


def worker_saved_successfully(sent_to_api: bool = False) -> str:
    """Сообщение об успешном сохранении самозанятого"""
    if sent_to_api:
        return '✅ Исполнитель успешно добавлен в базу и зарегистрирован в «Рабочие Руки»\n\n' \
               '📲 Исполнитель может войти в бот, введя свой номер телефона'
    else:
        return '✅ Исполнитель <b>добавлен в локальную базу</b>\n\n' \
               'ℹ️ Данные сохранены только локально (без отправки в «Рабочие Руки»)\n' \
               '📲 Исполнитель может войти в бот, введя свой номер телефона'


def worker_save_error() -> str:
    """Ошибка при сохранении самозанятого"""
    return '❌ <b>Ошибка при сохранении исполнителя</b>\n\n' \
           'Попробуйте еще раз или обратитесь к системному администратору'


def worker_save_cancelled() -> str:
    """Отмена сохранения самозанятого"""
    return 'ℹ️ Добавление исполнителя отменено'
