import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from bot.services.api import api_client
from bot.config import WEBAPP_URL, ADMIN_IDS
from bot.keyboards.admin import (
    admin_main_menu,
    notification_target_keyboard,
    notification_type_keyboard,
    stats_keyboard,
    groups_list_keyboard,
    group_detail_keyboard,
    webapp_keyboard,
)

router = Router()


# ==================== STATES ====================

class NotificationStates(StatesGroup):
    select_target = State()
    select_group = State()
    select_type = State()
    enter_title = State()
    enter_body = State()


# ==================== MAIN ADMIN MENU ====================

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    """Show statistics to admin"""
    resp = await api_client.admin_stats()
    if not resp.get("success"):
        await message.answer("Statistikani olib bo'lmadi.")
        return

    data = resp["data"]
    text = (
        f"📊 Bugungi statistika\n\n"
        f"📝 Uy ishi topshirganlar: {data.get('today_homework_submitted', 0)}\n"
        f"❌ Uy ishi topshirmaganlar: {data.get('today_homework_not_submitted', 0)}\n"
        f"💳 Bugungi tushum: {data.get('today_payment_received', 0):,} so'm\n"
        f"👥 Jami o'quvchilar: {data.get('total_students', 0)}"
    )
    await message.answer(text, reply_markup=stats_keyboard())


@router.callback_query(F.data == "stats_refresh")
async def refresh_stats(callback: CallbackQuery):
    """Refresh statistics"""
    resp = await api_client.admin_stats()
    if not resp.get("success"):
        await callback.message.edit_text("Statistikani olib bo'lmadi.")
        return

    data = resp["data"]
    text = (
        f"📊 Bugungi statistika\n\n"
        f"📝 Uy ishi topshirganlar: {data.get('today_homework_submitted', 0)}\n"
        f"❌ Uy ishi topshirmaganlar: {data.get('today_homework_not_submitted', 0)}\n"
        f"💳 Bugungi tushum: {data.get('today_payment_received', 0):,} so'm\n"
        f"👥 Jami o'quvchilar: {data.get('total_students', 0)}"
    )
    await callback.message.edit_text(text, reply_markup=stats_keyboard())
    await callback.answer("Yangilandi")


@router.callback_query(F.data == "stats_back")
async def stats_back(callback: CallbackQuery):
    """Go back from stats"""
    await callback.message.answer("Admin paneliga qaytdingiz.", reply_markup=admin_main_menu())
    await callback.answer()


# ==================== NOTIFICATIONS ====================

@router.message(F.text == "📢 E'lon yuborish")
async def send_announcement(message: Message, state: FSMContext):
    """Start notification sending flow"""
    await state.set_state(NotificationStates.select_target)
    await message.answer(
        "Qaysi guruhga yuborasiz?",
        reply_markup=notification_target_keyboard()
    )


@router.callback_query(NotificationStates.select_target, F.data.startswith("notif_target_"))
async def select_notification_target(callback: CallbackQuery, state: FSMContext):
    """Handle target selection"""
    target_type = callback.data.split("_")[2]

    if target_type == "all":
        await state.update_data(target_type="all", target_id=None)
        await state.set_state(NotificationStates.select_type)
        await callback.message.edit_text(
            "E'lon turini tanlang:",
            reply_markup=notification_type_keyboard()
        )
    elif target_type == "group":
        await state.update_data(target_type="group")
        await state.set_state(NotificationStates.select_group)
        # Get groups
        resp = await api_client.groups_for_admin()
        if not resp.get("success") or not resp.get("data"):
            await callback.message.edit_text("Guruhlar topilmadi.")
            return
        from bot.keyboards.admin import group_selection_keyboard
        await callback.message.edit_text(
            "Guruhni tanlang:",
            reply_markup=await group_selection_keyboard(resp["data"])
        )
    elif target_type == "user":
        await callback.message.edit_text(
            "📝 O'quvchining telegram ID sini kiriting:",
            reply_markup=None
        )
        await state.set_state(NotificationStates.select_type)
        await state.update_data(target_type="user")
    await callback.answer()


@router.callback_query(NotificationStates.select_group, F.data.startswith("group_"))
async def select_group_for_notification(callback: CallbackQuery, state: FSMContext):
    """Handle group selection"""
    group_id = int(callback.data.split("_")[1])
    await state.update_data(target_id=group_id)
    await state.set_state(NotificationStates.select_type)
    await callback.message.edit_text(
        "E'lon turini tanlang:",
        reply_markup=notification_type_keyboard()
    )
    await callback.answer()


@router.message(NotificationStates.select_target, F.contact)
async def select_user_by_contact(message: Message, state: FSMContext):
    """Select user by contact (not implemented for now)"""
    await message.answer("Iltimos, guruh yoki 'barcha' ni tanlang.")
    await state.set_state(NotificationStates.select_target)
    await message.answer(
        "Qaysi guruhga yuborasiz?",
        reply_markup=notification_target_keyboard()
    )


@router.callback_query(NotificationStates.select_type, F.data.startswith("notif_type_"))
async def select_notification_type(callback: CallbackQuery, state: FSMContext):
    """Handle notification type selection"""
    notif_type = callback.data.split("_")[2]
    await state.update_data(notification_type=notif_type)
    await state.set_state(NotificationStates.enter_title)
    await callback.message.edit_text(
        f"E'lon sarlavhasini kiriting (Turi: {notif_type}):",
        reply_markup=None
    )
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
    resp = await api_client.send_notification(
        sent_by=message.from_user.id,
        target_type=data.get("target_type", "all"),
        target_id=data.get("target_id"),
        title=data["title"],
        body=message.text,
        notification_type=data.get("notification_type", "announcement")
    )

    if not resp.get("success"):
        await message.answer("Xatolik yuz berdi.")
        await state.clear()
        return

    telegram_ids = resp.get("telegram_ids", [])
    count = resp.get("count", 0)

    # Send to each telegram user
    sent_count = 0
    for tg_id in telegram_ids:
        try:
            text = f"🔔 {data['title']}\n\n{message.text}"
            await bot.send_message(tg_id, text)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {tg_id}: {e}")

    await message.answer(
        f"✅ E'lon {sent_count}/{count} ta foydalanuvchiga yuborildi!",
        reply_markup=admin_main_menu()
    )
    await state.clear()


@router.callback_query(F.data == "notif_cancel")
async def cancel_notification(callback: CallbackQuery, state: FSMContext):
    """Cancel notification flow"""
    await state.clear()
    await callback.message.edit_text("Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "cancel_group_select")
async def cancel_group_select(callback: CallbackQuery, state: FSMContext):
    """Cancel group selection"""
    await state.clear()
    await callback.message.answer("Qaysi guruhga yuborasiz?", reply_markup=notification_target_keyboard())
    await callback.answer()


# ==================== GROUPS ====================

@router.message(F.text == "👥 Guruhlar")
async def show_groups(message: Message):
    """Show all groups"""
    resp = await api_client.groups_for_admin()
    if not resp.get("success") or not resp.get("data"):
        await message.answer("Guruhlar topilmadi.")
        return

    text = "📚 Guruhlar ro'yxati:\n\n"
    for group in resp["data"]:
        text += f"📖 {group['name']}\n"
    await message.answer(text, reply_markup=await groups_list_keyboard(resp["data"]))


@router.callback_query(F.data.startswith("group_detail_"))
async def group_detail(callback: CallbackQuery):
    """Show group detail"""
    group_id = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        f"Guruh #{group_id} boshqaruv menyu",
        reply_markup=group_detail_keyboard(group_id)
    )
    await callback.answer()


@router.callback_query(F.data == "groups_back")
async def groups_back(callback: CallbackQuery):
    """Go back from groups"""
    resp = await api_client.groups_for_admin()
    if not resp.get("success") or not resp.get("data"):
        await callback.message.answer("Admin paneliga qaytdingiz.", reply_markup=admin_main_menu())
        return
    text = "📚 Guruhlar ro'yxati:\n\n"
    for group in resp["data"]:
        text += f"📖 {group['name']}\n"
    await callback.message.edit_text(text, reply_markup=await groups_list_keyboard(resp["data"]))
    await callback.answer()


@router.callback_query(F.data == "group_detail_back")
async def group_detail_back(callback: CallbackQuery):
    """Go back from group detail"""
    resp = await api_client.groups_for_admin()
    if not resp.get("success") or not resp.get("data"):
        await callback.message.answer("Admin paneliga qaytdingiz.", reply_markup=admin_main_menu())
        return
    text = "📚 Guruhlar ro'yxati:\n\n"
    for group in resp["data"]:
        text += f"📖 {group['name']}\n"
    await callback.message.edit_text(text, reply_markup=await groups_list_keyboard(resp["data"]))
    await callback.answer()


@router.callback_query(F.data.startswith("group_students_"))
async def group_students(callback: CallbackQuery):
    """Show group students"""
    group_id = int(callback.data.split("_")[2])
    resp = await api_client.users_by_group(group_id)
    if not resp.get("success") or not resp.get("data"):
        await callback.answer("O'quvchilar topilmadi.", show_alert=True)
        return

    users = resp["data"]
    text = f"👥 Guruh #{group_id} o'quvchilari:\n\n"
    for i, user in enumerate(users, 1):
        name = user.get('full_name', 'Noma\'lum')
        tid = user.get('telegram_id', 'N/A')
        text += f"{i}. {name} (ID: {tid})\n"
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("group_homework_"))
async def group_homework(callback: CallbackQuery):
    """Show group homework (placeholder)"""
    await callback.answer("Bu funksiya hozircha ishlab chiqilmoqda.", show_alert=True)


@router.callback_query(F.data.startswith("group_announce_"))
async def group_announce(callback: CallbackQuery, state: FSMContext):
    """Announce to group"""
    group_id = int(callback.data.split("_")[2])
    await state.update_data(target_type="group", target_id=group_id, notification_type="announcement")
    await state.set_state(NotificationStates.enter_title)
    await callback.message.edit_text("E'lon sarlavhasini kiriting:")
    await callback.answer()


# ==================== WEBAPP HOMEWORK ====================

@router.message(F.text == "📝 Uy ishi yaratish (WebApp)")
async def open_homework_webapp(message: Message):
    """Open webapp for homework creation"""
    url = f"{WEBAPP_URL}?action=create_homework&telegram_id={message.from_user.id}"
    await message.answer(
        "Uy ishi yaratish uchun WebApp ochilmoqda...",
        reply_markup=webapp_keyboard(url)
    )


@router.callback_query(F.data.startswith("group_homework_create_"))
async def group_homework_create(callback: CallbackQuery):
    """Create homework for group via webapp"""
    group_id = int(callback.data.split("_")[3])
    url = f"{WEBAPP_URL}?action=create_homework&telegram_id={callback.from_user.id}&group_id={group_id}"
    await callback.message.edit_text(
        f"WebApp ochilmoqda (Guruh: {group_id})...",
        reply_markup=None
    )
    await callback.answer()


# ==================== BACK TO MAIN ====================

@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message):
    """Go back to main menu"""
    await message.answer("Asosiy menyu", reply_markup=admin_main_menu())
