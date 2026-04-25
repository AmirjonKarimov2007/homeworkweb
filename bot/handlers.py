"""
Bot handlerslari - telefon orqali login va inline menyu oqimi
"""
from typing import Dict, Optional

from aiogram import exceptions, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from loguru import logger

from database import db
from models import User


class BotHandlers:
    PAGE_SIZE = 10

    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.pending_homework_submissions: Dict[int, int] = {}

    async def register_handlers(self):
        self.dp.register_message_handler(self.handle_start, CommandStart())
        self.dp.register_message_handler(self.handle_contact, content_types=[types.ContentType.CONTACT])
        self.dp.register_message_handler(self.handle_text_message, content_types=[types.ContentType.TEXT])
        self.dp.register_callback_query_handler(self.handle_callback_query)
        logger.info("Barcha handlers ro'yxatdan o'tkazildi")

    async def handle_start(self, message: Message):
        try:
            user = await self.get_user_by_telegram_id(message.from_user.id)
            if user:
                await message.answer(
                    f"Assalomu alaykum, {user.full_name}.\n"
                    f"Sizning profilingiz allaqachon ulangan."
                )
                await self.show_role_menu(message, user)
                return

            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Telefon raqamini yuborish", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await message.answer(
                "Assalomu alaykum.\n\n"
                "Davom etish uchun telefon raqamingizni yuboring.\n"
                "Masalan: +998901234567",
                reply_markup=keyboard,
            )
        except exceptions.TelegramAPIError as e:
            logger.error(f"Telegram API error in handle_start: {e}")

    async def handle_contact(self, message: Message):
        phone = message.contact.phone_number if message.contact else None
        if not phone:
            await message.answer("Telefon raqamini yuborishda xatolik yuz berdi.")
            return
        await self._authenticate_by_phone(message, phone)

    async def handle_text_message(self, message: Message):
        user = await self.get_user_by_telegram_id(message.from_user.id)

        if user and message.from_user.id in self.pending_homework_submissions:
            await self._handle_homework_text_submission(message, user)
            return

        if user:
            await message.answer("Kerakli bo'limni tugmalardan tanlang.")
            await self.show_role_menu(message, user)
            return

        if not message.text:
            await message.answer("Telefon raqamingizni yuboring.")
            return

        if not self.validate_phone(message.text.strip()):
            await message.answer(
                "Telefon raqami noto'g'ri.\n"
                "To'g'ri format: +998901234567"
            )
            return

        await self._authenticate_by_phone(message, message.text.strip())

    async def _authenticate_by_phone(self, message: Message, phone: str):
        try:
            user = await db.check_user_by_phone(phone)
            if not user:
                await message.answer(
                    "Bu telefon raqam bazada topilmadi.\n"
                    "Ro'yxatdan o'tgan raqamingizni yuboring.",
                    reply_markup=types.ReplyKeyboardRemove(),
                )
                return

            success = await db.update_telegram_id(user.id, message.from_user.id)
            if not success:
                await message.answer(
                    "Bog'lashda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.",
                    reply_markup=types.ReplyKeyboardRemove(),
                )
                return

            user.telegram_id = message.from_user.id
            db.cache_user(user)
            await message.answer(
                f"Assalomu alaykum, {user.full_name}.\n"
                f"Rol: {self.get_role_name(user.role)}",
                reply_markup=types.ReplyKeyboardRemove(),
            )
            await self.show_role_menu(message, user)
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            await message.answer(
                "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
                reply_markup=types.ReplyKeyboardRemove(),
            )

    async def _handle_homework_text_submission(self, message: Message, user: User):
        homework_id = self.pending_homework_submissions.get(message.from_user.id)
        if not homework_id:
            await self.show_role_menu(message, user)
            return

        text = (message.text or "").strip()
        if not text:
            await message.answer("Uy ishini matn ko'rinishida yuboring.")
            return

        success = await db.submit_homework(user.id, homework_id, text)
        if success:
            self.pending_homework_submissions.pop(message.from_user.id, None)
            await message.answer("Uy ishingiz yuborildi.")
            await self.show_role_menu(message, user)
        else:
            await message.answer("Uy ishini yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.")

    def validate_phone(self, phone: str) -> bool:
        import re

        normalized = re.sub(r"[^\d]", "", phone)
        return (
            (len(normalized) == 12 and normalized.startswith("998"))
            or (len(normalized) == 13 and normalized.startswith("998"))
            or (len(normalized) == 9 and normalized.startswith("9"))
        )

    def get_role_name(self, role: str) -> str:
        role_names = {
            "SUPER_ADMIN": "Super Admin",
            "ADMIN": "Admin",
            "TEACHER": "O'qituvchi",
            "STUDENT": "Talaba",
        }
        return role_names.get(role, role)

    async def show_role_menu(self, message: Message, user: User):
        buttons = []
        if user.role == "STUDENT":
            buttons.append([InlineKeyboardButton(text="Guruhlarim", callback_data="show_groups")])
            buttons.append([InlineKeyboardButton(text="Uy ishlar", callback_data="show_homework")])
        elif user.role == "TEACHER":
            buttons.append([InlineKeyboardButton(text="Guruhlarim", callback_data="show_groups")])
            buttons.append([InlineKeyboardButton(text="Uy ish yaratish", callback_data="create_homework")])
            buttons.append([InlineKeyboardButton(text="Topshiriqlarni tekshirish", callback_data="check_homework")])
        else:
            buttons.append([InlineKeyboardButton(text="Barcha guruhlar", callback_data="show_groups")])
            buttons.append([InlineKeyboardButton(text="O'qituvchilar", callback_data="show_teachers")])
            buttons.append([InlineKeyboardButton(text="Statistika", callback_data="stats")])

        buttons.append([InlineKeyboardButton(text="Yordam", callback_data="help")])
        buttons.append([InlineKeyboardButton(text="Chiqish", callback_data="logout")])
        await message.answer(
            "Quyidagi bo'limlardan birini tanlang:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def handle_callback_query(self, callback: types.CallbackQuery):
        try:
            data = callback.data or ""
            user = await self.get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.message.edit_text("Foydalanuvchi topilmadi. /start bosing.")
                return

            if data == "show_groups":
                await self.show_groups(callback, user, page=1)
            elif data.startswith("groups_page:"):
                _, page = data.split(":")
                await self.show_groups(callback, user, page=int(page))
            elif data.startswith("group:"):
                _, group_id, page = data.split(":")
                await self.show_group_details(callback, user, int(group_id), int(page))
            elif data.startswith("lesson_page:"):
                _, group_id, page = data.split(":")
                await self.show_group_details(callback, user, int(group_id), int(page))
            elif data.startswith("lesson:"):
                _, lesson_id, group_id, page = data.split(":")
                await self.show_lesson_detail(callback, user, int(lesson_id), int(group_id), int(page))
            elif data.startswith("submit_hw:"):
                _, homework_id, lesson_id, group_id, page = data.split(":")
                await self.start_homework_submission(callback, int(homework_id), int(lesson_id), int(group_id), int(page))
            elif data == "show_homework":
                await self.show_homework(callback, user, page=1)
            elif data.startswith("homework_page:"):
                _, page = data.split(":")
                await self.show_homework(callback, user, page=int(page))
            elif data.startswith("homework_group:"):
                _, group_id, page = data.split(":")
                await self.show_group_homework(callback, int(group_id), int(page))
            elif data == "create_homework":
                await self.create_homework_start(callback, user)
            elif data == "check_homework":
                await self.check_homework(callback, user)
            elif data == "show_teachers":
                await self.show_teachers(callback)
            elif data == "stats":
                await self.show_stats(callback, user)
            elif data == "help":
                await self.show_help(callback)
            elif data == "logout":
                await self.handle_logout(callback, user)
            elif data == "back_to_menu":
                await self.show_role_menu(callback.message, user)
            elif data == "noop":
                await callback.answer()
                return
            else:
                await callback.answer("Noto'g'ri tanlov.", show_alert=True)
                return

            await callback.answer()
        except Exception as e:
            logger.error(f"Error in handle_callback_query: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        try:
            return await db.get_user_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Error getting user by telegram_id: {e}")
            return None

    async def handle_logout(self, callback: types.CallbackQuery, user: User):
        success = await db.update_telegram_id(user.id, None)
        db.remove_user_from_cache(callback.from_user.id)
        self.pending_homework_submissions.pop(callback.from_user.id, None)
        if success:
            await callback.message.edit_text(
                "Xayr.\n\nQayta kirish uchun /start buyrug'ini ishlating."
            )
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_groups(self, callback: types.CallbackQuery, user: User, page: int = 1):
        groups = await db.get_user_groups(user.id, user.role)
        if not groups:
            await callback.message.edit_text(
                "Sizga biriktirilgan guruhlar yo'q.",
                reply_markup=self.back_markup("back_to_menu"),
            )
            return

        total_pages = max(1, (len(groups) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))
        start = (page - 1) * self.PAGE_SIZE
        page_items = groups[start:start + self.PAGE_SIZE]

        buttons = [
            [InlineKeyboardButton(text=group.name, callback_data=f"group:{group.id}:1")]
            for group in page_items
        ]
        buttons.extend(self.build_pagination_row("groups_page", page, total_pages))
        buttons.append([InlineKeyboardButton(text="Orqaga", callback_data="back_to_menu")])

        await callback.message.edit_text(
            f"Guruhlar ({page}/{total_pages})",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def show_group_details(self, callback: types.CallbackQuery, user: User, group_id: int, page: int = 1):
        group = await db.get_group_by_id(group_id)
        if not group:
            await callback.message.edit_text("Guruh topilmadi.", reply_markup=self.back_markup("show_groups"))
            return

        offset = (page - 1) * self.PAGE_SIZE
        lessons = await db.get_lessons_by_group(group_id, offset=offset, limit=self.PAGE_SIZE)
        total = await db.get_lessons_count(group_id)
        total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))

        buttons = [
            [InlineKeyboardButton(text=f"{lesson.title}", callback_data=f"lesson:{lesson.id}:{group_id}:{page}")]
            for lesson in lessons
        ]
        buttons.extend(self.build_pagination_row(f"lesson_page:{group_id}", page, total_pages))
        buttons.append([InlineKeyboardButton(text="Orqaga", callback_data="show_groups")])

        header = f"📚 {group.name}\n"
        if group.schedule_time:
            header += f"🕒 {group.schedule_time}\n"
        header += f"\nDarslar ({page}/{total_pages})"

        await callback.message.edit_text(header, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    async def show_lesson_detail(self, callback: types.CallbackQuery, user: User, lesson_id: int, group_id: int, page: int):
        detail = await db.get_lesson_detail(lesson_id)
        if not detail:
            await callback.message.edit_text("Dars topilmadi.", reply_markup=self.back_markup(f"group:{group_id}:{page}"))
            return

        parts = []
        if detail.homework_due_date:
            parts.append(f"📅 deadline: {detail.homework_due_date.strftime('%d.%m.%Y %H:%M')}")
        parts.append("📖 Dars Detallari")
        parts.append(f"📌 Mavzu: {detail.title}")
        if detail.description:
            parts.append("📝 Tavsif:")
            parts.append(detail.description)
        if detail.homework_title or detail.homework_instructions:
            parts.append("")
            parts.append("Homework:")
            if detail.homework_title:
                parts.append(f"• {detail.homework_title}")
            if detail.homework_instructions:
                parts.append(detail.homework_instructions)

        buttons = []
        if user.role == "STUDENT" and detail.homework_id:
            buttons.append([
                InlineKeyboardButton(
                    text="✍️ Text javob yuborish",
                    callback_data=f"submit_hw:{detail.homework_id}:{lesson_id}:{group_id}:{page}",
                )
            ])
        buttons.append([InlineKeyboardButton(text="Orqaga", callback_data=f"group:{group_id}:{page}")])

        await callback.message.edit_text(
            "\n".join(parts),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def start_homework_submission(
        self, callback: types.CallbackQuery, homework_id: int, lesson_id: int, group_id: int, page: int
    ):
        self.pending_homework_submissions[callback.from_user.id] = homework_id
        await callback.message.edit_text(
            "Uy ishini matn ko'rinishida yuboring.\n\n"
            "Bir dona oddiy text yuborsangiz, tizim uni homework sifatida saqlaydi.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Orqaga", callback_data=f"lesson:{lesson_id}:{group_id}:{page}")]
                ]
            ),
        )

    async def show_homework(self, callback: types.CallbackQuery, user: User, page: int = 1):
        groups = await db.get_user_groups(user.id, user.role)
        if not groups:
            await callback.message.edit_text(
                "Sizning guruhlaringiz yo'q.",
                reply_markup=self.back_markup("back_to_menu"),
            )
            return

        total_pages = max(1, (len(groups) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))
        start = (page - 1) * self.PAGE_SIZE
        page_items = groups[start:start + self.PAGE_SIZE]

        buttons = [
            [InlineKeyboardButton(text=group.name, callback_data=f"homework_group:{group.id}:1")]
            for group in page_items
        ]
        buttons.extend(self.build_pagination_row("homework_page", page, total_pages))
        buttons.append([InlineKeyboardButton(text="Orqaga", callback_data="back_to_menu")])

        await callback.message.edit_text(
            f"Uy ishlar bo'limi ({page}/{total_pages})",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def show_group_homework(self, callback: types.CallbackQuery, group_id: int, page: int = 1):
        offset = (page - 1) * self.PAGE_SIZE
        homework_list = await db.get_homework_by_group(group_id, offset=offset, limit=self.PAGE_SIZE)
        total = await db.get_homework_count(group_id)
        total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))

        if not homework_list:
            await callback.message.edit_text(
                "Bu guruhda hozircha uy ishlar yo'q.",
                reply_markup=self.back_markup("show_homework"),
            )
            return

        text_parts = [f"Uy ishlar ({page}/{total_pages})", ""]
        for hw in homework_list:
            due_date = hw.due_date.strftime("%d.%m.%Y %H:%M") if hw.due_date else "Aniqlanmagan"
            text_parts.append(f"• {hw.title}")
            text_parts.append(f"  📚 {hw.lesson_title}")
            text_parts.append(f"  📅 {due_date}")
            if hw.description:
                text_parts.append(f"  📝 {hw.description}")
            text_parts.append("")

        buttons = []
        buttons.extend(self.build_pagination_row(f"homework_group:{group_id}", page, total_pages))
        buttons.append([InlineKeyboardButton(text="Orqaga", callback_data="show_homework")])

        await callback.message.edit_text(
            "\n".join(text_parts).strip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def create_homework_start(self, callback: types.CallbackQuery, user: User):
        if user.role not in ["TEACHER", "ADMIN", "SUPER_ADMIN"]:
            await callback.message.edit_text("Sizda ruxsat yo'q.")
            return
        await callback.message.edit_text(
            "Uy ishi yaratish hozircha bot ichida to'liq ulanmagan.\n"
            "Bu qismni keyingi bosqichda to'liq qo'shamiz.",
            reply_markup=self.back_markup("back_to_menu"),
        )

    async def check_homework(self, callback: types.CallbackQuery, user: User):
        if user.role not in ["TEACHER", "ADMIN", "SUPER_ADMIN"]:
            await callback.message.edit_text("Sizda ruxsat yo'q.")
            return
        await callback.message.edit_text(
            "Uy ishlarini tekshirish oqimi hali botda to'liq ulanmagan.",
            reply_markup=self.back_markup("back_to_menu"),
        )

    async def show_teachers(self, callback: types.CallbackQuery):
        teachers = await db.get_teachers()
        if not teachers:
            await callback.message.edit_text("Hech qanday o'qituvchi yo'q.", reply_markup=self.back_markup("back_to_menu"))
            return

        text = "O'qituvchilar ro'yxati:\n\n"
        for idx, teacher in enumerate(teachers, start=1):
            text += f"{idx}. {teacher.full_name}\n   📞 {teacher.phone}\n\n"
        await callback.message.edit_text(text.strip(), reply_markup=self.back_markup("back_to_menu"))

    async def show_stats(self, callback: types.CallbackQuery, user: User):
        await callback.message.edit_text(
            "Statistika bo'limi keyingi bosqichda to'liq ulanadi.",
            reply_markup=self.back_markup("back_to_menu"),
        )

    async def show_help(self, callback: types.CallbackQuery):
        help_text = (
            "Bot yordami\n\n"
            "• Guruhlarim orqali guruh va darslarni ko'rasiz\n"
            "• Dars ichida homework bo'lsa text ko'rinishida yuborasiz\n"
            "• Istalgan matn yuborsangiz menyu qayta chiqadi\n"
            "• /start bosilganda akkaunt ulangan bo'lsa telefon qayta so'ralmaydi"
        )
        await callback.message.edit_text(help_text, reply_markup=self.back_markup("back_to_menu"))

    def build_pagination_row(self, prefix: str, page: int, total_pages: int):
        if total_pages <= 1:
            return []

        row = []
        if page > 1:
            row.append(InlineKeyboardButton(text="<<", callback_data=f"{prefix}:{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            row.append(InlineKeyboardButton(text=">>", callback_data=f"{prefix}:{page + 1}"))
        return [row]

    def back_markup(self, callback_data: str):
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Orqaga", callback_data=callback_data)]]
        )
