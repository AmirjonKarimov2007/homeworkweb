from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    keyboard = [
        [KeyboardButton(text="My Groups"), KeyboardButton(text="Homework")],
        [KeyboardButton(text="Payments"), KeyboardButton(text="Materials")],
        [KeyboardButton(text="Notifications"), KeyboardButton(text="Profile")],
        [KeyboardButton(text="Help")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
