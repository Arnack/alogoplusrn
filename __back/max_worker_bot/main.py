"""
Главный файл бота исполнителя для мессенджера Max
Адаптировано из Telegram бота на основе библиотеки maxapi
"""
import asyncio
import logging
import sys
import os

from maxapi import Bot, Dispatcher

# Добавляем родительскую директорию в путь для импорта модулей из основного проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт handlers для исполнителя
from max_worker_bot.handlers import (
    registration_handlers,
    search_orders_handlers,
    applications_handlers,
    profile_handlers,
    act_handlers,
    other_handlers
)


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    from max_worker_bot.config_reader import config

    # Инициализация бота с токеном из конфига
    if not config.max_bot_token:
        logger.error("MAX_BOT_TOKEN не найден в .env файле")
        return

    bot = Bot(token=config.max_bot_token.get_secret_value())

    # Создание диспетчера
    dp = Dispatcher()

    # Удаление webhook если он установлен (для работы polling)
    try:
        await bot.delete_webhook()
        logger.info("Webhook удален")
    except Exception as e:
        logger.warning(f"Ошибка при удалении webhook: {e}")

    # Регистрация роутеров обработчиков
    dp.include_routers(
        registration_handlers.router,
        search_orders_handlers.router,
        applications_handlers.router,
        profile_handlers.router,
        act_handlers.router,
        other_handlers.router
    )

    logger.info("Бот запущен. Ожидание сообщений...")

    # Запуск polling
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем")
