from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "Help")
async def help_message(message: Message):
    await message.answer("Use the menu to navigate: Homework, Payments, Materials, Notifications, Profile.")
