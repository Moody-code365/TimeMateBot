import json
import os
from datetime import datetime, timedelta
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

            self._clean_old_records()

            print(f"✅ Загружено: {len(self.active_shifts)} активных смен, "
                  f"{len(self.shift_history)} записей истории")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки данных: {e}")

    def _clean_old_records(self):
        """Удалить записи истории, старые чем KEEP_HISTORY_DAYS дней"""
        # Сохраняем исходное количество
        original_count = len(self.shift_history)

        # Вычисляем дату отсечки
        cutoff_date = datetime.now() - timedelta(days=config.KEEP_HISTORY_DAYS)

        # Оставляем только свежие записи (старше cutoff_date)
        self.shift_history = [
            shift for shift in self.shift_history
            if shift.start_datetime > cutoff_date
        ]

        # Подсчитываем удалённые записи
        deleted_count = original_count - len(self.shift_history)
        if deleted_count > 0:
            print(f"️ Удалено {deleted_count} старых записей (старше {config.KEEP_HISTORY_DAYS} дней)")
            self._save_data()

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

    def get_user_schedule(self, user_id: int) -> tuple:
        """Получить расписание пользователя"""
        return config.USER_SCHEDULES.get(user_id, (9, 18))  # По умолчанию 9-18

    def is_off_day(self) -> bool:
        """Проверить: сегодня выходной?"""
        weekday = datetime.now().weekday()  # 0=Пн, 6=Вс
        return weekday in config.OFF_DAYS

    def is_working_hours(self, user_id: int) -> bool:
        """Проверить: сейчас рабочие часы пользователя?"""
        from datetime import time

        # Если сегодня выходной, рабочих часов нет
        if self.is_off_day():
            return False

        current_time = datetime.now().time()
        start_hour, end_hour = self.get_user_schedule(user_id)

        # Если конец смены раньше чем начало (ночная смена, например 17-02)
        if end_hour < start_hour:
            # Ночная смена: работаем либо после start_hour, либо до end_hour
            return current_time >= time(start_hour, 0) or current_time < time(end_hour, 0)
        else:
            # Дневная смена: работаем между start_hour и end_hour
            return time(start_hour, 0) <= current_time < time(end_hour, 0)

    def check_forgot_to_checkin(self, user_id: int) -> bool:
        """Проверить: пользователь забыл отметиться приходом?

        Возвращает True если:
        - Сейчас рабочие часы пользователя
        - Но он не отметился приходом
        """
        return self.is_working_hours(user_id) and not self.is_on_shift(user_id)

    def check_forgot_to_checkout(self, user_id: int) -> bool:
        """Проверить: пользователь забыл отметиться уходом?

        Возвращает True если:
        - Пользователь на смене (есть start_time)
        - Но смена длится дольше MAX_SHIFT_HOURS часов
        """
        shift = self.get_active_shift(user_id)
        if not shift:
            return False

        elapsed_time = datetime.now() - shift.start_datetime
        max_hours = config.MAX_SHIFT_HOURS

        return elapsed_time.total_seconds() / 3600 > max_hours

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
            self._clean_old_records()  # Очищаем при добавлении новой записи
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
