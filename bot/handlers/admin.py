from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.services.database import db_service
from bot.config import ADMIN_IDS
from bot.keyboards.admin import admin_main_menu

router = Router()


# ==================== STATES ====================

class NotificationStates(StatesGroup):
    select_target = State()
    enter_title = State()
    enter_body = State()


class HomeworkCheckStates(StatesGroup):
    select_homework = State()


# ==================== MAIN ADMIN MENU ====================

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    """Show admin statistics"""
    # Get all groups
    groups = await db_service.get_all_groups()

    if not groups:
        await message.answer("Hozirda hech qanday guruh yo'q.")
        return

    stats_text = "📊 Umumiy statistika\n\n"

    for group in groups:
        group_stats = await db_service.get_group_statistics(group.id)
        stats_text += f"**{group_stats['group_name']}**\n"
        stats_text += f"   📚 Talabalar: {group_stats['total_students']}\n"
        stats_text += f"   📝 Uy ishlari: {group_stats['homework_count']}\n\n"

    await message.answer(stats_text)


@router.message(F.text == "👥 Barcha guruhlar")
async def show_all_groups(message: Message):
    """Show all groups with admin actions"""
    groups = await db_service.get_all_groups()

    if not groups:
        await message.answer("Hozirda hech qanday guruh yo'q.")
        return

    builder = InlineKeyboardBuilder()

    for group in groups:
        builder.add(InlineKeyboardButton(
            text=f"📚 {group.name}",
            callback_data=f"admin_group_{group.id}"
        ))

    builder.adjust(1)
    await message.answer("Barcha guruhlar:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin_group_"))
async def show_admin_group_details(callback: CallbackQuery):
    """Show group details with admin actions"""
    group_id = int(callback.data.split("_")[2])

    group = await db_service.get_group_by_id(group_id)
    if not group:
        await callback.message.answer("Guruh topilmadi.")
        await callback.answer()
        return

    # Get group users
    users = await db_service.get_users_by_group(group_id)

    text = f"""
**{group.name}**

📅 Yaratilgan: {group.created_at.strftime("%d.%m.%Y %H:%M")}
👨‍🎓 Talabalar soni: {len(users)}
📝 Uy ishlari soni: 0  # TODO: Add this count
"""

    # Create keyboard
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="👨‍🎓 Talabalar ro'yxati",
        callback_data=f"admin_group_users_{group_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="📝 Uy ishlari",
        callback_data=f"admin_group_homework_{group_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="📊 Statistika",
        callback_data=f"admin_group_stats_{group_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="🔙 Guruhlar ro'yxati",
        callback_data="admin_all_groups"
    ))

    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_group_users_"))
async def show_group_users(callback: CallbackQuery):
    """Show users in specific group"""
    group_id = int(callback.data.split("_")[3])

    users = await db_service.get_users_by_group(group_id)

    if not users:
        await callback.message.answer("Bu guruhda talabalar yo'q.")
        await callback.answer()
        return

    text = f"""
**Guruhdagi talabalar ({len(users)}):**
"""

    for user in users:
        text += f"\n• {user.full_name} ({user.phone})"

    # Add back button
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=f"admin_group_{group_id}"
    ))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_group_homework_"))
async def show_group_homework(callback: CallbackQuery):
    """Show homework for specific group"""
    group_id = int(callback.data.split("_")[3])

    # Get user's groups (for admin)
    groups = await db_service.get_all_groups()

    # Get homework for first group as placeholder
    if groups:
        homework_data = await db_service.get_user_homework(groups[0].id)
        homework_list = homework_data["homework"]

        if homework_list:
            text = f"""
**{groups[0].name} - Uy ishlari**

"""
            for homework in homework_list[:5]:  # Show first 5
                text += f"\n📝 {homework.title}\n"
                text += f"   Muddati: {homework.due_date.strftime('%d.%m.%Y') if homework.due_date else 'Noma\'lum'}\n"
                text += f"   Holati: {homework.status.value}\n"

            if len(homework_list) > 5:
                text += f"\n... va yana {len(homework_list) - 5} ta uy ishi"

            # Add buttons
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data=f"admin_group_{group_id}"
            ))
            builder.adjust(1)

            await callback.message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await callback.message.edit_text(f"Bu guruhda hali uy ishlari tayyorlanmagan.")
    else:
        await callback.message.edit_text("Hech qanday guruh yo'q.")

    await callback.answer()


@router.callback_query(F.data.startswith("admin_group_stats_"))
async def show_group_homework_stats(callback: CallbackQuery):
    """Show homework statistics for group"""
    group_id = int(callback.data.split("_")[3])

    # TODO: Implement group homework statistics
    # For now, show placeholder
    await callback.message.edit_text("Bu funksiya hali implementatsiya qilinmagan.")
    await callback.answer()


@router.message(F.text == "📢 Xabar yuborish")
async def show_send_notification_menu(message: Message, state: FSMContext):
    """Show notification sending options"""
    await state.set_state(NotificationStates.select_target)

    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="🎓 Hamma talabalarga",
        callback_data="send_all"
    ))

    builder.add(InlineKeyboardButton(
        text="📚 Guruhga",
        callback_data="send_group"
    ))

    builder.add(InlineKeyboardButton(
        text="🔙 Bekor qilish",
        callback_data="notif_cancel"
    ))

    builder.adjust(1)

    await message.answer("Bildirishnomani kim yuborishni tanlang:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "send_all")
async def send_to_all(callback: CallbackQuery, state: FSMContext):
    """Start sending notification to all"""
    await state.update_data(target_type="all")
    await state.set_state(NotificationStates.enter_title)
    await callback.message.edit_text("E'lon sarlavhasini kiriting:")
    await callback.answer()


@router.callback_query(F.data == "send_group")
async def send_to_group(callback: CallbackQuery, state: FSMContext):
    """Start sending notification to group"""
    groups = await db_service.get_all_groups()

    if not groups:
        await callback.message.edit_text("Hech qanday guruh yo'q.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.add(InlineKeyboardButton(
            text=f"📚 {group.name}",
            callback_data=f"send_group_{group.id}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Bekor qilish",
        callback_data="notif_cancel"
    ))

    builder.adjust(1)
    await callback.message.edit_text("Guruhni tanlang:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("send_group_"))
async def select_group_for_notification(callback: CallbackQuery, state: FSMContext):
    """Select specific group for notification"""
    group_id = int(callback.data.split("_")[2])
    await state.update_data(target_type="group", target_id=group_id)
    await state.set_state(NotificationStates.enter_title)
    await callback.message.edit_text("E'lon sarlavhasini kiriting:")
    await callback.answer()


@router.callback_query(F.data == "notif_cancel")
async def cancel_notification(callback: CallbackQuery, state: FSMContext):
    """Cancel notification flow"""
    await state.clear()
    await callback.message.edit_text"Bekor qilindi.")
    await callback.answer()


@router.message(NotificationStates.enter_title)
async def enter_notification_title(message: Message, state: FSMContext):
    """Enter notification title"""
    if not message.text:
        await message.answer("Iltimos, sarlavhani kiriting:")
        return
    await state.update_data(title=message.text)
    await state.set_state(NotificationStates.enter_body)
    await message.answer("E'lon matnini kiriting:")


@router.message(NotificationStates.enter_body)
async def enter_notification_body(message: Message, state: FSMContext, bot: Bot):
    """Enter notification body and send"""
    data = await state.get_data()

    # Send notification
    success = await db_service.send_notification(
        target_type=data.get("target_type", "all"),
        target_id=data.get("target_id"),
        title=data["title"],
        body=message.text,
        notification_type="announcement"
    )

    if not success:
        await message.answer("Xatolik yuz berdi.")
        await state.clear()
        return

    await message.answer("✅ E'lon muvaffaqiyatli yuborildi!")
    await state.clear()


@router.message(F.text == "📝 Uy ishlarni tekshirish")
async def check_homework_menu(message: Message, state: FSMContext):
    """Show homework checking options"""
    await state.set_state(HomeworkCheckStates.select_homework)

    # Get all groups and their homework
    groups = await db_service.get_all_groups()

    if not groups:
        await message.answer("Hech qanday guruh yo'q.")
        return

    builder = InlineKeyboardBuilder()

    for group in groups:
        builder.add(InlineKeyboardButton(
            text=f"📚 {group.name}",
            callback_data=f"check_group_{group.id}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Bekor qilish",
        callback_data="homework_check_cancel"
    ))

    builder.adjust(1)
    await message.answer("Qaysi guruhning uy ishlarini tekshirmoqchisiz?", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("check_group_"))
async def check_group_homework(callback: CallbackQuery, state: FSMContext):
    """Show homework for specific group"""
    group_id = int(callback.data.split("_")[2])

    # Get homework for this group
    homework_data = await db_service.get_user_homework_for_group(group_id)  # TODO: Implement this method

    if not homework_data or not homework_data["homework"]:
        await callback.message.edit_text("Bu guruhda hali uy ishlari tayyorlanmagan.")
        await callback.answer()
        return

    homework_list = homework_data["homework"]
    text = f"""
**Uy ishlarni tekshirish - {homework_data['group_name']}**

"""

    for homework in homework_list:
        # Get homework statistics
        hw_stats = await db_service.get_homework_statistics(homework.id)
        completion_rate = hw_stats.get("completion_rate", 0)

        text += f"\n📝 **{homework.title}**\n"
        text += f"   Muddati: {homework.due_date.strftime('%d.%m.%Y') if homework.due_date else 'Noma\'lum'}\n"
        text += f"   Bajarish: {completion_rate:.1f}%\n"

    # Add buttons to view detailed homework
    builder = InlineKeyboardBuilder()
    for homework in homework_list[:3]:  # Show first 3
        builder.add(InlineKeyboardButton(
            text=f"📝 {homework.title}",
            callback_data=f"check_hw_{homework.id}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="homework_check_cancel"
    ))

    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("check_hw_"))
async def check_homework_details(callback: CallbackQuery):
    """Check specific homework details"""
    homework_id = int(callback.data.split("_")[2])

    # Get homework details
    homework = await db_service.get_homework_by_id(homework_id)
    if not homework:
        await callback.message.answer("Uy ishi topilmadi.")
        await callback.answer()
        return

    # Get all submissions
    submissions = await db_service.get_homework_submissions(homework_id)

    # Calculate statistics
    total = len(submissions)
    completed = sum(1 for s in submissions if s["status"] == "completed")

    text = f"""
**Uy Ishi - {homework.title}**

📝 Tavsifi: {homework.description or "Tavsif berilmagan"}
📅 Muddati: {homework.due_date.strftime('%d.%m.%Y') if homework.due_date else 'Noma\'lum'}
📊 Bajarish: {completed}/{total} ({(completed/total*100):.1f}%)

**Topshiruvchilar ({total} ta):**
"""

    for submission in submissions:
        status_emoji = "✅" if submission["status"] == "completed" else "⏳"
        text += f"\n{status_emoji} {submission['user_name']}"
        text += f" - {submission['submitted_at'].strftime('%d.%m.%Y %H:%M')}"

    # Add admin buttons
    builder = InlineKeyboardBuilder()

    if completed < total:
        builder.add(InlineKeyboardButton(
            text="⏳ Bajarilmaganlar",
            callback_data=f"pending_hw_{homework_id}"
        ))

    if completed > 0:
        builder.add(InlineKeyboardButton(
            text="✅ Bajarilganlar",
            callback_data=f"completed_hw_{homework_id}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="homework_check_cancel"
    ))

    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("pending_hw_"))
async def show_pending_homework(callback: CallbackQuery):
    """Show pending homework submissions"""
    homework_id = int(callback.data.split("_")[2])

    submissions = await db_service.get_homework_submissions(homework_id)
    pending = [s for s in submissions if s["status"] != "completed"]

    if not pending:
        await callback.message.answer("Bajarilmagan topshiruvchilar yo'q.")
        await callback.answer()
        return

    text = f"""
**Bajarilmagan uy ishlari - {len(pending)} ta:**
"""

    for submission in pending:
        text += f"\n⏳ {submission['user_name']}"
        text += f" - Topshirilgan: {submission['submitted_at'].strftime('%d.%m.%Y %H:%M')}"
        text += f"\n   Text: {submission['text'][:100]}{'...' if len(submission['text']) > 100 else ''}\n"

    # Add back button
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=f"check_hw_{homework_id}"
    ))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("completed_hw_"))
async def show_completed_homework(callback: CallbackQuery):
    """Show completed homework submissions"""
    homework_id = int(callback.data.split("_")[2])

    submissions = await db_service.get_homework_submissions(homework_id)
    completed = [s for s in submissions if s["status"] == "completed"]

    if not completed:
        await callback.message.answer("Bajarilgan topshiruvchilar yo'q.")
        await callback.answer()
        return

    text = f"""
**Bajarilgan uy ishlari - {len(completed)} ta:**
"""

    for submission in completed:
        text += f"\n✅ {submission['user_name']}"
        text += f" - Topshirilgan: {submission['submitted_at'].strftime('%d.%m.%Y %H:%M')}"
        text += f"\n   Text: {submission['text'][:100]}{'...' if len(submission['text']) > 100 else ''}\n"

    # Add back button
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=f"check_hw_{homework_id}"
    ))
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "homework_check_cancel")
async def cancel_homework_check(callback: CallbackQuery, state: FSMContext):
    """Cancel homework check flow"""
    await state.clear()
    await callback.message.edit_text"Bekor qilindi.")
    await callback.answer()


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message):
    """Go back to main menu"""
    await message.answer("Asosiy menyu", reply_markup=admin_main_menu())