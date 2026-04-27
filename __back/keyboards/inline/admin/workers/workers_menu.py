from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton


def adm_workers_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🚶 СМЗ', callback_data='AddWorker')],
            [InlineKeyboardButton(text='Разблокировать', callback_data='UnblockUser'),
             InlineKeyboardButton(text='Заблокировать', callback_data='BlockUser')],
            [InlineKeyboardButton(text='Сформировать PDF', callback_data='GetAllWorkersPDF'),
             InlineKeyboardButton(text='Аккаунт', callback_data='WorkerAccount')],
            [InlineKeyboardButton(text='📊 Закрываемость', callback_data='ClosureReport'),
             InlineKeyboardButton(text='❌ Удалить', callback_data='AdminDeleteFromOrder')],
            [InlineKeyboardButton(text='💰 Договорные комиссии', callback_data='SelfEmployedMenu')]
        ]
    )
