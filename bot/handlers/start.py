from aiogram import Router, F
from aiogram.filters import CommandStart, CallbackQuery
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.services.database import db_service
from bot.keyboards.main import main_menu
from bot.keyboards.admin import admin_main_menu
from bot.keyboards.homework import homework_navigation_keyboard, lesson_homework_keyboard
from bot.config import ADMIN_IDS
from bot.utils.enums import Role

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Handle /start command"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if user is already linked
    user = await db_service.find_user_by_telegram_id(telegram_id)

    if user:
        # Already linked - show main menu
        if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS:
            await message.answer(f"Assalomu alaykum, {user.full_name}!\n\nAdmin panelga xush kelibsiz.", reply_markup=admin_main_menu())
        else:
            # Show student menu with initial groups
            groups = await db_service.get_user_groups(user.id)
            if groups:
                await show_groups_menu(message, user.id)
            else:
                await message.answer(f"Assalomu alaykum, {user.full_name}!\n\nSizning guruhlaringiz yo'q.\n\nAsosiy menyu:", reply_markup=main_menu())


async def show_groups_menu(message: Message, user_id: int):
    """Show user's groups with inline keyboard"""
    groups = await db_service.get_user_groups(user_id)

    if not groups:
        await message.answer("Sizda hech qanday guruh yo'q.")
        return

    builder = InlineKeyboardBuilder()

    for group in groups:
        builder.add(InlineKeyboardButton(
            text=f"📚 {group.name}",
            callback_data=f"group_{group.id}"
        ))

    builder.adjust(1)

    await message.answer("Mening guruhlarim:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("group_"))
async def show_group_lessons(callback: CallbackQuery):
    """Show lessons for selected group"""
    group_id = int(callback.data.split("_")[1])

    lessons_data = await db_service.get_group_lessons(group_id, page=1, page_size=10)
    lessons = lessons_data["lessons"]
    total_pages = lessons_data["total_pages"]

    if not lessons:
        await callback.message.answer(f"Bu guruhda hali darslar tayyorlanmagan.")
        await callback.answer()
        return

    # Create keyboard with lessons navigation
    builder = InlineKeyboardBuilder()

    # Add lessons
    for lesson in lessons:
        lesson_date = lesson.date.strftime("%d.%m.%Y %H:%M") if lesson.date else "Noma'lum"
        lesson_text = f"📖 {lesson.title} ({lesson_date})"
        builder.add(InlineKeyboardButton(
            text=lesson_text,
            callback_data=f"lesson_{lesson.id}"
        ))

    # Add navigation buttons
    nav_buttons = []
    if lessons_data["page"] > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"group_{group_id}_page_{lessons_data['page'] - 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text="🔙 Asosiy",
        callback_data="main_menu"
    ))

    if lessons_data["page"] < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"group_{group_id}_page_{lessons_data['page'] + 1}"
        ))

    builder.row(*nav_buttons)
    builder.adjust(1)

    group_name = lessons["0"].group.name if lessons else "Guruh"
    await callback.message.answer(f"**{group_name}** - Darslar\n\n", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("group_"))
async def show_group_lessons_pagination(callback: CallbackQuery):
    """Handle lesson pagination"""
    if "page" not in callback.data:
        await callback.answer()
        return

    data_parts = callback.data.split("_")
    group_id = int(data_parts[1])
    page = int(data_parts[3])

    lessons_data = await db_service.get_group_lessons(group_id, page=page, page_size=10)
    lessons = lessons_data["lessons"]
    total_pages = lessons_data["total_pages"]

    if not lessons:
        await callback.message.edit_text("Bu sahifada darslar yo'q.")
        return

    # Create keyboard with lessons navigation
    builder = InlineKeyboardBuilder()

    # Add lessons
    for lesson in lessons:
        lesson_date = lesson.date.strftime("%d.%m.%Y %H:%M") if lesson.date else "Noma'lum"
        lesson_text = f"📖 {lesson.title} ({lesson_date})"
        builder.add(InlineKeyboardButton(
            text=lesson_text,
            callback_data=f"lesson_{lesson.id}"
        ))

    # Add navigation buttons
    nav_buttons = []
    if lessons_data["page"] > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"group_{group_id}_page_{lessons_data['page'] - 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text="🔙 Asosiy",
        callback_data="main_menu"
    ))

    if lessons_data["page"] < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"group_{group_id}_page_{lessons_data['page'] + 1}"
        ))

    builder.row(*nav_buttons)
    builder.adjust(1)

    group_name = lessons[0].group.name if lessons else "Guruh"
    await callback.message.edit_text(f"**{group_name}** - Darslar ( sahifa {lessons_data['page']}/{total_pages} )\n\n", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("lesson_"))
async def show_lesson_details(callback: CallbackQuery):
    """Show lesson details with homework"""
    lesson_id = int(callback.data.split("_")[1])

    lesson = await db_service.get_lesson_by_id(lesson_id)
    if not lesson:
        await callback.message.answer("Dars topilmadi.")
        await callback.answer()
        return

    # Show lesson details
    lesson_info = f"""
**{lesson.title}**

📝 Tavsifi: {lesson.description or "Tavsif berilmagan"}

📅 Vaqti: {lesson.date.strftime("%d.%m.%Y %H:%M") if lesson.date else "Noma'lum"}

📍 Joyi: {lesson.location or "Aniq joy berilmagan"}
"""

    # Check if user has homework for this lesson
    telegram_id = callback.from_user.id
    user = await db_service.find_user_by_telegram_id(telegram_id)

    if user:
        # Get homework for this lesson
        homework_data = await db_service.get_user_homework(user.id)
        lesson_homework = None
        for hw in homework_data["homework"]:
            if hw.lesson_id == lesson_id:
                lesson_homework = hw
                break

        if lesson_homework:
            homework_info = f"""
📚 Uy ishi:
- {lesson_homework.title}
- Muddati: {lesson_homework.due_date.strftime("%d.%m.%Y") if lesson_homework.due_date else "Noma'lum"}
- Holati: {lesson_homework.status.value}
"""
            lesson_info += homework_info

            # Add submit button for pending homework
            if lesson_homework.status.value == "pending":
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="📝 Uy ishini topshirish",
                    callback_data=f"submit_hw_{lesson_homework.id}"
                ))
                builder.add(InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data=f"group_{lesson.group.id}"
                ))
                builder.adjust(1)

                await callback.message.answer(lesson_info, reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="👀 Uy ishini ko'rish",
                    callback_data=f"view_hw_{lesson_homework.id}"
                ))
                builder.add(InlineKeyboardButton(
                    text="🔙 Orqaga",
                    callback_data=f"group_{lesson.group.id}"
                ))
                builder.adjust(1)

                await callback.message.answer(lesson_info, reply_markup=builder.as_markup())
        else:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data=f"group_{lesson.group.id}"
            ))
            builder.adjust(1)

            await callback.message.answer(lesson_info, reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"group_{lesson.group.id}"
        ))
        builder.adjust(1)

        await callback.message.answer(lesson_info, reply_markup=builder.as_markup())

    await callback.answer()
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
    user = await db_service.find_user_by_telegram_id(telegram_id)
    if user:
        # Already linked, show menu
        if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=admin_main_menu())
        else:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=main_menu())
        return

    # Process phone from contact
    phone = message.contact.phone_number

    # Link user directly to database
    db_user = await db_service.find_user_by_phone(phone)
    if not db_user:
        await message.answer(
            "❌ Bu telefon raqam bilan ro'yxatdan o'tilgan foydalanuvchi topilmadi.\n\n"
            "Iltimos, websitedagi profilingizdagi telefon raqamini tekshiring."
        )
        return

    # Check if user is enrolled in any group
    groups = await db_service.get_user_groups(db_user.id)
    if not groups:
        await message.answer(
            "❌ Siz hech qanday guruhga biriktirilmagansiz.\n\n"
            "Iltimos, administrator bilan bog'laning."
        )
        return

    # Link telegram to user
    success = await db_service.link_telegram_to_user(db_user.id, telegram_id, username)
    if not success:
        await message.answer(
            "❌ Telegram akkauntingiz allaqachon boshqa foydalanuvchi bilan bog'langan.\n\n"
            "Iltimos, administrator bilan bog'laning."
        )
        return

    # Show success message
    if db_user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS:
        await message.answer(
            f"✅ Muvaffaqiyatli ulandi!\n\n"
            f"Ism: {db_user.full_name}\n"
            f"Rol: {db_user.role.value}\n\n"
            f"Admin panelga xush kelibsiz!",
            reply_markup=admin_main_menu()
        )
    else:
        groups_text = "\n\nSizning guruhlaringiz:\n"
        for group in groups:
            groups_text += f"📚 {group.name}\n"

        await message.answer(
            f"✅ Muvaffaqiyatli ulandi!\n\n"
            f"Ism: {db_user.full_name}\n"
            f"Rol: {db_user.role.value}{groups_text}",
            reply_markup=main_menu()
        )


@router.message(F.text.regexp(r"^(\+?998\d{9}|998\d{9}|\d{9})$"))
async def capture_phone_text(message: Message):
    """Capture phone number from text input"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if already linked
    user = await db_service.find_user_by_telegram_id(telegram_id)
    if user:
        # Already linked, show menu
        if user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=admin_main_menu())
        else:
            await message.answer("Siz allaqachon tizimga ulangan.", reply_markup=main_menu())
        return

    # Process phone from text
    phone = message.text.strip()

    # Link user directly to database
    db_user = await db_service.find_user_by_phone(phone)
    if not db_user:
        await message.answer(
            "❌ Bu telefon raqam bilan ro'yxatdan o'tilgan foydalanuvchi topilmadi.\n\n"
            "Iltimos, websitedagi profilingizdagi telefon raqamini tekshiring."
        )
        return

    # Check if user is enrolled in any group
    groups = await db_service.get_user_groups(db_user.id)
    if not groups:
        await message.answer(
            "❌ Siz hech qanday guruhga biriktirilmagansiz.\n\n"
            "Iltimos, administrator bilan bog'laning."
        )
        return

    # Link telegram to user
    success = await db_service.link_telegram_to_user(db_user.id, telegram_id, username)
    if not success:
        await message.answer(
            "❌ Telegram akkauntingiz allaqachon boshqa foydalanuvchi bilan bog'langan.\n\n"
            "Iltimos, administrator bilan bog'laning."
        )
        return

    # Show success message
    if db_user.role in [Role.ADMIN.value, Role.SUPER_ADMIN.value, Role.TEACHER.value] or telegram_id in ADMIN_IDS:
        await message.answer(
            f"✅ Muvaffaqiyatli ulandi!\n\n"
            f"Ism: {db_user.full_name}\n"
            f"Rol: {db_user.role.value}\n\n"
            f"Admin panelga xush kelibsiz!",
            reply_markup=admin_main_menu()
        )
    else:
        groups_text = "\n\nSizning guruhlaringiz:\n"
        for group in groups:
            groups_text += f"📚 {group.name}\n"

        await message.answer(
            f"✅ Muvaffaqiyatli ulandi!\n\n"
            f"Ism: {db_user.full_name}\n"
            f"Rol: {db_user.role.value}{groups_text}",
            reply_markup=main_menu()
        )
