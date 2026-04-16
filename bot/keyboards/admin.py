from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ==================== MAIN KEYBOARD ====================

def admin_main_menu():
    """Admin main menu with all admin functions"""
    keyboard = [
        [KeyboardButton(text="📢 E'lon yuborish")],
        [KeyboardButton(text="📝 Uy ishi yaratish (WebApp)"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👥 Guruhlar"), KeyboardButton(text="🔙 Asosiy menyu")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ==================== NOTIFICATION TARGET SELECTION ====================

def notification_target_keyboard():
    """Select notification target: All, Group, User"""
    keyboard = [
        [
            InlineKeyboardButton(text="📢 Barchaga", callback_data="notif_target_all"),
            InlineKeyboardButton(text="👥 Guruhga", callback_data="notif_target_group"),
        ],
        [InlineKeyboardButton(text="👤 Shaxsiy", callback_data="notif_target_user")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="notif_cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== GROUP SELECTION ====================

async def group_selection_keyboard(groups: list):
    """Select a group for notification or homework"""
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=f"{group['name']}", callback_data=f"group_{group['id']}")
    builder.button(text="🔙 Orqaga", callback_data="cancel_group_select")
    return builder.as_markup()


# ==================== NOTIFICATION TYPE SELECTION ====================

def notification_type_keyboard():
    """Select notification type"""
    keyboard = [
        [
            InlineKeyboardButton(text="📢 E'lon", callback_data="notif_type_announcement"),
            InlineKeyboardButton(text="📝 Uy ishi", callback_data="notif_type_homework"),
        ],
        [
            InlineKeyboardButton(text="💳 To'lov", callback_data="notif_type_payment"),
            InlineKeyboardButton(text="📚 Dars", callback_data="notif_type_lesson"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="notif_cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== STATS KEYBOARD ====================

def stats_keyboard():
    """Statistics menu with refresh option"""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="stats_refresh"),
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="stats_back"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== GROUP LIST KEYBOARD ====================

async def groups_list_keyboard(groups: list):
    """Show all groups with options"""
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=f"📚 {group['name']}", callback_data=f"group_detail_{group['id']}")
    builder.button(text="🔙 Orqaga", callback_data="groups_back")
    return builder.as_markup()


def group_detail_keyboard(group_id: int):
    """Options for a specific group"""
    keyboard = [
        [
            InlineKeyboardButton(text="👥 O'quvchilar", callback_data=f"group_students_{group_id}"),
            InlineKeyboardButton(text="📝 Uy ishlari", callback_data=f"group_homework_{group_id}"),
        ],
        [
            InlineKeyboardButton(text="📢 Guruhga e'lon", callback_data=f"group_announce_{group_id}"),
            InlineKeyboardButton(text="📝 Uy ishi yaratish", callback_data=f"group_homework_create_{group_id}"),
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="group_detail_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ==================== WEBAPP KEYBOARD ====================

def webapp_keyboard(webapp_url: str):
    """Open webapp button"""
    keyboard = [
        [KeyboardButton(text="🌐 Webapp ochish", web_app={"url": webapp_url})],
        [KeyboardButton(text="🔙 Orqaga")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ==================== CONFIRMATION KEYBOARD ====================

def confirm_keyboard(action: str):
    """Confirm action"""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_{action}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
