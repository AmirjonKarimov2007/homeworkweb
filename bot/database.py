import re
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Dict, List, Optional

import asyncpg
from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings

from models import Group, Homework, HomeworkSubmission, Lesson, LessonDetail, Teacher, User

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_PHONE: str
    DATABASE_URL: str
    LOG_LEVEL: str = "INFO"
    POOL_SIZE: int = 20
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

logger.remove()
logger.add(
    lambda msg: print(f"\033[94m{msg}\033[0m"),
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}",
    colorize=True,
)
logger.add(
    "bot.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {function}:{line} | {message}",
)


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.user_cache: Dict[int, User] = {}

    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=settings.POOL_SIZE,
            command_timeout=60,
            server_settings={
                "application_name": "telegram_bot",
                "timezone": "Asia/Tashkent",
            },
        )
        logger.info("Database connection pool created successfully")

    async def close(self):
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            raise ConnectionError("Database not initialized")

        connection = None
        try:
            connection = await self.pool.acquire()
            yield connection
        finally:
            if connection:
                await self.pool.release(connection)

    @staticmethod
    def normalize_phone(phone: str) -> str:
        digits = re.sub(r"[^\d]", "", phone)
        if digits.startswith("998998"):
            digits = digits[3:]
        if digits.startswith("998"):
            digits = digits[3:]
        if len(digits) == 9 and digits.startswith("9"):
            return f"+998{digits}"
        return phone if phone.startswith("+") else f"+{phone}"

    async def check_user_by_phone(self, phone: str) -> Optional[User]:
        try:
            normalized_phone = self.normalize_phone(phone)
            raw_variants = {
                normalized_phone,
                normalized_phone.lstrip("+"),
            }
            digits = re.sub(r"[^\d]", "", normalized_phone)
            if len(digits) == 12 and digits.startswith("998"):
                raw_variants.add(f"+998 {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}")
                raw_variants.add(f"+998 {digits[3:5]} {digits[5:7]} {digits[7:9]} {digits[9:]}")

            async with self.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT u.id, u.full_name, u.role, u.phone, tl.telegram_id
                    FROM users u
                    LEFT JOIN telegram_links tl ON tl.user_id = u.id
                    WHERE u.phone = ANY($1::text[])
                    ORDER BY u.id DESC
                    LIMIT 1
                    """,
                    list(raw_variants),
                )
                if not result:
                    return None
                return User(
                    id=result["id"],
                    full_name=result["full_name"],
                    role=result["role"],
                    phone=result["phone"],
                    telegram_id=result["telegram_id"],
                )
        except Exception as e:
            logger.error(f"Error checking user by phone {phone}: {e}")
            return None

    async def update_telegram_id(self, user_id: int, telegram_id: Optional[int]) -> bool:
        try:
            async with self.get_connection() as conn:
                existing = await conn.fetchrow(
                    "SELECT id, telegram_id FROM telegram_links WHERE user_id = $1",
                    user_id,
                )
                if telegram_id is None:
                    if existing:
                        await conn.execute("DELETE FROM telegram_links WHERE user_id = $1", user_id)
                    return True

                if existing:
                    if existing["telegram_id"] != telegram_id:
                        await conn.execute(
                            "UPDATE telegram_links SET telegram_id = $1, linked_at = NOW() WHERE user_id = $2",
                            telegram_id,
                            user_id,
                        )
                else:
                    await conn.execute(
                        "INSERT INTO telegram_links (user_id, telegram_id, linked_at) VALUES ($1, $2, NOW())",
                        user_id,
                        telegram_id,
                    )
                return True
        except Exception as e:
            logger.error(f"Error updating telegram link for user {user_id}: {e}")
            return False

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        cached = self.user_cache.get(telegram_id)
        if cached:
            return cached

        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT u.id, u.full_name, u.role, u.phone, tl.telegram_id
                    FROM users u
                    JOIN telegram_links tl ON tl.user_id = u.id
                    WHERE tl.telegram_id = $1
                    """,
                    telegram_id,
                )
                if not result:
                    return None
                user = User(
                    id=result["id"],
                    full_name=result["full_name"],
                    role=result["role"],
                    phone=result["phone"],
                    telegram_id=result["telegram_id"],
                )
                self.cache_user(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
            return None

    def cache_user(self, user: User):
        if user.telegram_id:
            self.user_cache[user.telegram_id] = user

    def remove_user_from_cache(self, telegram_id: int):
        self.user_cache.pop(telegram_id, None)

    async def get_user_groups(self, user_id: int, role: str) -> List[Group]:
        try:
            async with self.get_connection() as conn:
                if role == "STUDENT":
                    query = """
                        SELECT g.id, g.name, g.schedule_time, g.goal_type
                        FROM groups g
                        JOIN student_group_enrollments sge ON sge.group_id = g.id
                        WHERE sge.student_id = $1
                          AND sge.status = 'ACTIVE'
                          AND g.is_active = true
                        ORDER BY g.name
                    """
                    rows = await conn.fetch(query, user_id)
                elif role == "TEACHER":
                    query = """
                        SELECT DISTINCT g.id, g.name, g.schedule_time, g.goal_type
                        FROM groups g
                        LEFT JOIN group_teachers gt ON gt.group_id = g.id
                        WHERE g.is_active = true
                          AND (
                            g.primary_teacher_id = $1
                            OR gt.teacher_id = $1
                          )
                        ORDER BY g.name
                    """
                    rows = await conn.fetch(query, user_id)
                elif role in ["ADMIN", "SUPER_ADMIN"]:
                    query = """
                        SELECT g.id, g.name, g.schedule_time, g.goal_type
                        FROM groups g
                        WHERE g.is_active = true
                        ORDER BY g.name
                    """
                    rows = await conn.fetch(query)
                else:
                    rows = []

                return [
                    Group(
                        id=row["id"],
                        name=row["name"],
                        schedule_time=row["schedule_time"],
                        goal_type=row["goal_type"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting groups for user {user_id}: {e}")
            return []

    async def get_group_by_id(self, group_id: int) -> Optional[Group]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT id, name, schedule_time, goal_type
                    FROM groups
                    WHERE id = $1 AND is_active = true
                    """,
                    group_id,
                )
                if not row:
                    return None
                return Group(
                    id=row["id"],
                    name=row["name"],
                    schedule_time=row["schedule_time"],
                    goal_type=row["goal_type"],
                )
        except Exception as e:
            logger.error(f"Error getting group {group_id}: {e}")
            return None

    async def get_teachers(self) -> List[Teacher]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, full_name, phone
                    FROM users
                    WHERE role = 'TEACHER' AND is_active = true
                    ORDER BY full_name
                    """
                )
                return [Teacher(**row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting teachers: {e}")
            return []

    async def get_lessons_by_group(self, group_id: int, offset: int = 0, limit: int = 10) -> List[Lesson]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT l.id, l.title, l.date, l.description, l.status, u.full_name AS created_by
                    FROM lessons l
                    JOIN users u ON u.id = l.created_by
                    WHERE l.group_id = $1
                      AND COALESCE(l.visible_to_students, true) = true
                    ORDER BY l.date DESC, l.id DESC
                    LIMIT $2 OFFSET $3
                    """,
                    group_id,
                    limit,
                    offset,
                )
                return [
                    Lesson(
                        id=row["id"],
                        title=row["title"],
                        date=row["date"],
                        description=row["description"],
                        status=row["status"],
                        created_by=row["created_by"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting lessons for group {group_id}: {e}")
            return []

    async def get_lessons_count(self, group_id: int) -> int:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT COUNT(*) AS count
                    FROM lessons
                    WHERE group_id = $1
                      AND COALESCE(visible_to_students, true) = true
                    """,
                    group_id,
                )
                return int(row["count"]) if row else 0
        except Exception as e:
            logger.error(f"Error getting lesson count for group {group_id}: {e}")
            return 0

    async def get_lesson_detail(self, lesson_id: int) -> Optional[LessonDetail]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT
                        l.id,
                        l.title,
                        l.date,
                        l.description,
                        h.id AS homework_id,
                        h.title AS homework_title,
                        h.instructions AS homework_instructions,
                        h.due_date AS homework_due_date
                    FROM lessons l
                    LEFT JOIN homework_tasks h ON h.lesson_id = l.id
                    WHERE l.id = $1
                    ORDER BY h.created_at DESC NULLS LAST
                    LIMIT 1
                    """,
                    lesson_id,
                )
                if not row:
                    return None
                return LessonDetail(
                    id=row["id"],
                    title=row["title"],
                    date=row["date"],
                    description=row["description"],
                    homework_id=row["homework_id"],
                    homework_title=row["homework_title"],
                    homework_instructions=row["homework_instructions"],
                    homework_due_date=row["homework_due_date"],
                )
        except Exception as e:
            logger.error(f"Error getting lesson detail {lesson_id}: {e}")
            return None

    async def get_lesson_group_id(self, lesson_id: int) -> Optional[int]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT group_id FROM lessons WHERE id = $1",
                    lesson_id,
                )
                return int(row["group_id"]) if row and row["group_id"] is not None else None
        except Exception as e:
            logger.error(f"Error getting lesson group id for lesson {lesson_id}: {e}")
            return None

    async def get_homework_for_lesson(self, lesson_id: int) -> Optional[Homework]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT h.id, h.title, h.instructions, h.due_date, l.title AS lesson_title
                    FROM homework_tasks h
                    JOIN lessons l ON l.id = h.lesson_id
                    WHERE h.lesson_id = $1
                    ORDER BY h.created_at DESC
                    LIMIT 1
                    """,
                    lesson_id,
                )
                if not row:
                    return None
                return Homework(
                    id=row["id"],
                    title=row["title"],
                    description=row["instructions"],
                    due_date=row["due_date"],
                    lesson_title=row["lesson_title"],
                )
        except Exception as e:
            logger.error(f"Error getting homework for lesson {lesson_id}: {e}")
            return None

    async def get_student_submission_status(self, student_id: int, homework_id: int) -> Optional[str]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT status
                    FROM homework_submissions
                    WHERE student_id = $1 AND homework_id = $2
                    ORDER BY submitted_at DESC, id DESC
                    LIMIT 1
                    """,
                    student_id,
                    homework_id,
                )
                return row["status"] if row else None
        except Exception as e:
            logger.error(f"Error getting submission status: {e}")
            return None

    async def get_homework_by_group(self, group_id: int, offset: int = 0, limit: int = 10) -> List[Homework]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT h.id, h.title, h.instructions, h.due_date, l.title AS lesson_title
                    FROM homework_tasks h
                    JOIN lessons l ON l.id = h.lesson_id
                    WHERE l.group_id = $1
                    ORDER BY COALESCE(h.due_date, l.date::timestamp) DESC, h.id DESC
                    LIMIT $2 OFFSET $3
                    """,
                    group_id,
                    limit,
                    offset,
                )
                return [
                    Homework(
                        id=row["id"],
                        title=row["title"],
                        description=row["instructions"],
                        due_date=row["due_date"],
                        lesson_title=row["lesson_title"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting homework for group {group_id}: {e}")
            return []

    async def get_homework_count(self, group_id: int) -> int:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT COUNT(*) AS count
                    FROM homework_tasks h
                    JOIN lessons l ON l.id = h.lesson_id
                    WHERE l.group_id = $1
                    """,
                    group_id,
                )
                return int(row["count"]) if row else 0
        except Exception as e:
            logger.error(f"Error getting homework count for group {group_id}: {e}")
            return 0

    async def get_student_homework_submissions(
        self, student_id: int, offset: int = 0, limit: int = 10
    ) -> List[HomeworkSubmission]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT hs.id, h.title, h.due_date, hs.status, hs.submitted_at, hs.text
                    FROM homework_submissions hs
                    JOIN homework_tasks h ON h.id = hs.homework_id
                    WHERE hs.student_id = $1
                    ORDER BY hs.submitted_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    student_id,
                    limit,
                    offset,
                )
                return [
                    HomeworkSubmission(
                        id=row["id"],
                        homework_title=row["title"],
                        due_date=row["due_date"],
                        status=row["status"],
                        submitted_at=row["submitted_at"],
                        text_content=row["text"],
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting student submissions for {student_id}: {e}")
            return []

    async def get_student_submissions_count(self, student_id: int) -> int:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT COUNT(*) AS count FROM homework_submissions WHERE student_id = $1",
                    student_id,
                )
                return int(row["count"]) if row else 0
        except Exception as e:
            logger.error(f"Error getting student submission count for {student_id}: {e}")
            return 0

    async def get_students_by_group(self, group_id: int, offset: int = 0, limit: int = 10) -> List[User]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT u.id, u.full_name, u.role, u.phone
                    FROM users u
                    JOIN student_group_enrollments sge ON sge.student_id = u.id
                    WHERE sge.group_id = $1
                      AND sge.status = 'ACTIVE'
                      AND u.is_active = true
                    ORDER BY u.full_name
                    LIMIT $2 OFFSET $3
                    """,
                    group_id,
                    limit,
                    offset,
                )
                return [
                    User(
                        id=row["id"],
                        full_name=row["full_name"],
                        role=row["role"],
                        phone=row["phone"],
                        telegram_id=None,
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting students by group {group_id}: {e}")
            return []

    async def get_students_count(self, group_id: int) -> int:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT COUNT(*) AS count
                    FROM student_group_enrollments
                    WHERE group_id = $1 AND status = 'ACTIVE'
                    """,
                    group_id,
                )
                return int(row["count"]) if row else 0
        except Exception as e:
            logger.error(f"Error getting student count for group {group_id}: {e}")
            return 0

    async def get_group_student_telegram_ids(self, group_id: int) -> List[int]:
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT tl.telegram_id
                    FROM student_group_enrollments sge
                    JOIN users u ON u.id = sge.student_id
                    JOIN telegram_links tl ON tl.user_id = u.id
                    WHERE sge.group_id = $1
                      AND sge.status = 'ACTIVE'
                      AND u.is_active = true
                      AND tl.telegram_id IS NOT NULL
                    """,
                    group_id,
                )
                return [int(row["telegram_id"]) for row in rows]
        except Exception as e:
            logger.error(f"Error getting telegram ids for group {group_id}: {e}")
            return []

    async def get_student_submission_for_lesson(self, student_id: int, lesson_id: int) -> Optional[dict]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT
                        hs.id AS submission_id,
                        hs.text,
                        hs.status,
                        hs.submitted_at,
                        h.id AS homework_id,
                        h.title AS homework_title,
                        h.instructions,
                        h.due_date
                    FROM homework_tasks h
                    LEFT JOIN homework_submissions hs
                      ON hs.homework_id = h.id AND hs.student_id = $1
                    WHERE h.lesson_id = $2
                    ORDER BY hs.submitted_at DESC NULLS LAST, h.created_at DESC
                    LIMIT 1
                    """,
                    student_id,
                    lesson_id,
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting student submission for lesson {lesson_id}: {e}")
            return None

    async def get_lesson_stats(self, lesson_id: int) -> Optional[dict]:
        try:
            async with self.get_connection() as conn:
                homework = await conn.fetchrow(
                    """
                    SELECT h.id, l.group_id
                    FROM homework_tasks h
                    JOIN lessons l ON l.id = h.lesson_id
                    WHERE h.lesson_id = $1
                    ORDER BY h.created_at DESC
                    LIMIT 1
                    """,
                    lesson_id,
                )
                if not homework:
                    lesson = await conn.fetchrow("SELECT group_id FROM lessons WHERE id = $1", lesson_id)
                    if not lesson:
                        return None
                    group_id = lesson["group_id"]
                    students = await conn.fetch(
                        """
                        SELECT u.full_name
                        FROM users u
                        JOIN student_group_enrollments sge ON sge.student_id = u.id
                        WHERE sge.group_id = $1 AND sge.status = 'ACTIVE'
                        ORDER BY u.full_name
                        """,
                        group_id,
                    )
                    not_submitted = [row["full_name"] for row in students]
                    return {
                        "homework_id": None,
                        "submitted_count": 0,
                        "not_submitted_count": len(not_submitted),
                        "submitted_names": [],
                        "not_submitted_names": not_submitted,
                    }

                group_id = homework["group_id"]
                homework_id = homework["id"]

                submitted_rows = await conn.fetch(
                    """
                    SELECT DISTINCT u.full_name
                    FROM homework_submissions hs
                    JOIN users u ON u.id = hs.student_id
                    WHERE hs.homework_id = $1
                    ORDER BY u.full_name
                    """,
                    homework_id,
                )
                submitted_names = [row["full_name"] for row in submitted_rows]

                not_submitted_rows = await conn.fetch(
                    """
                    SELECT u.full_name
                    FROM users u
                    JOIN student_group_enrollments sge ON sge.student_id = u.id
                    WHERE sge.group_id = $1
                      AND sge.status = 'ACTIVE'
                      AND NOT EXISTS (
                        SELECT 1
                        FROM homework_submissions hs
                        WHERE hs.homework_id = $2
                          AND hs.student_id = u.id
                      )
                    ORDER BY u.full_name
                    """,
                    group_id,
                    homework_id,
                )
                not_submitted_names = [row["full_name"] for row in not_submitted_rows]

                return {
                    "homework_id": homework_id,
                    "submitted_count": len(submitted_names),
                    "not_submitted_count": len(not_submitted_names),
                    "submitted_names": submitted_names,
                    "not_submitted_names": not_submitted_names,
                }
        except Exception as e:
            logger.error(f"Error getting lesson stats {lesson_id}: {e}")
            return None

    async def update_submission_status(self, submission_id: int, reviewer_id: int, status: str) -> bool:
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    UPDATE homework_submissions
                    SET status = $1,
                        reviewed_by = $2,
                        reviewed_at = NOW()
                    WHERE id = $3
                    """,
                    status,
                    reviewer_id,
                    submission_id,
                )
                return True
        except Exception as e:
            logger.error(f"Error updating submission status {submission_id}: {e}")
            return False

    async def create_lesson(self, group_id: int, title: str, description: Optional[str], teacher_id: int, lesson_date: date) -> Optional[int]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO lessons (group_id, title, date, description, created_by, created_at, visible_to_students)
                    VALUES ($1, $2, $3, $4, $5, NOW(), true)
                    RETURNING id
                    """,
                    group_id,
                    title,
                    lesson_date,
                    description,
                    teacher_id,
                )
                return int(row["id"]) if row else None
        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            return None

    async def create_homework(self, lesson_id: int, title: str, instructions: str, teacher_id: int, due_date: datetime = None) -> Optional[int]:
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO homework_tasks (
                        lesson_id,
                        title,
                        instructions,
                        due_date,
                        allow_late_submission,
                        max_revision_attempts,
                        created_by,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, true, 2, $5, NOW())
                    RETURNING id
                    """,
                    lesson_id,
                    title,
                    instructions,
                    due_date,
                    teacher_id,
                )
                return int(row["id"]) if row else None
        except Exception as e:
            logger.error(f"Error creating homework: {e}")
            return None

    async def update_homework(self, homework_id: int, title: str, instructions: str, due_date: Optional[datetime]) -> bool:
        try:
            async with self.get_connection() as conn:
                await conn.execute(
                    """
                    UPDATE homework_tasks
                    SET title = $1,
                        instructions = $2,
                        due_date = $3
                    WHERE id = $4
                    """,
                    title,
                    instructions,
                    due_date,
                    homework_id,
                )
                return True
        except Exception as e:
            logger.error(f"Error updating homework {homework_id}: {e}")
            return False

    async def submit_homework(self, user_id: int, homework_id: int, text: str) -> str:
        try:
            async with self.get_connection() as conn:
                existing = await conn.fetchrow(
                    """
                    SELECT id, status, reviewed_by
                    FROM homework_submissions
                    WHERE homework_id = $1 AND student_id = $2
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    homework_id,
                    user_id,
                )
                if existing:
                    if existing["reviewed_by"] is not None or existing["status"] in {
                        "ACCEPTED",
                        "REVISION_REQUESTED",
                        "REVIEWED",
                    }:
                        return "LOCKED"
                    await conn.execute(
                        """
                        UPDATE homework_submissions
                        SET text = $1,
                            status = 'SUBMITTED',
                            submitted_at = NOW(),
                            reviewed_by = NULL,
                            reviewed_at = NULL
                        WHERE id = $2
                        """,
                        text,
                        existing["id"],
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO homework_submissions (homework_id, student_id, status, text, submitted_at, revision_count)
                        VALUES ($1, $2, 'SUBMITTED', $3, NOW(), 0)
                        """,
                        homework_id,
                        user_id,
                        text,
                    )
                return "OK"
        except Exception as e:
            logger.error(f"Error submitting homework: {e}")
            return "ERROR"


db = Database()
