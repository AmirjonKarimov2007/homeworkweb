from aiogram import Router, F
from aiogram.types import Message
from bot.services.api import api_client

router = Router()


@router.message(F.text == "My Groups")
async def my_groups(message: Message):
    resp = await api_client.groups(message.from_user.id)
    if not resp.get("success") or not resp.get("data"):
        await message.answer("No groups assigned.")
        return
    for g in resp["data"]:
        await message.answer(f"{g['name']} ({g.get('schedule_time','')})")
