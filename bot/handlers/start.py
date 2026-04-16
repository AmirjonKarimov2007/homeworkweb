from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ContentType
from bot.services.api import api_client
from bot.keyboards.main import main_menu
from bot.keyboards.admin import admin_main_menu
from bot.config import ADMIN_IDS
from bot.utils.enums import Role

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Handle /start command"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if user is already linked
    resp = await api_client.me(telegram_id)

    if resp.get("success"):
        data = resp.get("data", {})
        role = data.get("role")
        is_admin = role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS

        if is_admin:
            await message.answer(f"Assalomu alaykum, {data.get('full_name', 'Admin')}!\n\nAdmin panelga xush kelibsiz.", reply_markup=admin_main_menu())
        else:
            student_name = data.get('full_name', 'O\'quvchi')
            await message.answer(f"Assalomu alaykum, {student_name}!\n\nAsosiy menyu:", reply_markup=main_menu())
        return

    # Not linked - ask for phone number
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni ulashish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Tizimga kirish uchun telefon raqamingizni ulashing.\n"
        "Telefon raqamingiz websitedagi profilingiz bilan mos kelishi kerak.",
        reply_markup=kb
    )


@router.message(F.contact)
async def capture_phone_contact(message: Message):
    """Capture phone number from contact"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if already linked
    resp = await api_client.me(telegram_id)
    if resp.get("success"):
        # Already linked, show menu
        data = resp.get("data", {})
        role = data.get("role")
        is_admin = role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS
        if is_admin:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=admin_main_menu())
        else:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=main_menu())
        return

    # Process phone from contact
    phone = message.contact.phone_number

    # Link with backend
    resp = await api_client.link_telegram(telegram_id, phone, username)

    if resp.get("success"):
        data = resp.get("data", {})
        role = data.get("role")
        is_admin = role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS

        full_name = data.get("full_name", "Foydalanuvchi")

        if is_admin:
            await message.answer(
                f"✅ Muvaffaqiyatli ulandi!\n\n"
                f"Ism: {full_name}\n"
                f"Rol: {role}\n\n"
                f"Admin panelga xush kelibsiz!",
                reply_markup=admin_main_menu()
            )
        else:
            groups = data.get("groups", [])
            group_text = ""
            if groups:
                group_text = "\n\nSizning guruhlaringiz:\n"
                for g in groups:
                    group_text += f"📚 {g['name']}\n"

            await message.answer(
                f"✅ Muvaffaqiyatli ulandi!\n\n"
                f"Ism: {full_name}\n"
                f"Rol: {role}{group_text}",
                reply_markup=main_menu()
            )
    else:
        detail = resp.get("detail", "Noma'lum xatolik")
        if "not found" in detail.lower():
            await message.answer(
                "❌ Bu telefon raqam bilan ro'yxatdan o'tilgan foydalanuvchi topilmadi.\n\n"
                "Iltimos, websitedagi profilingizdagi telefon raqamini tekshiring."
            )
        elif "not enrolled" in detail.lower():
            await message.answer(
                "❌ Siz hech qanday guruhga biriktirilmagansiz.\n\n"
                "Iltimos, administrator bilan bog'laning."
            )
        else:
            await message.answer(f"❌ Xatolik: {detail}\n\nIltimos, administrator bilan bog'laning.")


@router.message(F.text.regexp(r"^(\+?998\d{9}|998\d{9}|\d{9})$"))
async def capture_phone_text(message: Message):
    """Capture phone number from text input"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if already linked
    resp = await api_client.me(telegram_id)
    if resp.get("success"):
        
        # Already linked, don't process
        return

    # Process phone from text
    phone = message.text.strip()

    # Link with backend
    resp = await api_client.link_telegram(telegram_id, phone, username)

    if resp.get("success"):
        data = resp.get("data", {})
        role = data.get("role")
        is_admin = role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS

        full_name = data.get("full_name", "Foydalanuvchi")

        if is_admin:
            await message.answer(
                f"✅ Muvaffaqiyatli ulandi!\n\n"
                f"Ism: {full_name}\n"
                f"Rol: {role}\n\n"
                f"Admin panelga xush kelibsiz!",
                reply_markup=admin_main_menu()
            )
        else:
            groups = data.get("groups", [])
            group_text = ""
            if groups:
                group_text = "\n\nSizning guruhlaringiz:\n"
                for g in groups:
                    group_text += f"📚 {g['name']}\n"

            await message.answer(
                f"✅ Muvaffaqiyatli ulandi!\n\n"
                f"Ism: {full_name}\n"
                f"Rol: {role}{group_text}",
                reply_markup=main_menu()
            )
    else:
        detail = resp.get("detail", "Noma'lum xatolik")
        if "not found" in detail.lower():
            await message.answer(
                "❌ Bu telefon raqam bilan ro'yxatdan o'tilgan foydalanuvchi topilmadi.\n\n"
                "Iltimos, websitedagi profilingizdagi telefon raqamini tekshiring."
            )
        elif "not enrolled" in detail.lower():
            await message.answer(
                "❌ Siz hech qanday guruhga biriktirilmagansiz.\n\n"
                "Iltimos, administrator bilan bog'laning."
            )
        else:
            await message.answer(f"❌ Xatolik: {detail}\n\nIltimos, administrator bilan bog'laning.")
