import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import config
from handlers import router
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


async def check_reminders():
    """Проверка забытых отметок и отправка напоминаний"""
    if not bot:
        return

    user_schedules = config.USER_SCHEDULES

    for user_id, (start_hour, end_hour) in user_schedules.items():
        try:
            # Проверка: забыл ли отметиться приходом
            if storage.check_forgot_to_checkin(user_id):
                await bot.send_message(
                    user_id,
                    "⏰ <b>Напоминание!</b>\n"
                    "Ты в рабочих часах, но не отметился приходом! \n"
                    "Нажми кнопку <b>'Пришёл'</b>",
                    parse_mode="HTML"
                )
                logger.info(f" Отправлено напоминание о приходе пользователю {user_id}")

            # Проверка: забыл ли отметиться уходом
            if storage.check_forgot_to_checkout(user_id):
                await bot.send_message(
                    user_id,
                    "⏰ <b>Напоминание!</b>\n"
                    f"Смена длится дольше {config.MAX_SHIFT_HOURS} часов! \n"
                    "Пора отмечаться уходом?",
                    parse_mode="HTML"
                )
                logger.info(f" Отправлено напоминание об уходе пользователю {user_id}")

        except Exception as e:
            logger.error(f"⚠️ Ошибка при отправке напоминания {user_id}: {e}")


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

    # Регистрация роутера
    dp.include_router(router)

    # Запуск scheduler для напоминаний
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_reminders, "interval", minutes=30)  # Проверка каждые 30 минут
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
