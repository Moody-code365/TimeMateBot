import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from models import ShiftRecord
from config import config


class ShiftStorage:
    """Хранилище данных о сменах"""

    def __init__(self, data_file: str = config.DATA_FILE):
        self.data_file = data_file
        self.active_shifts: Dict[int, ShiftRecord] = {}
        self.shift_history: List[ShiftRecord] = []
        self._load_data()

    def _ensure_data_dir(self):
        """Создать папку для данных если не существует"""
        data_dir = os.path.dirname(self.data_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _load_data(self):
        """Загрузить данные из файла"""
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Загружаем активные смены
            self.active_shifts = {
                int(user_id): ShiftRecord.from_dict(shift_data)
                for user_id, shift_data in data.get('active_shifts', {}).items()
            }

            # Загружаем историю
            self.shift_history = [
                ShiftRecord.from_dict(shift_data)
                for shift_data in data.get('shift_history', [])
            ]

            print(f"✅ Загружено: {len(self.active_shifts)} активных смен, "
                  f"{len(self.shift_history)} записей истории")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки данных: {e}")

    def _save_data(self):
        """Сохранить данные в файл"""
        self._ensure_data_dir()

        data = {
            'active_shifts': {
                str(user_id): shift.to_dict()
                for user_id, shift in self.active_shifts.items()
            },
            'shift_history': [shift.to_dict() for shift in self.shift_history]
        }

        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения данных: {e}")

    def start_shift(self, user_id: int, username: str, full_name: str) -> ShiftRecord:
        """Начать смену"""
        shift = ShiftRecord(
            user_id=user_id,
            username=username,
            full_name=full_name,
            start_time=datetime.now().isoformat()
        )
        self.active_shifts[user_id] = shift
        self._save_data()
        return shift

    def end_shift(self, user_id: int) -> Optional[ShiftRecord]:
        """Закончить смену"""
        shift = self.active_shifts.pop(user_id, None)
        if shift:
            shift.end_time = datetime.now().isoformat()
            self.shift_history.append(shift)
            self._save_data()
        return shift

    def is_on_shift(self, user_id: int) -> bool:
        """Проверка: на смене ли пользователь"""
        return user_id in self.active_shifts

    def get_active_shift(self, user_id: int) -> Optional[ShiftRecord]:
        """Получить активную смену пользователя"""
        return self.active_shifts.get(user_id)

    def get_user_history(self, user_id: int, limit: int = 10) -> List[ShiftRecord]:
        """Получить историю смен пользователя"""
        user_shifts = [s for s in self.shift_history if s.user_id == user_id]
        return user_shifts[-limit:]

    def get_all_active_shifts(self) -> List[ShiftRecord]:
        """Получить все активные смены"""
        return list(self.active_shifts.values())