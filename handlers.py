from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards import get_main_keyboard, get_reply_keyboard
from storage import ShiftStorage
from config import config

# Создаём роутер
router = Router()

# Хранилище данных
storage = ShiftStorage()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start - приветствие"""
    # Показываем ID группы в консоли
    if message.chat.type in ['group', 'supergroup']:
        print(f"📝 ID этой группы: {message.chat.id}")
        
        # Проверяем является ли пользователь владельцем
        try:
            admins = await message.bot.get_chat_administrators(message.chat.id)
            is_owner = any(admin.status == "creator" and admin.user.id == message.from_user.id for admin in admins)
            
            if is_owner:
                await message.answer(
                    "👋 <b>Привет! Я бот учёта рабочего времени</b>\n\n"
                    "👑 <b>Обнаружен владелец группы!</b>\n"
                    "Доступна админ-панель: /admin\n\n"
                    "Используй кнопки внизу для отметки смен:\n"
                    "🟢 <b>Пришёл</b> — начать смену\n"
                    "🔴 <b>Ушёл</b> — закончить смену\n"
                    "📊 <b>Статус</b> — кто сейчас на работе\n"
                    "📜 <b>История</b> — твои последние смены\n\n"
                    "<b>Команды:</b>\n"
                    "/stats — твоя статистика\n"
                    "/admin — админ-панель (только для владельца)",
                    parse_mode="HTML",
                    reply_markup=get_reply_keyboard()
                )
                return
        except Exception as e:
            print(f"Ошибка проверки владельца: {e}")

    await message.answer(
        "👋 <b>Привет! Я бот учёта рабочего времени</b>\n\n"
        "Используй кнопки внизу для отметки смен:\n"
        "🟢 <b>Пришёл</b> — начать смену\n"
        "🔴 <b>Ушёл</b> — закончить смену\n"
        "📊 <b>Статус</b> — кто сейчас на работе\n"
        "📜 <b>История</b> — твои последние смены\n\n"
        "<b>Команды:</b>\n"
        "/stats — твоя статистика",
        parse_mode="HTML",
        reply_markup=get_reply_keyboard()
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu - показать меню"""
    await message.answer(
        "Выбери действие:",
        reply_markup=get_reply_keyboard()
    )


# Обработка текстовых кнопок "Пришёл"
@router.message(F.text == "🟢 Пришёл")
async def text_shift_start(message: Message):
    """Начать смену через текстовую кнопку"""
    user_id = message.from_user.id
    username = message.from_user.username or "noname"
    full_name = message.from_user.full_name

    # Проверка: уже на смене?
    if storage.is_on_shift(user_id):
        await message.answer("⚠️ Ты уже отметился! Сначала нажми 'Ушёл'")
        return

    # Начинаем смену
    shift = storage.start_shift(user_id, username, full_name)
    time_str = shift.start_datetime.strftime("%H:%M")

    await message.answer(
        f"✅ <b>{full_name}</b> пришёл на смену в {time_str}",
        parse_mode="HTML"
    )


# Обработка текстовых кнопок "Ушёл"
@router.message(F.text == "🔴 Ушёл")
async def text_shift_end(message: Message):
    """Закончить смену через текстовую кнопку"""
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    # Проверка: отмечался ли приход?
    if not storage.is_on_shift(user_id):
        await message.answer("⚠️ Ты ещё не отметился! Сначала нажми 'Пришёл'")
        return

    # Заканчиваем смену
    shift = storage.end_shift(user_id)
    if shift:
        start_str = shift.start_datetime.strftime("%H:%M")
        end_str = shift.end_datetime.strftime("%H:%M")
        duration = shift.duration_str()

        await message.answer(
            f"🏁 <b>{full_name}</b> закончил смену\n"
            f"⏰ Время: {start_str} — {end_str}\n"
            f"⌛️ Отработано: {duration}",
            parse_mode="HTML"
        )


# Обработка текстовых кнопок "Статус"
@router.message(F.text == "📊 Статус")
async def text_shift_status(message: Message):
    """Показать текущий статус через текстовую кнопку"""
    active_shifts = storage.get_all_active_shifts()

    if not active_shifts:
        await message.answer("Сейчас никого нет на работе 🏖")
        return

    # Формируем список
    lines = ["👥 <b>Сейчас на смене:</b>\n"]
    for shift in active_shifts:
        start_time = shift.start_datetime.strftime("%H:%M")
        elapsed = shift.elapsed_time()

        lines.append(
            f"• <b>{shift.full_name}</b>\n"
            f"  └ Пришёл: {start_time} ({elapsed} назад)"
        )

    await message.answer(
        "\n\n".join(lines),
        parse_mode="HTML"
    )


# Обработка текстовых кнопок "История"
@router.message(F.text == "📜 История")
async def text_shift_history(message: Message):
    """Показать историю смен через текстовую кнопку"""
    user_id = message.from_user.id
    history = storage.get_user_history(user_id, limit=config.HISTORY_LIMIT)

    if not history:
        await message.answer("У тебя пока нет завершённых смен 📭")
        return

    # Формируем список
    lines = ["📜 <b>Твои последние смены:</b>\n"]
    for shift in reversed(history):
        date_str = shift.start_datetime.strftime("%d.%m.%Y")
        start_str = shift.start_datetime.strftime("%H:%M")
        end_str = shift.end_datetime.strftime("%H:%M") if shift.end_datetime else "—"
        duration = shift.duration_str()

        lines.append(
            f"📅 {date_str}\n"
            f"  ⏰ {start_str} — {end_str}\n"
            f"  ⌛️ {duration}"
        )

    await message.answer(
        "\n\n".join(lines),
        parse_mode="HTML"
    )


# Inline-кнопки (оставил для совместимости)
@router.callback_query(F.data == "shift_start")
async def callback_shift_start(callback: CallbackQuery):
    """Начать смену"""
    user_id = callback.from_user.id
    username = callback.from_user.username or "noname"
    full_name = callback.from_user.full_name

    if storage.is_on_shift(user_id):
        await callback.answer("⚠️ Ты уже отметился! Сначала нажми 'Ушёл'", show_alert=True)
        return

    shift = storage.start_shift(user_id, username, full_name)
    time_str = shift.start_datetime.strftime("%H:%M")

    await callback.message.answer(
        f"✅ <b>{full_name}</b> пришёл на смену в {time_str}",
        parse_mode="HTML"
    )
    await callback.answer("Смена началась! 💼")


@router.callback_query(F.data == "shift_end")
async def callback_shift_end(callback: CallbackQuery):
    """Закончить смену"""
    user_id = callback.from_user.id
    full_name = callback.from_user.full_name

    if not storage.is_on_shift(user_id):
        await callback.answer("⚠️ Ты ещё не отметился! Сначала нажми 'Пришёл'", show_alert=True)
        return

    shift = storage.end_shift(user_id)
    if shift:
        start_str = shift.start_datetime.strftime("%H:%M")
        end_str = shift.end_datetime.strftime("%H:%M")
        duration = shift.duration_str()

        await callback.message.answer(
            f"🏁 <b>{full_name}</b> закончил смену\n"
            f"⏰ Время: {start_str} — {end_str}\n"
            f"⌛️ Отработано: {duration}",
            parse_mode="HTML"
        )
        await callback.answer("Хорошей дороги! 👋")


@router.callback_query(F.data == "shift_status")
async def callback_shift_status(callback: CallbackQuery):
    """Показать текущий статус"""
    active_shifts = storage.get_all_active_shifts()

    if not active_shifts:
        await callback.answer("Сейчас никого нет на работе 🏖", show_alert=True)
        return

    lines = ["👥 <b>Сейчас на смене:</b>\n"]
    for shift in active_shifts:
        start_time = shift.start_datetime.strftime("%H:%M")
        elapsed = shift.elapsed_time()

        lines.append(
            f"• <b>{shift.full_name}</b>\n"
            f"  └ Пришёл: {start_time} ({elapsed} назад)"
        )

    await callback.message.answer("\n\n".join(lines), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "shift_history")
async def callback_shift_history(callback: CallbackQuery):
    """Показать историю смен"""
    user_id = callback.from_user.id
    history = storage.get_user_history(user_id, limit=config.HISTORY_LIMIT)

    if not history:
        await callback.answer("У тебя пока нет завершённых смен 📭", show_alert=True)
        return

    lines = ["📜 <b>Твои последние смены:</b>\n"]
    for shift in reversed(history):
        date_str = shift.start_datetime.strftime("%d.%m.%Y")
        start_str = shift.start_datetime.strftime("%H:%M")
        end_str = shift.end_datetime.strftime("%H:%M") if shift.end_datetime else "—"
        duration = shift.duration_str()

        lines.append(
            f"📅 {date_str}\n"
            f"  ⏰ {start_str} — {end_str}\n"
            f"  ⌛️ {duration}"
        )

    await callback.message.answer("\n\n".join(lines), parse_mode="HTML")
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика пользователя"""
    user_id = message.from_user.id
    history = storage.get_user_history(user_id, limit=1000)

    if not history:
        await message.answer("У тебя пока нет данных для статистики 📊")
        return

    total_shifts = len(history)
    total_duration = sum(
        (s.duration() for s in history if s.duration()),
        timedelta()
    )
    total_hours = total_duration.total_seconds() / 3600
    avg_hours = total_hours / total_shifts if total_shifts > 0 else 0

    last_shift = history[-1]
    last_date = last_shift.start_datetime.strftime("%d.%m.%Y")

    await message.answer(
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"✅ Всего смен: {total_shifts}\n"
        f"⏱ Всего отработано: {total_hours:.1f} ч\n"
        f"📅 Последняя смена: {last_date}\n"
        f"⌛️ Средняя длительность: {avg_hours:.1f} ч",
        parse_mode="HTML"
    )
