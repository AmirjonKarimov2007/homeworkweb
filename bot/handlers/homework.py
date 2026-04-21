from aiogram import Router, F
from aiogram.filters import CommandStart, CallbackQuery
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.services.database import db_service
from bot.utils.enums import Role

router = Router()


@router.callback_query(F.data.startswith("submit_hw_"))
async def submit_homework_start(callback: CallbackQuery):
    """Start homework submission process"""
    homework_id = int(callback.data.split("_")[2])

    await callback.message.answer(
        "Uy ishingizni matn shaklida yuboring.\n\n"
        "⚠️ E'tibor bering: Fayl, rasm yoki boshqa formatdagi materiallar qabul qilinmaydi."
    )

    # Save current state for text input
    from bot.keyboards.inline import save_homework_state
    await save_homework_state(callback.from_user.id, homework_id)

    await callback.answer()


@router.message(F.text)
async def handle_homework_text(message: Message):
    """Handle homework text submission"""
    # Get current state
    from bot.keyboards.inline import get_homework_state

    state = await get_homework_state(message.from_user.id)
    if not state:
        await message.answer("Iltimos, avval uy ishini tanlang.")
        return

    homework_id = state["homework_id"]
    telegram_id = message.from_user.id

    # Submit homework
    success = await db_service.submit_homework(homework_id, telegram_id, message.text)

    if success:
        await message.answer(
            "✅ Uy ishingiz muvaffaqiyatli topshirildi!\n\n"
            "O'qituvchingiz javobini kutib turing."
        )
    else:
        await message.answer(
            "❌ Uy ishini topshirishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )

    # Clear state
    from bot.keyboards.inline import clear_homework_state
    await clear_homework_state(message.from_user.id)


@router.callback_query(F.data.startswith("view_hw_"))
async def view_homework_details(callback: CallbackQuery):
    """View homework details"""
    homework_id = int(callback.data.split("_")[2])

    # Get homework details
    homework = await db_service.get_homework_by_id(homework_id)
    if not homework:
        await callback.message.answer("Uy ishi topilmadi.")
        await callback.answer()
        return

    # Get user's submissions for this homework
    submissions = await db_service.get_homework_submissions(homework_id)

    # Show homework details
    homework_info = f"""
**Uy Ishi - {homework.title}**

📝 Tavsifi: {homework.description or "Tavsif berilmagan"}

📅 Muddati: {homework.due_date.strftime("%d.%m.%Y %H:%M") if homework.due_date else "Noma'lum"}

📊 Bajarish holati: {homework.status.value}

📤 Yaratilgan vaqti: {homework.created_at.strftime("%d.%m.%Y %H:%M")}
"""

    if submissions:
        homework_info += "\n\n**Topshirgan talabalar:**\n"
        for submission in submissions[:5]:  # Show first 5 submissions
            status_emoji = "✅" if submission["status"] == "completed" else "⏳"
            homework_info += f"\n{status_emoji} {submission['user_name']} - {submission['submitted_at'].strftime('%d.%m.%Y %H:%M')}"

        if len(submissions) > 5:
            homework_info += f"\n\n... va yana {len(submissions) - 5} nafar talaba"

    # Add back button
    if homework.lesson:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data=f"group_{homework.lesson.group.id}"
        ))
        builder.adjust(1)

        await callback.message.edit_text(homework_info, reply_markup=builder.as_markup())
    else:
        await callback.message.answer(homework_info)

    await callback.answer()


@router.callback_query(F.data.startswith("view_hw_submissions_"))
async def view_all_homework_submissions(callback: CallbackQuery):
    """View all submissions for a homework"""
    homework_id = int(callback.data.split("_")[3])

    # Get all submissions
    submissions = await db_service.get_homework_submissions(homework_id)

    if not submissions:
        await callback.message.answer("Ushbu uy uchun hech qanday topshiriq topilmagan.")
        await callback.answer()
        return

    # Create pagination for submissions
    page_size = 10
    total_pages = (len(submissions) + page_size - 1) // page_size
    page = 1

    text = f"""
**Uy Ishi Topshiruvchilar - {len(submissions)} ta**

"""

    # Add submissions for current page
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    for submission in submissions[start_idx:end_idx]:
        status_emoji = "✅" if submission["status"] == "completed" else "⏳"
        text += f"\n{status_emoji} **{submission['user_name']}**\n"
        text += f"   • Topshirilgan: {submission['submitted_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"   • Holat: {submission['status']}\n"
        text += f"   • Text: {submission['text'][:100]}{'...' if len(submission['text']) > 100 else ''}\n"

    # Add navigation buttons
    builder = InlineKeyboardBuilder()

    if page > 1:
        builder.add(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"view_hw_submissions_{homework_id}_page_{page - 1}"
        ))

    if page < total_pages:
        builder.add(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"view_hw_submissions_{homework_id}_page_{page + 1}"
        ))

    builder.add(InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=f"view_hw_{homework_id}"
    ))

    builder.adjust(2)

    await callback.message.edit_text(
        text + f"\n\nSahifa {page}/{total_pages}",
        reply_markup=builder.as_markup()
    )
    await callback.answer()
