from aiogram import Router, F
from aiogram.types import Message
from bot.services.api import api_client

router = Router()


@router.message(F.text == "Materials")
async def materials_menu(message: Message):
    resp = await api_client.materials(message.from_user.id)
    if not resp.get("success") or not resp.get("data"):
        await message.answer("No materials available.")
        return

    for m in resp["data"]:
        text = f"{m['title']} ({m['type']})"
        if m.get("link_url"):
            text += f"\nLink: {m['link_url']}"
        await message.answer(text)
