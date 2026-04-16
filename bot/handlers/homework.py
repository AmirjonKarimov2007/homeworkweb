from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pathlib import Path
from bot.services.api import api_client
from bot.states.homework import HomeworkStates

router = Router()
TMP_DIR = Path("bot/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)


@router.message(F.text == "Homework")
async def homework_menu(message: Message, state: FSMContext):
    resp = await api_client.homework_list(message.from_user.id)
    if not resp.get("success") or not resp.get("data"):
        await message.answer("No homework found.")
        return

    builder = InlineKeyboardBuilder()
    for item in resp["data"]:
        builder.button(text=item["title"], callback_data=f"hw:{item['id']}")
    builder.adjust(1)
    await message.answer("Select homework:", reply_markup=builder.as_markup())
    await state.set_state(HomeworkStates.choosing)


@router.callback_query(F.data.startswith("hw:"))
async def homework_select(callback: CallbackQuery, state: FSMContext):
    homework_id = int(callback.data.split(":")[1])
    await state.update_data(homework_id=homework_id)
    await state.set_state(HomeworkStates.submitting)
    await callback.message.answer("Send your homework text and/or file in one message.")
    await callback.answer()


@router.message(HomeworkStates.submitting)
async def homework_submit(message: Message, state: FSMContext):
    data = await state.get_data()
    homework_id = data.get("homework_id")
    if not homework_id:
        await message.answer("Please select homework again.")
        await state.clear()
        return

    text = message.text
    file_path = None

    if message.document:
        file = message.document
        file_path = TMP_DIR / file.file_name
        await message.bot.download(file, destination=file_path)
    elif message.photo:
        photo = message.photo[-1]
        file_path = TMP_DIR / f"photo_{photo.file_id}.jpg"
        await message.bot.download(photo, destination=file_path)

    resp = await api_client.submit_homework(homework_id, message.from_user.id, text, str(file_path) if file_path else None)
    if resp.get("success"):
        await message.answer("Homework submitted successfully.")
    else:
        await message.answer("Failed to submit homework.")

    if file_path and file_path.exists():
        file_path.unlink(missing_ok=True)

    await state.clear()
