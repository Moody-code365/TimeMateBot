import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import config
from handlers import router
from admin_handlers import admin_router
from storage import ShiftStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные
bot = None
storage = ShiftStorage()


async def main():
    """Запуск бота"""
    global bot

    # Проверка токена
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
        return

    # Инициализация
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(router)
    dp.include_router(admin_router)

    # Запуск scheduler для напоминаний
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("⏱️ Scheduler запущен")

    # Запуск
    logger.info(" Бот запускается...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Бот остановлен")
