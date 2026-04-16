from aiogram import Router, F
from aiogram.types import Message
from bot.services.api import api_client

router = Router()


@router.message(F.text == "Profile")
async def profile(message: Message):
    resp = await api_client.me(message.from_user.id)
    if not resp.get("success"):
        await message.answer("Profile not linked.")
        return
    data = resp.get("data", {})
    await message.answer(f"Name: {data.get('full_name')}\nRole: {data.get('role')}")
