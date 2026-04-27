import asyncio
import logging

import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import MenuButtonDefault

from utils import scheduler, schedule_delete_inactive_users, schedule_missing_campaigns, schedule_streak_skip_check
from middlewares import CheckBlockMiddleware
from config_reader import config
from handlers import get_routers
import database as db


async def setup_web_app_menu_button(bot: Bot) -> None:
    """Убираем глобальную кнопку «Web-панель» у поля ввода (оставляем стандартное меню Telegram)."""
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
        logging.info('[STARTUP] setChatMenuButton: стандартная кнопка меню (без Web-панели)')
    except Exception:
        logging.exception('[STARTUP] setChatMenuButton не удался')


async def main():
    # Настройка логирования: INFO в консоль (для journalctl) и файл
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Вывод в консоль (journalctl)
            logging.FileHandler('bot.log')  # Запись в файл
        ]
    )

    redis = aioredis.from_url(
        f"redis://{config.redis_host.get_secret_value()}:"
        f"{config.redis_port.get_secret_value()}/"
        f"{config.redis_db.get_secret_value()}"
    )

    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher(storage=RedisStorage(redis))
    dp.message.middleware(CheckBlockMiddleware())
    dp.callback_query.middleware(CheckBlockMiddleware())
    dp.include_routers(*get_routers())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        logging.info("[STARTUP] Инициализация базы данных...")
        await db.init_models()
        await db.set_default_settings()

        logging.info("[STARTUP] Запуск планировщика...")
        scheduler.start()

        # Очистка старых проблемных задач звонков (с устаревшими названиями функций)
        logging.info("[STARTUP] Очистка старых задач звонков...")
        removed_count = 0
        for job in scheduler.get_jobs():
            # Удаляем старые задачи call_* (новые используют формат campaign_*)
            if job.id.startswith('call_') or job.id.startswith('poll_call_'):
                try:
                    scheduler.remove_job(job.id)
                    removed_count += 1
                    logging.info(f"[STARTUP] Удалена старая задача: {job.id}")
                except Exception as e:
                    logging.warning(f"[STARTUP] Не удалось удалить задачу {job.id}: {e}")

        if removed_count > 0:
            logging.info(f"[STARTUP] Удалено старых задач: {removed_count}")

        logging.info(f"[STARTUP] Scheduler запущен, задач в очереди: {len(scheduler.get_jobs())}")
        for job in scheduler.get_jobs():
            logging.info(f"[STARTUP]   Job: {job.id}, next_run_time: {job.next_run_time}")

        logging.info("[STARTUP] Планирование удаления неактивных пользователей...")
        await schedule_delete_inactive_users()

        logging.info("[STARTUP] Проверка и планирование прозвонов для активных заказов...")
        await schedule_missing_campaigns()

        logging.info("[STARTUP] Планирование проверки пропусков по акциям...")
        await schedule_streak_skip_check()

        logging.info(f"[STARTUP] Задач после инициализации: {len(scheduler.get_jobs())}")
        for job in scheduler.get_jobs():
            logging.info(f"[STARTUP]   Job: {job.id}, next_run_time: {job.next_run_time}")

        logging.info('[STARTUP] Настройка кнопки Web App (Bot API)...')
        await setup_web_app_menu_button(bot)

        logging.info("[STARTUP] Запуск polling...")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


async def on_startup(dispatcher: Dispatcher):
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for tg_id in config.bot_admins:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text='ℹ️ Бот запущен'
                )
            except:
                pass
    print("Start")


async def on_shutdown(dispatcher: Dispatcher):
    await db.close_session()
    async with Bot(token=config.bot_token.get_secret_value()) as bot:
        for tg_id in config.bot_admins:
            try:
                await bot.send_message(
                    chat_id=tg_id,
                    text='❗Бот выключен'
                )
            except:
                pass
    print('Finish')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
