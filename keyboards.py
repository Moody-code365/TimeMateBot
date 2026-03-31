from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главная inline-клавиатура (кнопки под сообщениями)"""
    builder = InlineKeyboardBuilder()

    # Первая строка
    builder.row(
        InlineKeyboardButton(text="🟢 Пришёл", callback_data="shift_start"),
        InlineKeyboardButton(text="🔴 Ушёл", callback_data="shift_end")
    )

    # Вторая строка
    builder.row(
        InlineKeyboardButton(text="📊 Статус", callback_data="shift_status"),
        InlineKeyboardButton(text="📜 История", callback_data="shift_history")
    )

    return builder.as_markup()


def get_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply-клавиатура (постоянные кнопки внизу экрана)"""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="🟢 Пришёл"),
        KeyboardButton(text="🔴 Ушёл")
    )
    builder.row(
        KeyboardButton(text="📊 Статус"),
        KeyboardButton(text="📜 История")
    )

    return builder.as_markup(resize_keyboard=True)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    builder = InlineKeyboardBuilder()

    # Первая строка - основные функции
    builder.row(
        InlineKeyboardButton(text="👥 Кто на смене", callback_data="admin_active_shifts"),
        InlineKeyboardButton(text="📊 Статистика всех", callback_data="admin_stats_all")
    )
    
    # Вторая строка - детализация
    builder.row(
        InlineKeyboardButton(text="🔍 Детали пользователя", callback_data="admin_user_details"),
        InlineKeyboardButton(text="📈 Метрики", callback_data="admin_metrics")
    )
    
    # Третья строка - доп. функции
    builder.row(
        InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export")
    )

    return builder.as_markup()


def get_admin_reply_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная админ-клавиатура (как у обычных пользователей)"""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="👥 Кто на смене"),
        KeyboardButton(text="📊 Статистика всех")
    )
    builder.row(
        KeyboardButton(text="🔍 Детали пользователя"),
        KeyboardButton(text="📈 Метрики")
    )
    builder.row(
        KeyboardButton(text="📤 Экспорт данных"),
        KeyboardButton(text="🔙 Назад")
    )

    return builder.as_markup(resize_keyboard=True)


def get_export_format_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора формата экспорта"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📄 CSV", callback_data="export_csv"),
        InlineKeyboardButton(text="📋 JSON", callback_data="export_json")
    )
    builder.row(
        InlineKeyboardButton(text="📝 TXT", callback_data="export_txt"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
    )

    return builder.as_markup()


def get_user_list_keyboard(users: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора пользователя"""
    builder = InlineKeyboardBuilder()

    # Добавляем пользователей по 2 в строку
    for i in range(0, len(users), 2):
        if i + 1 < len(users):
            builder.row(
                InlineKeyboardButton(text=users[i]['name'], callback_data=f"user_select_{users[i]['id']}"),
                InlineKeyboardButton(text=users[i+1]['name'], callback_data=f"user_select_{users[i+1]['id']}")
            )
        else:
            builder.row(
                InlineKeyboardButton(text=users[i]['name'], callback_data=f"user_select_{users[i]['id']}")
            )
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
    )

    return builder.as_markup()