from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class ShiftRecord:
    """Запись о смене"""
    user_id: int
    username: str
    full_name: str
    start_time: str  # ISO формат
    end_time: Optional[str] = None

    @property
    def start_datetime(self) -> datetime:
        """Начало смены как datetime"""
        return datetime.fromisoformat(self.start_time)

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Конец смены как datetime"""
        return datetime.fromisoformat(self.end_time) if self.end_time else None

    def duration(self) -> Optional[timedelta]:
        """Продолжительность смены"""
        if self.end_time:
            return self.end_datetime - self.start_datetime
        return None

    def duration_str(self) -> str:
        """Продолжительность в читаемом виде"""
        duration = self.duration()
        if duration:
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            return f"{hours}ч {minutes}м"
        return "В процессе"

    def elapsed_time(self) -> str:
        """Сколько времени прошло с начала смены"""
        elapsed = datetime.now() - self.start_datetime
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        return f"{hours}ч {minutes}м"

    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ShiftRecord':
        """Создание из словаря"""
        return cls(**data)