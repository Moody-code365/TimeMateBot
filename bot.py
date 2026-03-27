import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import config
from handlers import router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота"""
    # Проверка токена
    if config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ ОШИБКА: Вставьте токен бота в config.py!")
        return

    # Инициализация
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация роутера
    dp.include_router(router)

    # Запуск
    logger.info("🤖 Бот запускается...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен")