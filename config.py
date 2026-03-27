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
    MAX_SHIFT_HOURS: int = 12

    # Лимит истории для показа
    HISTORY_LIMIT: int = 5


config = Config()