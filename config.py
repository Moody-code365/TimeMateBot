import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация бота"""
    # Токен бота (получить у @BotFather)
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    # Путь к файлу с данными
    DATA_FILE: str = "data/shifts.json"

    # Максимальная длительность смены (часы)
    MAX_SHIFT_HOURS: int = 9

    # Лимит истории для показа
    HISTORY_LIMIT: int = 5

    # Хранить только последние N дней (90 дней = 3 месяца)
    KEEP_HISTORY_DAYS: int = 30

    USER_SCHEDULES = {
        339487480: (17, 2),  # Замените на реальные ID и время
      #  987654321: (17, 2),   17:00 до 02:00 (ночная смена)
    }

    OFF_DAYS = (5, 6)  # Суббота и воскресенье


config = Config()