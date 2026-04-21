from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def homework_navigation_keyboard(page: int = 1, total_pages: int = 1):
    """Create navigation keyboard for homework list"""
    builder = InlineKeyboardBuilder()

    # Homework items would be added dynamically

    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"hw_page_{page - 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text="🔙 Asosiy",
        callback_data="main_menu"
    ))

    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"hw_page_{page + 1}"
        ))

    builder.row(*nav_buttons)
    builder.adjust(1)

    return builder.as_markup()


def lesson_homework_keyboard(homework_id: int, has_homework: bool = False):
    """Create keyboard for lesson homework actions"""
    builder = InlineKeyboardBuilder()

    if has_homework:
        builder.add(InlineKeyboardButton(
            text="📝 Uy ishini topshirish",
            callback_data=f"submit_hw_{homework_id}"
        ))
    else:
        builder.add(InlineKeyboardButton(
            text="👀 Uy ishini ko'rish",
            callback_data=f"view_hw_{homework_id}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="main_menu"
    ))

    builder.adjust(1)
    return builder.as_markup()


def admin_homework_keyboard(homework_id: int):
    """Create keyboard for admin homework actions"""
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(
        text="📊 Barcha topshiruvchilar",
        callback_data=f"view_hw_submissions_{homework_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="✅ Bajarilganlar",
        callback_data=f"hw_completed_{homework_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="⏳ Bajarilmaganlar",
        callback_data=f"hw_pending_{homework_id}"
    ))

    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="main_menu"
    ))

    builder.adjust(2)
    return builder.as_markup()