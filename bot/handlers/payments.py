from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pathlib import Path
from bot.services.api import api_client
from bot.states.payments import PaymentStates

router = Router()
TMP_DIR = Path("bot/tmp")
TMP_DIR.mkdir(parents=True, exist_ok=True)


@router.message(F.text == "Payments")
async def payments_menu(message: Message, state: FSMContext):
    resp = await api_client.payments(message.from_user.id)
    if not resp.get("success") or not resp.get("data"):
        await message.answer("No payments found.")
        return

    builder = InlineKeyboardBuilder()
    for item in resp["data"]:
        builder.button(text=f"{item['month']} - {item['status']}", callback_data=f"pay:{item['id']}")
    builder.adjust(1)
    await message.answer("Select a payment to upload receipt:", reply_markup=builder.as_markup())
    await state.set_state(PaymentStates.choosing)


@router.callback_query(F.data.startswith("pay:"))
async def payment_select(callback: CallbackQuery, state: FSMContext):
    payment_id = int(callback.data.split(":")[1])
    await state.update_data(payment_id=payment_id)
    await state.set_state(PaymentStates.uploading)
    await callback.message.answer("Upload receipt as photo or document. You can add a note in caption.")
    await callback.answer()


@router.message(PaymentStates.uploading)
async def payment_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get("payment_id")
    if not payment_id:
        await message.answer("Please select payment again.")
        await state.clear()
        return

    file_path = None
    if message.document:
        file = message.document
        file_path = TMP_DIR / file.file_name
        await message.bot.download(file, destination=file_path)
    elif message.photo:
        photo = message.photo[-1]
        file_path = TMP_DIR / f"receipt_{photo.file_id}.jpg"
        await message.bot.download(photo, destination=file_path)

    if not file_path:
        await message.answer("Please upload a photo or document.")
        return

    note = message.caption
    resp = await api_client.upload_receipt(message.from_user.id, payment_id, None, note, str(file_path))
    if resp.get("success"):
        await message.answer("Receipt uploaded.")
    else:
        await message.answer("Failed to upload receipt.")

    if file_path.exists():
        file_path.unlink(missing_ok=True)
    await state.clear()
