from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu():
    keyboard = [
        [KeyboardButton(text="📚 Mening guruhlarim")],
        [KeyboardButton(text="📝 Uy ishi")],
        [KeyboardButton(text="💰 To'lovlar")],
        [KeyboardButton(text="📁 Materiallar")],
        [KeyboardButton(text="🔔 Bildirishnomalar")],
        [KeyboardButton(text="� Profil")],
        [KeyboardButton(text="❓ Yordam")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
