"""
Telegram bot handlers
"""

from datetime import datetime
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
    FINAL_SUBMISSION_STATUSES = {"ACCEPTED", "REVISION_REQUESTED", "REVIEWED"}

    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp
        self.pending_homework_submissions: Dict[int, dict] = {}
        self.pending_actions: Dict[int, dict] = {}

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
                    f"Salom, {user.full_name}.\n"
                    f"Profilingiz allaqachon ulangan."
                )
                await self.show_role_menu(message, user)
                return

            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Telefon raqamini yuborish", request_contact=True)]],
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

        if user and message.from_user.id in self.pending_actions:
            await self._handle_pending_action(message, user)
            return

        if user:
            await message.answer("👇 Kerakli bo'limni tanlang")
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
                f"✅ Assalomu alaykum, {user.full_name}\n"
                f"👤 Rol: {self.get_role_name(user.role)}",
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
        state = self.pending_homework_submissions.get(message.from_user.id)
        if not state:
            await self.show_role_menu(message, user)
            return

        text = (message.text or "").strip()
        if not text:
            await message.answer("Uy ishini matn ko'rinishida yuboring.")
            return

        result = await db.submit_homework(user.id, state["homework_id"], text)
        self.pending_homework_submissions.pop(message.from_user.id, None)

        if result == "OK":
            await message.answer(
                "✅ Uy ishingiz yuborildi.\n"
                "STATUS: jarayonda"
            )
            await self.show_role_menu(message, user)
        elif result == "LOCKED":
            await message.answer(
                "❌ Bu homework allaqachon tekshirilgan. Endi uni o'zgartirib bo'lmaydi."
            )
            await self.show_role_menu(message, user)
        else:
            await message.answer("Uy ishini yuborib bo'lmadi. Keyinroq qayta urinib ko'ring.")

    async def _handle_pending_action(self, message: Message, user: User):
        state = self.pending_actions.get(message.from_user.id)
        if not state:
            await self.show_role_menu(message, user)
            return

        text = (message.text or "").strip()
        if not text:
            await message.answer("Matn yuboring.")
            return

        action_type = state["type"]
        if action_type == "create_lesson":
            await self._handle_create_lesson_flow(message, user, state, text)
        elif action_type in {"create_homework", "edit_homework"}:
            await self._handle_homework_flow(message, user, state, text)
        else:
            self.pending_actions.pop(message.from_user.id, None)
            await self.show_role_menu(message, user)

    async def _handle_create_lesson_flow(self, message: Message, user: User, state: dict, text: str):
        if state["step"] == "title":
            state["title"] = text
            state["step"] = "date"
            await message.answer("📅 Dars sanasini yuboring.\nFormat: `2026-04-25`", parse_mode="Markdown")
            return

        if state["step"] == "date":
            try:
                state["date"] = datetime.strptime(text, "%Y-%m-%d").date()
            except ValueError:
                await message.answer("Sana formati noto'g'ri. To'g'ri format: 2026-04-25")
                return
            state["step"] = "description"
            await message.answer("📝 Dars tavsifini yuboring.\nAgar kerak bo'lmasa `-` yuboring.", parse_mode="Markdown")
            return

        description = None if text == "-" else text
        lesson_id = await db.create_lesson(
            group_id=state["group_id"],
            title=state["title"],
            description=description,
            teacher_id=user.id,
            lesson_date=state["date"],
        )
        self.pending_actions.pop(message.from_user.id, None)
        if lesson_id:
            await message.answer("✅ Yangi dars yaratildi.")
        else:
            await message.answer("❌ Dars yaratib bo'lmadi.")
        await self.show_role_menu(message, user)

    async def _handle_homework_flow(self, message: Message, user: User, state: dict, text: str):
        if state["step"] == "title":
            state["title"] = text
            state["step"] = "instructions"
            await message.answer("📝 Homework matnini yuboring.")
            return

        if state["step"] == "instructions":
            state["instructions"] = text
            state["step"] = "due_date"
            await message.answer(
                "📅 Deadline yuboring.\nFormat: `25.04.2026 23:59`\nYoki deadlinesiz bo'lsa `-` yuboring.",
                parse_mode="Markdown",
            )
            return

        due_date = None
        if text != "-":
            try:
                due_date = datetime.strptime(text, "%d.%m.%Y %H:%M")
            except ValueError:
                await message.answer("Deadline formati noto'g'ri. Masalan: 25.04.2026 23:59")
                return

        self.pending_actions.pop(message.from_user.id, None)
        if state["type"] == "create_homework":
            homework_id = await db.create_homework(
                lesson_id=state["lesson_id"],
                title=state["title"],
                instructions=state["instructions"],
                teacher_id=user.id,
                due_date=due_date,
            )
            if homework_id:
                await message.answer("✅ Homework yaratildi.")
                await self._notify_group_students_about_homework(
                    group_id=state["group_id"],
                    title=state["title"],
                    due_date=due_date,
                )
            else:
                await message.answer("❌ Homework yaratib bo'lmadi.")
        else:
            success = await db.update_homework(
                homework_id=state["homework_id"],
                title=state["title"],
                instructions=state["instructions"],
                due_date=due_date,
            )
            await message.answer("✅ Homework yangilandi." if success else "❌ Homework yangilanmadi.")

        await self.show_role_menu(message, user)

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
        if user.role in {"STUDENT", "TEACHER"}:
            buttons.append([InlineKeyboardButton(text="📚 Guruhlarim", callback_data="show_groups")])
        else:
            buttons.append([InlineKeyboardButton(text="📚 Barcha guruhlar", callback_data="show_groups")])
            buttons.append([InlineKeyboardButton(text="👨‍🏫 O'qituvchilar", callback_data="show_teachers")])
            buttons.append([InlineKeyboardButton(text="📊 Statistika", callback_data="stats")])

        await message.answer(
            "Kerakli bo'limni tanlang:",
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
            elif data.startswith("stat:"):
                _, lesson_id, group_id, page = data.split(":")
                await self.show_lesson_stats(callback, int(lesson_id), int(group_id), int(page))
            elif data.startswith("students:"):
                _, lesson_id, group_id, page = data.split(":")
                await self.show_lesson_students(callback, user, int(lesson_id), int(group_id), int(page))
            elif data.startswith("student:"):
                _, lesson_id, group_id, student_id, page = data.split(":")
                await self.show_student_submission(callback, user, int(lesson_id), int(group_id), int(student_id), int(page))
            elif data.startswith("review:"):
                _, submission_id, action, lesson_id, group_id, student_id, page = data.split(":")
                await self.review_submission(
                    callback,
                    user,
                    int(submission_id),
                    action,
                    int(lesson_id),
                    int(group_id),
                    int(student_id),
                    int(page),
                )
            elif data.startswith("newlesson:"):
                _, group_id = data.split(":")
                await self.start_create_lesson(callback, int(group_id))
            elif data.startswith("newhw:"):
                _, lesson_id = data.split(":")
                await self.start_create_homework(callback, int(lesson_id))
            elif data.startswith("edithw:"):
                _, lesson_id, homework_id = data.split(":")
                await self.start_edit_homework(callback, int(lesson_id), int(homework_id))
            elif data == "show_teachers":
                await self.show_teachers(callback)
            elif data == "stats":
                await self.show_stats(callback, user)
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

    async def show_groups(self, callback: types.CallbackQuery, user: User, page: int = 1):
        groups = await db.get_user_groups(user.id, user.role)
        if not groups:
            await callback.message.edit_text("Sizga biriktirilgan guruhlar yo'q.")
            return

        total_pages = max(1, (len(groups) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))
        start = (page - 1) * self.PAGE_SIZE
        page_items = groups[start:start + self.PAGE_SIZE]

        buttons = [[InlineKeyboardButton(text=f"📘 {group.name}", callback_data=f"group:{group.id}:1")] for group in page_items]
        buttons.extend(self.build_pagination_row("groups_page", page, total_pages))

        await callback.message.edit_text(
            f"📚 Guruhlar ({page}/{total_pages})",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def show_group_details(self, callback: types.CallbackQuery, user: User, group_id: int, page: int = 1):
        group = await db.get_group_by_id(group_id)
        if not group:
            await callback.message.edit_text("Guruh topilmadi.")
            return

        offset = (page - 1) * self.PAGE_SIZE
        lessons = await db.get_lessons_by_group(group_id, offset=offset, limit=self.PAGE_SIZE)
        total = await db.get_lessons_count(group_id)
        total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))

        buttons = [[InlineKeyboardButton(text=f"📗 {lesson.title}", callback_data=f"lesson:{lesson.id}:{group_id}:{page}")] for lesson in lessons]
        if user.role in {"TEACHER", "ADMIN", "SUPER_ADMIN"}:
            buttons.append([InlineKeyboardButton(text="➕ Yangi dars yaratish", callback_data=f"newlesson:{group_id}")])
        buttons.extend(self.build_pagination_row(f"lesson_page:{group_id}", page, total_pages))
        buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="show_groups")])

        header = f"📚 {group.name}"
        if group.schedule_time:
            header += f"\n🕒 {group.schedule_time}"
        header += f"\n\nDarslar ({page}/{total_pages})"

        await callback.message.edit_text(header, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    async def show_lesson_detail(self, callback: types.CallbackQuery, user: User, lesson_id: int, group_id: int, page: int):
        detail = await db.get_lesson_detail(lesson_id)
        if not detail:
            await callback.message.edit_text("Dars topilmadi.")
            return

        parts = []
        if detail.homework_due_date:
            parts.append(f"📅 deadline: {detail.homework_due_date.strftime('%d.%m.%Y %H:%M')}")
        parts.append("📖 Dars Detallari")
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
            status = await db.get_student_submission_status(user.id, detail.homework_id)
            if status:
                parts.append("")
                parts.append(f"STATUS: {self.format_submission_status(status)}")
            if status in self.FINAL_SUBMISSION_STATUSES:
                parts.append("🔒 Tekshiruv yakunlangan. Qayta yuborish yopilgan.")
            else:
                buttons.append([
                    InlineKeyboardButton(
                        text="✍️ Text yuborish",
                        callback_data=f"submit_hw:{detail.homework_id}:{lesson_id}:{group_id}:{page}",
                    )
                ])

        if user.role in {"TEACHER", "ADMIN", "SUPER_ADMIN"}:
            buttons.append([InlineKeyboardButton(text="📊 Statistika", callback_data=f"stat:{lesson_id}:{group_id}:{page}")])
            buttons.append([InlineKeyboardButton(text="👥 O'quvchilar", callback_data=f"students:{lesson_id}:{group_id}:1")])
            if detail.homework_id:
                buttons.append([InlineKeyboardButton(text="✏️ Homeworkni tahrirlash", callback_data=f"edithw:{lesson_id}:{detail.homework_id}")])
            else:
                buttons.append([InlineKeyboardButton(text="➕ Homework qo'shish", callback_data=f"newhw:{lesson_id}")])

        buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"group:{group_id}:{page}")])
        await callback.message.edit_text(
            "\n".join(parts),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def start_homework_submission(self, callback: types.CallbackQuery, homework_id: int, lesson_id: int, group_id: int, page: int):
        user = await self.get_user_by_telegram_id(callback.from_user.id)
        if user:
            status = await db.get_student_submission_status(user.id, homework_id)
            if status in self.FINAL_SUBMISSION_STATUSES:
                await callback.answer("Bu homework tekshirilgan, qayta yuborib bo'lmaydi.", show_alert=True)
                return

        self.pending_homework_submissions[callback.from_user.id] = {
            "homework_id": homework_id,
            "lesson_id": lesson_id,
            "group_id": group_id,
            "page": page,
        }
        await callback.message.edit_text(
            "📝 Uy ishini matn ko'rinishida yuboring.\n\n"
            "Bir dona text yuborsangiz yetarli.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"lesson:{lesson_id}:{group_id}:{page}")]]
            ),
        )

    async def show_lesson_stats(self, callback: types.CallbackQuery, lesson_id: int, group_id: int, page: int):
        stats = await db.get_lesson_stats(lesson_id)
        if not stats:
            await callback.message.edit_text("Statistika topilmadi.", reply_markup=self.back_markup(f"lesson:{lesson_id}:{group_id}:{page}"))
            return

        text = [
            "📊 Dars statistikasi",
            f"✅ Bajarganlar: {stats['submitted_count']}",
            f"❌ Bajarmaganlar: {stats['not_submitted_count']}",
            "",
            "✅ Bajarganlar:",
            ", ".join(stats["submitted_names"]) if stats["submitted_names"] else "Hech kim yo'q",
            "",
            "❌ Bajarmaganlar:",
            ", ".join(stats["not_submitted_names"]) if stats["not_submitted_names"] else "Hech kim yo'q",
        ]
        await callback.message.edit_text("\n".join(text), reply_markup=self.back_markup(f"lesson:{lesson_id}:{group_id}:{page}"))

    async def show_lesson_students(self, callback: types.CallbackQuery, user: User, lesson_id: int, group_id: int, page: int = 1):
        offset = (page - 1) * self.PAGE_SIZE
        students = await db.get_students_by_group(group_id, offset=offset, limit=self.PAGE_SIZE)
        total = await db.get_students_count(group_id)
        total_pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        page = max(1, min(page, total_pages))

        buttons = [[InlineKeyboardButton(text=f"👤 {student.full_name}", callback_data=f"student:{lesson_id}:{group_id}:{student.id}:{page}")] for student in students]
        buttons.extend(self.build_pagination_row(f"students:{lesson_id}:{group_id}", page, total_pages))
        buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"lesson:{lesson_id}:{group_id}:1")])

        await callback.message.edit_text(
            f"👥 O'quvchilar ({page}/{total_pages})",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def show_student_submission(self, callback: types.CallbackQuery, user: User, lesson_id: int, group_id: int, student_id: int, page: int):
        result = await db.get_student_submission_for_lesson(student_id, lesson_id)
        if not result:
            await callback.message.edit_text("Ma'lumot topilmadi.", reply_markup=self.back_markup(f"students:{lesson_id}:{group_id}:{page}"))
            return

        text = []
        text.append(f"🧑‍🎓 Student ID: {student_id}")
        if result.get("homework_title"):
            text.append(f"📚 Homework: {result['homework_title']}")
        if result.get("due_date"):
            text.append(f"📅 deadline: {result['due_date'].strftime('%d.%m.%Y %H:%M')}")
        text.append("")

        if result.get("submission_id"):
            text.append(f"STATUS: {self.format_submission_status(result['status'])}")
            text.append("")
            text.append("📝 Yuborilgan javob:")
            text.append(result.get("text") or "(bo'sh)")
        else:
            text.append("❌ Bu o'quvchi hali homework yubormagan.")

        buttons = []
        if result.get("submission_id"):
            buttons.append([
                InlineKeyboardButton(
                    text="✅ Tekshirildi",
                    callback_data=f"review:{result['submission_id']}:accept:{lesson_id}:{group_id}:{student_id}:{page}",
                ),
                InlineKeyboardButton(
                    text="↩️ Bekor qilish",
                    callback_data=f"review:{result['submission_id']}:rev:{lesson_id}:{group_id}:{student_id}:{page}",
                ),
            ])
        buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"students:{lesson_id}:{group_id}:{page}")])

        await callback.message.edit_text(
            "\n".join(text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    async def review_submission(
        self,
        callback: types.CallbackQuery,
        user: User,
        submission_id: int,
        action: str,
        lesson_id: int,
        group_id: int,
        student_id: int,
        page: int,
    ):
        status = "ACCEPTED" if action == "accept" else "REVISION_REQUESTED"
        success = await db.update_submission_status(submission_id, user.id, status)
        if success:
            await callback.answer("Holat yangilandi")
        await self.show_student_submission(callback, user, lesson_id, group_id, student_id, page)

    async def start_create_lesson(self, callback: types.CallbackQuery, group_id: int):
        self.pending_actions[callback.from_user.id] = {
            "type": "create_lesson",
            "group_id": group_id,
            "step": "title",
        }
        await callback.message.edit_text(
            "➕ Yangi dars yaratish\n\n"
            "1-qadam: dars nomini yuboring.",
            reply_markup=self.back_markup(f"group:{group_id}:1"),
        )

    async def start_create_homework(self, callback: types.CallbackQuery, lesson_id: int):
        group_id = await db.get_lesson_group_id(lesson_id)
        if not group_id:
            await callback.message.edit_text("Dars topilmadi.")
            return

        self.pending_actions[callback.from_user.id] = {
            "type": "create_homework",
            "lesson_id": lesson_id,
            "group_id": group_id,
            "step": "title",
        }
        await callback.message.edit_text(
            "➕ Yangi homework\n\n"
            "1-qadam: homework sarlavhasini yuboring.",
        )

    async def _notify_group_students_about_homework(self, group_id: Optional[int], title: str, due_date: Optional[datetime]):
        if not group_id:
            return

        telegram_ids = await db.get_group_student_telegram_ids(group_id)
        if not telegram_ids:
            return

        deadline_text = due_date.strftime("%d.%m.%Y %H:%M") if due_date else "-"
        text = (
            "📚 Sizda yangi homework bor.\n\n"
            f"📝 {title}\n"
            f"⏰ Deadline: {deadline_text}"
        )
        for telegram_id in telegram_ids:
            try:
                await self.bot.send_message(chat_id=telegram_id, text=text)
            except Exception as e:
                logger.warning(f"Homework xabari yuborilmadi ({telegram_id}): {e}")

    async def start_edit_homework(self, callback: types.CallbackQuery, lesson_id: int, homework_id: int):
        self.pending_actions[callback.from_user.id] = {
            "type": "edit_homework",
            "lesson_id": lesson_id,
            "homework_id": homework_id,
            "step": "title",
        }
        await callback.message.edit_text(
            "✏️ Homeworkni tahrirlash\n\n"
            "1-qadam: yangi sarlavhani yuboring.",
        )

    async def show_teachers(self, callback: types.CallbackQuery):
        teachers = await db.get_teachers()
        if not teachers:
            await callback.message.edit_text("Hech qanday o'qituvchi yo'q.")
            return

        text = ["👨‍🏫 O'qituvchilar ro'yxati", ""]
        for idx, teacher in enumerate(teachers, start=1):
            text.append(f"{idx}. {teacher.full_name}")
            text.append(f"   📞 {teacher.phone}")
            text.append("")
        await callback.message.edit_text("\n".join(text).strip(), reply_markup=self.back_markup("show_groups"))

    async def show_stats(self, callback: types.CallbackQuery, user: User):
        await callback.message.edit_text(
            "📊 Umumiy statistika bo'limi keyingi bosqichda kengaytiriladi.",
            reply_markup=self.back_markup("show_groups"),
        )

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
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data=callback_data)]]
        )

    def format_submission_status(self, status: Optional[str]) -> str:
        mapping = {
            "SUBMITTED": "jarayonda",
            "REVIEWED": "tekshirildi",
            "ACCEPTED": "qabul qilindi",
            "REVISION_REQUESTED": "bekor qilindi",
            "LATE": "kechikkan",
            "NOT_SUBMITTED": "topshirilmagan",
        }
        return mapping.get(status or "", status or "noma'lum")
