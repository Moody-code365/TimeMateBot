from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from keyboards import get_admin_keyboard, get_admin_reply_keyboard, get_export_format_keyboard, get_user_list_keyboard, get_reply_keyboard
from storage import ShiftStorage

# Создаём роутер для админских команд
admin_router = Router()
storage = ShiftStorage()


async def check_group_owner(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Проверить является ли пользователь владельцем группы"""
    try:
        # Получаем администраторов группы
        admins = await bot.get_chat_administrators(chat_id)
        
        # Ищем владельца (creator)
        owners = set()
        for admin in admins:
            if admin.status == "creator":
                owners.add(admin.user.id)
        
        # Кешируем результат
        await storage.update_group_owners(chat_id, owners)
        
        return user_id in owners
    except Exception:
        return False


@admin_router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    """Админ-панель"""
    if message.chat.type not in ['group', 'supergroup']:
        await message.answer("⚠️ Эта команда работает только в группах!")
        return
    
    # Проверяем является ли пользователь владельцем
    is_owner = await check_group_owner(message.bot, message.chat.id, message.from_user.id)
    
    if not is_owner:
        await message.answer("🚫 Доступ запрещено! Эта команда только для владельца группы.")
        return
    
    await message.answer(
        "👑 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )


# Обработка текстовых кнопок админ-панели
@admin_router.message(F.text == "👥 Кто на смене")
async def admin_text_active_shifts(message: Message):
    """Показать всех на смене через текстовую кнопку"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    active_shifts = storage.get_all_active_shifts()
    
    if not active_shifts:
        await message.answer("🏖 Сейчас никого нет на работе")
        return
    
    lines = ["👥 <b>Сейчас на смене:</b>\n"]
    
    for shift in active_shifts:
        start_time = shift.start_datetime.strftime("%H:%M")
        elapsed = shift.elapsed_time()
        
        lines.append(
            f"• <b>{shift.full_name}</b> (@{shift.username or 'no_username'})\n"
            f"  └ Пришёл: {start_time} ({elapsed} назад)"
        )
    
    lines.append(f"\n📊 <b>Всего на смене:</b> {len(active_shifts)} человек")
    
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@admin_router.message(F.text == "📊 Статистика всех")
async def admin_text_stats_all(message: Message):
    """Показать статистику по всем пользователям через текстовую кнопку"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    stats = storage.get_all_users_stats()
    
    if not stats:
        await message.answer("📊 Пока нет данных для статистики")
        return
    
    lines = ["📊 <b>Статистика по всем пользователям:</b>\n"]
    
    # Сортируем по общему времени работы
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_hours'], reverse=True)
    
    for user_id, user_stats in sorted_stats:
        lines.append(
            f"👤 <b>{user_stats['name']}</b>\n"
            f"  └ Смен: {user_stats['shifts_count']} | "
            f"Часов: {user_stats['total_hours']:.1f} | "
            f"Среднее: {user_stats['total_hours']/user_stats['shifts_count']:.1f}ч"
        )
    
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@admin_router.message(F.text == "🔍 Детали пользователя")
async def admin_text_user_details(message: Message):
    """Подробная информация о пользователе через текстовую кнопку"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    # Получаем список всех пользователей
    stats = storage.get_all_users_stats()
    
    if not stats:
        await message.answer("📭 Пока нет пользователей")
        return
    
    # Формируем список пользователей для выбора
    users = []
    for user_id, user_stats in stats.items():
        users.append({
            'id': user_id,
            'name': user_stats['name']
        })
    
    await message.answer(
        "🔍 <b>Выберите пользователя:</b>",
        parse_mode="HTML",
        reply_markup=get_user_list_keyboard(users)
    )


@admin_router.message(F.text == "📈 Метрики")
async def admin_text_metrics(message: Message):
    """Метрики и аналитика через текстовую кнопку"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    # Получаем данные за последние 30 дней
    cutoff_date = datetime.now() - timedelta(days=30)
    recent_shifts = [s for s in storage.shift_history if s.start_datetime > cutoff_date]
    
    if not recent_shifts:
        await message.answer("📭 За последние 30 дней смен не было")
        return
    
    # Группируем смены по дням
    daily_shifts = {}
    for shift in recent_shifts:
        date_key = shift.start_datetime.strftime("%d.%m.%y")
        if date_key not in daily_shifts:
            daily_shifts[date_key] = []
        daily_shifts[date_key].append(shift)
    
    lines = ["📈 <b>Смены по дням (последние 30 дней):</b>\n"]
    
    # Сортируем по дате
    sorted_dates = sorted(daily_shifts.keys(), reverse=True)
    
    for date in sorted_dates[:15]:  # Показываем последние 15 дней
        shifts = daily_shifts[date]
        lines.append(f"\n📅 <b>{date}</b> ({len(shifts)} смен):")
        
        for shift in shifts:
            start_str = shift.start_datetime.strftime("%H:%M")
            end_str = shift.end_datetime.strftime("%H:%M") if shift.end_datetime else "—"
            duration = shift.duration_str()
            
            lines.append(f"  • {shift.full_name}: {start_str}-{end_str} ({duration})")
    
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@admin_router.message(F.text == "📤 Экспорт данных")
async def admin_text_export(message: Message):
    """Экспорт данных через текстовую кнопку"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    await message.answer(
        "📤 <b>Выберите формат экспорта:</b>",
        parse_mode="HTML",
        reply_markup=get_export_format_keyboard()
    )


@admin_router.message(F.text == "🔙 Назад")
async def admin_text_back(message: Message):
    """Вернуться к пользовательской панели"""
    if not await check_group_owner(message.bot, message.chat.id, message.from_user.id):
        return
    
    await message.answer(
        "👋 <b>Возврат к основному меню</b>\n\n"
        "Используйте кнопки для отметки смен:\n"
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


# Callback обработчики для inline кнопок
@admin_router.callback_query(F.data == "admin_active_shifts")
async def admin_active_shifts(callback: CallbackQuery):
    """Показать всех на смене"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    active_shifts = storage.get_all_active_shifts()
    
    if not active_shifts:
        await callback.message.answer("🏖 Сейчас никого нет на работе")
        await callback.answer()
        return
    
    lines = ["👥 <b>Сейчас на смене:</b>\n"]
    
    for shift in active_shifts:
        start_time = shift.start_datetime.strftime("%H:%M")
        elapsed = shift.elapsed_time()
        
        lines.append(
            f"• <b>{shift.full_name}</b> (@{shift.username or 'no_username'})\n"
            f"  └ Пришёл: {start_time} ({elapsed} назад)"
        )
    
    lines.append(f"\n📊 <b>Всего на смене:</b> {len(active_shifts)} человек")
    
    await callback.message.answer("\n\n".join(lines), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data == "admin_stats_all")
async def admin_stats_all(callback: CallbackQuery):
    """Показать статистику по всем пользователям"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    stats = storage.get_all_users_stats()
    
    if not stats:
        await callback.message.answer("📊 Пока нет данных для статистики")
        await callback.answer()
        return
    
    lines = ["📊 <b>Статистика по всем пользователям:</b>\n"]
    
    # Сортируем по общему времени работы
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_hours'], reverse=True)
    
    for user_id, user_stats in sorted_stats:
        lines.append(
            f"👤 <b>{user_stats['name']}</b>\n"
            f"  └ Смен: {user_stats['shifts_count']} | "
            f"Часов: {user_stats['total_hours']:.1f} | "
            f"Среднее: {user_stats['total_hours']/user_stats['shifts_count']:.1f}ч"
        )
    
    await callback.message.answer("\n\n".join(lines), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data == "admin_user_details")
async def admin_user_details(callback: CallbackQuery):
    """Подробная информация о пользователе"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    # Получаем список всех пользователей
    stats = storage.get_all_users_stats()
    
    if not stats:
        await callback.message.answer("📭 Пока нет пользователей")
        await callback.answer()
        return
    
    # Формируем список пользователей для выбора
    users = []
    for user_id, user_stats in stats.items():
        users.append({
            'id': user_id,
            'name': user_stats['name']
        })
    
    await callback.message.answer(
        "🔍 <b>Выберите пользователя:</b>",
        parse_mode="HTML",
        reply_markup=get_user_list_keyboard(users)
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_metrics")
async def admin_metrics(callback: CallbackQuery):
    """Метрики и аналитика"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    # Получаем данные за последние 30 дней
    cutoff_date = datetime.now() - timedelta(days=30)
    recent_shifts = [s for s in storage.shift_history if s.start_datetime > cutoff_date]
    
    if not recent_shifts:
        await callback.message.answer("📭 За последние 30 дней смен не было")
        await callback.answer()
        return
    
    # Группируем смены по дням
    daily_shifts = {}
    for shift in recent_shifts:
        date_key = shift.start_datetime.strftime("%d.%m.%y")
        if date_key not in daily_shifts:
            daily_shifts[date_key] = []
        daily_shifts[date_key].append(shift)
    
    lines = ["📈 <b>Смены по дням (последние 30 дней):</b>\n"]
    
    # Сортируем по дате
    sorted_dates = sorted(daily_shifts.keys(), reverse=True)
    
    for date in sorted_dates[:15]:  # Показываем последние 15 дней
        shifts = daily_shifts[date]
        lines.append(f"\n📅 <b>{date}</b> ({len(shifts)} смен):")
        
        for shift in shifts:
            start_str = shift.start_datetime.strftime("%H:%M")
            end_str = shift.end_datetime.strftime("%H:%M") if shift.end_datetime else "—"
            duration = shift.duration_str()
            
            lines.append(f"  • {shift.full_name}: {start_str}-{end_str} ({duration})")
    
    await callback.message.answer("\n\n".join(lines), parse_mode="HTML")
    await callback.answer()


@admin_router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery):
    """Экспорт данных"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    await callback.message.answer(
        "📤 <b>Выберите формат экспорта:</b>",
        parse_mode="HTML",
        reply_markup=get_export_format_keyboard()
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Вернуться к пользовательской панели"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    await callback.message.answer(
        "👋 <b>Возврат к основному меню</b>\n\n"
        "Используйте кнопки для отметки смен:\n"
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
    await callback.answer()


# Обработка выбора пользователя
@admin_router.callback_query(F.data.startswith("user_select_"))
async def admin_user_selected(callback: CallbackQuery):
    """Обработка выбора пользователя"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[2])
    
    # Получаем историю пользователя
    history = storage.get_user_history(user_id, limit=1000)
    
    if not history:
        await callback.message.answer("📭 У этого пользователя пока нет смен")
        await callback.answer()
        return
    
    user_name = history[0].full_name
    username = history[0].username
    
    # Статистика
    total_shifts = len(history)
    total_duration = sum(
        (s.duration() for s in history if s.duration()),
        timedelta()
    )
    total_hours = total_duration.total_seconds() / 3600
    avg_hours = total_hours / total_shifts if total_shifts > 0 else 0
    
    # Последние 5 смен
    recent_shifts = history[-5:]
    
    lines = [
        f"👤 <b>Информация о пользователе:</b>\n\n"
        f"👨‍💼 <b>{user_name}</b>\n"
        f"🔹 ID: {user_id}\n"
        f"🔹 Username: @{username or 'нет'}\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"  • Всего смен: {total_shifts}\n"
        f"  • Всего часов: {total_hours:.1f}\n"
        f"  • Среднее время: {avg_hours:.1f} ч\n\n"
        f"📜 <b>Последние 5 смен:</b>\n"
    ]
    
    for shift in reversed(recent_shifts):
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


# Обработка экспорта
@admin_router.callback_query(F.data == "export_csv")
async def admin_export_csv(callback: CallbackQuery):
    """Экспорт в CSV файлом"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    import io
    from aiogram.types import BufferedInputFile
    from datetime import datetime
    
    # Только завершенные смены
    completed_shifts = [s for s in storage.shift_history if s.end_time]
    
    # Формируем CSV в памяти
    csv_lines = ["Имя,Username,Дата начала,Дата конца,Длительность"]
    
    for shift in completed_shifts:
        start_str = shift.start_datetime.strftime("%d.%m.%Y %H:%M")
        end_str = shift.end_datetime.strftime("%d.%m.%Y %H:%M") if shift.end_datetime else ""
        duration = shift.duration_str() if shift.duration() else "0ч 0м"
        
        csv_lines.append(f"{shift.full_name},{shift.username},{start_str},{end_str},{duration}")
    
    csv_text = "\n".join(csv_lines)
    
    # Создаем файл
    file = BufferedInputFile(
        csv_text.encode('utf-8'),
        filename=f"shifts_export_{datetime.now().strftime('%d%m%Y_%H%M%S')}.csv"
    )
    
    await callback.message.answer_document(
        document=file,
        caption=f"📄 <b>CSV Экспорт</b>\n\n"
                f"✅ Завершенных смен: {len(completed_shifts)}\n"
                f"🔄 Активных смен: {len(storage.active_shifts)}",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "export_json")
async def admin_export_json(callback: CallbackQuery):
    """Экспорт в JSON файлом"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    import json
    import io
    from aiogram.types import BufferedInputFile
    from datetime import datetime
    
    # Только завершенные смены
    completed_shifts = [s for s in storage.shift_history if s.end_time]
    
    # Формируем JSON
    export_data = {
        "export_info": {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "total_completed_shifts": len(completed_shifts),
            "active_shifts": len(storage.active_shifts)
        },
        "shifts": []
    }
    
    for shift in completed_shifts:
        export_data["shifts"].append({
            "name": shift.full_name,
            "username": shift.username,
            "user_id": shift.user_id,
            "start_time": shift.start_datetime.strftime("%d.%m.%Y %H:%M"),
            "end_time": shift.end_datetime.strftime("%d.%m.%Y %H:%M") if shift.end_datetime else None,
            "duration": shift.duration_str() if shift.duration() else "0ч 0м"
        })
    
    json_text = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    # Создаем файл
    file = BufferedInputFile(
        json_text.encode('utf-8'),
        filename=f"shifts_export_{datetime.now().strftime('%d%m%Y_%H%M%S')}.json"
    )
    
    await callback.message.answer_document(
        document=file,
        caption=f"📋 <b>JSON Экспорт</b>\n\n"
                f"✅ Завершенных смен: {len(completed_shifts)}\n"
                f"🔄 Активных смен: {len(storage.active_shifts)}",
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "export_txt")
async def admin_export_txt(callback: CallbackQuery):
    """Экспорт в TXT файлом"""
    if not await check_group_owner(callback.bot, callback.message.chat.id, callback.from_user.id):
        await callback.answer("🚫 Доступ запрещено!", show_alert=True)
        return
    
    import io
    from aiogram.types import BufferedInputFile
    from datetime import datetime
    
    # Только завершенные смены
    completed_shifts = [s for s in storage.shift_history if s.end_time]
    
    # Формируем TXT
    lines = [
        "ЭКСПОРТ ДАННЫХ БОТА",
        "=" * 50,
        f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
        f"Всего завершенных смен: {len(completed_shifts)}",
        f"Активных смен сейчас: {len(storage.active_shifts)}",
        "=" * 50,
        ""
    ]
    
    for shift in completed_shifts:
        date_str = shift.start_datetime.strftime("%d.%m.%Y")
        start_str = shift.start_datetime.strftime("%H:%M")
        end_str = shift.end_datetime.strftime("%H:%M") if shift.end_datetime else "—"
        duration = shift.duration_str() if shift.duration() else "0ч 0м"
        
        lines.append(f"{date_str} | {shift.full_name} | {start_str}-{end_str} | {duration}")
    
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"ИТОГО: {len(completed_shifts)} завершенных смен")
    
    txt_text = "\n".join(lines)
    
    # Создаем файл
    file = BufferedInputFile(
        txt_text.encode('utf-8'),
        filename=f"shifts_export_{datetime.now().strftime('%d%m%Y_%H%M%S')}.txt"
    )
    
    await callback.message.answer_document(
        document=file,
        caption=f"📝 <b>TXT Экспорт</b>\n\n"
                f"✅ Завершенных смен: {len(completed_shifts)}\n"
                f"🔄 Активных смен: {len(storage.active_shifts)}",
        parse_mode="HTML"
    )
    await callback.answer()
