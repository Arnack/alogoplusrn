def roles_menu():
    return "🎭 <b>Управление ролями</b>\n\nВыберите роль для управления:"


def directors():
    return "👔 <b>Директора</b>\n\nУправление директорами платформы"


def directors_list():
    return "👔 <b>Список директоров</b>\n\nВыберите директора для просмотра информации:"


def directors_none():
    return "👔 <b>Директора</b>\n\nСписок директоров пуст"


def director_info(name: str, tg_id: int):
    return f"<b>Директор</b>\n\nФИО: {name}\nTelegram ID: {tg_id}"


def add_director_full_name():
    return "Введите ФИО директора:"


def add_director_position():
    return "Введите должность директора:"


def add_director_tg_id():
    return "Введите Telegram ID директора:"


def accept_new_director(name: str, tg_id: str):
    return f"<b>Подтвердите данные:</b>\n\nФИО: {name}\nTelegram ID: {tg_id}"


def director_added():
    return "✅ Директор успешно добавлен"


def director_deleted():
    return "🗑 Директор удален"
