"""
Bot handlerslari - soddalashtirilgan versiya
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from aiogram import types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from database import db

class BotHandlers:
    def __init__(self, bot, dp):
        self.bot = bot
        self.dp = dp

    async def register_handlers(self):
        """Barcha handlerslarni ro'yxatdan o'tkazish"""
        # Start command
        self.dp.message.register(self.handle_start, CommandStart())

        # Text message handlers
        self.dp.message.register(self.handle_phone_input, self.handle_text_filter)
        self.dp.callback_query.register(self.handle_callback_query)

    def handle_text_filter(self, message: Message):
        """Text message filter"""
        return message.text and not message.text.startswith('/')

    async def handle_start(self, message: Message):
        """/start komandasi"""
        try:
            logger.info(f"User {message.from_user.id} started bot")

            await message.answer(
                "Assalomu alaykum! Iltimos, telefon raqamingizni kiriting:\n\n"
                "Misol: +998901234567\n"
                "Yoki: 998901234567",
                reply_markup=types.ReplyKeyboardRemove()
            )
        except TelegramAPIError as e:
            logger.error(f"Telegram API error in handle_start: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in handle_start: {e}")

    async def handle_phone_input(self, message: Message):
        """Telefon raqami bilan ishlash"""
        try:
            phone = message.text.strip()
            logger.info(f"Phone input from {message.from_user.id}: {phone}")

            # Telefon raqamini tekshirish
            if not await self.validate_phone(phone):
                await message.answer(
                    "Iltimos, telefon raqamini to'g'ri formatda kiriting:\n\n"
                    "Misol: +998901234567\n"
                    "Yoki: 998901234567",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                return

            # Foydalanuvchini bazada tekshirish
            user = await db.check_user_by_phone(phone)

            if not user:
                await message.answer(
                    "Bu telefon raqam bazada topilmadi. Iltimos, ro'yxatdan o'tgan telefon raqamingizni kiriting.",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                return

            # Telegram ID ni yangilash
            success = await db.update_telegram_id(user.id, message.from_user.id)
            if not success:
                await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring.")
                return

            # Foydalanuvchi ma'lumotlari
            welcome_text = f"Assalomu alaykum, {user.full_name}! Sizning ro'lingiz: {user.role}"

            if user.role == 'STUDENT':
                await message.answer(welcome_text)
                await self.show_student_menu(message, user)
            elif user.role in ['TEACHER', 'ADMIN', 'SUPER_ADMIN']:
                await message.answer(welcome_text)
                await self.show_teacher_menu(message, user)

        except Exception as e:
            logger.error(f"Error in handle_phone_input: {e}")
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

    async def validate_phone(self, phone: str) -> bool:
        """Telefon raqamini tekshirish"""
        try:
            import re
            # Normalize phone
            normalized = re.sub(r'[^\d]', '', phone)

            # Check format: 998XXXXXXXX or 9XXXXXXXX
            if len(normalized) == 12 and normalized.startswith('998'):
                return True
            elif len(normalized) == 9 and normalized.startswith('9'):
                return True

            return False
        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            return False

    async def show_student_menu(self, message: Message, user):
        """Talaba menyusi ko'rsatish"""
        try:
            groups = await db.get_user_groups(user.id, user.role)

            if not groups:
                await message.answer("Siz hech qandah guruhga a'zo emassiz.")
                return

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="📊 Guruhlarim", callback_data="show_groups"))
            builder.row(InlineKeyboardButton(text="📚 Uy ishlar", callback_data="show_homework"))
            builder.row(InlineKeyboardButton(text="❓ Yordam", callback_data="help"))

            await message.answer("Menyuni tanlang:", reply_markup=builder.as_markup())
        except Exception as e:
            logger.error(f"Error in show_student_menu: {e}")
            await message.answer("Xatolik yuz berdi.")

    async def show_teacher_menu(self, message: Message, user):
        """O'qituvchi menyusi ko'rsatish"""
        try:
            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="👥 Guruhlarim", callback_data="show_groups"))
            builder.row(InlineKeyboardButton(text="➕ Uy ish yaratish", callback_data="create_homework"))
            builder.row(InlineKeyboardButton(text="📝 Tekshirish", callback_data="check_homework"))
            builder.row(InlineKeyboardButton(text="👨‍🏫 O'qituvchilar", callback_data="show_teachers"))
            builder.row(InlineKeyboardButton(text="📊 Statistika", callback_data="stats"))

            await message.answer("Menyuni tanlang:", reply_markup=builder.as_markup())
        except Exception as e:
            logger.error(f"Error in show_teacher_menu: {e}")
            await message.answer("Xatolik yuz berdi.")

    async def handle_callback_query(self, callback: types.CallbackQuery):
        """Callback query bilan ishlash"""
        try:
            data = callback.data

            # Foydalanuvchini tekshirish
            user = await self.get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.message.edit_text("Foydalanuvchi topilmadi.")
                return

            if data == "show_groups":
                await self.show_groups(callback, user)
            elif data == "show_homework":
                await self.show_homework(callback, user)
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
            elif data.startswith("group_"):
                await self.show_group_details(callback, int(data.split("_")[1]))
            elif data.startswith("homework_group_"):
                await self.show_group_homework(callback, int(data.split("_")[2]))
            else:
                await callback.answer("Noto'g'ri tanlov.", show_alert=True)

        except Exception as e:
            logger.error(f"Error in handle_callback_query: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def get_user_by_telegram_id(self, telegram_id: int):
        """Telegram ID orqali foydalanuvchini olish"""
        try:
            return await db.get_user_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Error getting user by telegram_id: {e}")
            return None

    async def show_groups(self, callback: types.CallbackQuery, user):
        """Foydalanuvchining guruhlarini ko'rsatish"""
        try:
            groups = await db.get_user_groups(user.id, user.role)

            if not groups:
                await callback.message.edit_text("Sizning guruhlaringiz yo'q.")
                return

            text = "Sizning guruhlaringiz:\n\n"
            builder = InlineKeyboardBuilder()

            for group in groups:
                text += f"📌 {group.name}\n"
                builder.row(InlineKeyboardButton(
                    text=group.name,
                    callback_data=f"group_{group.id}"
                ))

            builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu"))

            await callback.message.edit_text(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error in show_groups: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_homework(self, callback: types.CallbackQuery, user):
        """Talabaga uy ishlarini ko'rsatish"""
        try:
            groups = await db.get_user_groups(user.id, user.role)

            if not groups:
                await callback.message.edit_text("Sizning guruhlaringiz yo'q.")
                return

            text = "Uy ishlar:\n\n"
            builder = InlineKeyboardBuilder()

            for group in groups:
                builder.row(InlineKeyboardButton(
                    text=f"📚 {group.name}",
                    callback_data=f"homework_group_{group.id}"
                ))

            await callback.message.edit_text(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error in show_homework: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_group_homework(self, callback: types.CallbackQuery, group_id: int):
        """Guruh uy ishlarini ko'rsatish"""
        try:
            homework_list = await db.get_homework_by_group(group_id)

            if not homework_list:
                await callback.message.edit_text("Hozircha uy ishlar yo'q.")
                return

            text = f"Uy ishlar:\n\n"
            for hw in homework_list:
                due_date = hw.due_date.strftime('%d.%m.%Y %H:%M') if hw.due_date else "Aniqlanmagan"
                text += f"📚 {hw.title}\n"
                text += f"   Tavsif: {hw.description}\n"
                text += f"   Muddat: {due_date}\n"
                text += f"   Dars: {hw.lesson_title}\n\n"

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_homework"))

            await callback.message.edit_text(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error in show_group_homework: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def create_homework_start(self, callback: types.CallbackQuery, user):
        """Uy ishi yaratishni boshlash"""
        try:
            if user.role not in ['TEACHER', 'ADMIN', 'SUPER_ADMIN']:
                await callback.message.edit_text("Sizda ruxsat yo'q.")
                return

            await callback.message.edit_text(
                "Uy ishi yaratish uchun iltimos, quyidagi ma'lumotlarni kiriting:\n\n"
                "1. Guruh nomi yoki IDsi\n"
                "2. Uy ishi sarlavhasi\n"
                "3. Tavsifi\n"
                "4. Muddati (YYYY-MM-DD HH:MM formatida)\n\n"
                "Har bir qator alohida xabar yuboring."
            )

            await callback.answer("Uy ishi yaratishni boshlang.")
        except Exception as e:
            logger.error(f"Error in create_homework_start: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def check_homework(self, callback: types.CallbackQuery, user):
        """Uy ishlarni tekshirish"""
        try:
            if user.role not in ['TEACHER', 'ADMIN', 'SUPER_ADMIN']:
                await callback.message.edit_text("Sizda ruxsat yo'q.")
                return

            await callback.message.edit_text(
                "Uy ishlarni tekshirish funksiyasi hali tayyorlanmagan.\n\n"
                "Tez orada qo'shiladi!"
            )

        except Exception as e:
            logger.error(f"Error in check_homework: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_teachers(self, callback: types.CallbackQuery):
        """O'qituvchilar ro'yxatini ko'rsatish"""
        try:
            teachers = await db.get_teachers()

            if not teachers:
                await callback.message.edit_text("Hech qanday o'qituvchi yo'q.")
                return

            text = "O'qituvchilar ro'yxati:\n\n"
            for teacher in teachers:
                text += f"👨‍🏫 {teacher.full_name}\n"
                text += f"   Telefon: {teacher.phone}\n\n"

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu"))

            await callback.message.edit_text(text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error in show_teachers: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_stats(self, callback: types.CallbackQuery, user):
        """Statistika ko'rsatish"""
        try:
            if user.role not in ['ADMIN', 'SUPER_ADMIN']:
                await callback.message.edit_text("Sizda ruxsat yo'q.")
                return

            await callback.message.edit_text(
                "Statistika funksiyasi hali tayyorlanmagan.\n\n"
                "Tez orada qo'shiladi!"
            )

        except Exception as e:
            logger.error(f"Error in show_stats: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_help(self, callback: types.CallbackQuery):
        """Yordam xabari"""
        try:
            help_text = """📚 Bot yordimi

Asosiy funksiyalar:
• Guruhlaringizni ko'ring
• Uy ishlaringizni tekshiring
• Yangi uy ishi yarating (o'qituvchilar uchun)
• Topshiriqlaringizni yuboring (talabalar uchun)

Agar qo'shimcha yordam kerak bo'lsa, admin bilan bog'laning."""

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu"))

            await callback.message.edit_text(help_text, reply_markup=builder.as_markup())

        except Exception as e:
            logger.error(f"Error in show_help: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_group_details(self, callback: types.CallbackQuery, group_id: int):
        """Guruh detallarini ko'rsatish"""
        try:
            await callback.message.edit_text(
                "Guruh detallari hali tayyorlanmagan.\n\n"
                "Tez orada qo'shiladi!"
            )

        except Exception as e:
            logger.error(f"Error in show_group_details: {e}")
            await callback.answer("Xatolik yuz berdi.", show_alert=True)