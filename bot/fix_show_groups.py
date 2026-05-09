import re

with open('handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken show_group_details function
old_code = '''    async def show_group_details(self, callback: types.CallbackQuery, user: User, group_id: int, page: int = 1):
        """Guruh detallarini ko'rsatish"""
        try:

    async def show_lesson_detail'''

new_code = '''    async def show_group_details(self, callback: types.CallbackQuery, user: User, group_id: int, page: int = 1):
        """Guruh detallarini ko'rsatish"""
        try:
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

            # Guruh sarlavhasi - Super Admin uchun maxsus ko'rsatkich
            header = f"📚 {group.name}"
            if user.role == "SUPER_ADMIN":
                header = f"👑 *{group.name}*"
            if group.schedule_time:
                header += f"\n🕒 {group.schedule_time}"
            header += f"\n\nDarslar ({page}/{total_pages})"

            await callback.message.edit_text(
                header,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="Markdown" if user.role == "SUPER_ADMIN" else None,
            )
        except Exception as e:
            logger.error(f"Error in show_group_details: {e}", exc_info=True)
            await callback.answer("Xatolik yuz berdi.", show_alert=True)

    async def show_lesson_detail'''

content = content.replace(old_code, new_code)

with open('handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed show_group_details function')
