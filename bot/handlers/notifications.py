from aiogram import Router, F
from aiogram.types import Message
from bot.services.api import api_client

router = Router()


@router.message(F.text == "Notifications")
async def notifications_menu(message: Message):
    resp = await api_client.notifications(message.from_user.id)
    if not resp.get("success") or not resp.get("data"):
        await message.answer("No new notifications.")
        return

    for n in resp["data"]:
        await message.answer(f"{n['title']}\n{n.get('body','')}")
