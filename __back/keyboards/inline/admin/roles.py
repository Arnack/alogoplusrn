from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def roles_menu():
    """Главное меню управления ролями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👔 Директор", callback_data="DirectorsMenu")],
        [InlineKeyboardButton(text="🦺 Координатор", callback_data="RoleCoordinators")],
        [InlineKeyboardButton(text="💳 Кассир", callback_data="RoleCashiers")],
        [InlineKeyboardButton(text="👥 Менеджеры", callback_data="RoleManagers")],
    ])


def directors_menu():
    """Меню директоров"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить директора", callback_data="AddDirector")],
        [InlineKeyboardButton(text="👔 Все директора", callback_data="AllDirectors")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="RolesMenuBack")]
    ])


async def directors_list():
    """Список всех директоров"""
    from database import get_directors
    directors = await get_directors()

    buttons = []
    for director in directors:
        buttons.append([
            InlineKeyboardButton(
                text=director.full_name,
                callback_data=f"Director:{director.tg_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="DirectorsMenu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def directors_back():
    """Кнопка назад для пустого списка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="DirectorsMenu")]
    ])


def delete_director(director_id: int):
    """Кнопка удаления директора"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"DeleteDirector:{director_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="AllDirectors")]
    ])


def save_director():
    """Кнопка сохранения нового директора"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 Сохранить", callback_data="SaveDirector")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="DirectorAddCancel")]
    ])
