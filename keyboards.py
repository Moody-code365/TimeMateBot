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