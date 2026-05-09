import os
import re
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import asyncpg
from dotenv import load_dotenv
from loguru import logger
from pydantic_settings import BaseSettings

from models import Group, Homework, HomeworkSubmission, Lesson, LessonDetail, Teacher, User

# Bot papkasidan 2 daraja tepaga ko'tarib root .env ni topamiz
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = os.path.join(BASE_DIR.parent, ".env")
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_PHONE: str
    ADMIN_IDS: str = ""  # Vergul bilan ajratilgan admin ID lar
    DATABASE_URL_BOT: str = ""
    DATABASE_URL: str = ""
    ADMIN_ID: str = ""
    LOG_LEVEL: str = "INFO"
    POOL_SIZE: int = 20
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    model_config = {"env_file": ENV_FILE, "extra": "ignore"}

    @property
    def DATABASE_URL_FOR_BOT(self) -> str:
        """Bot uses postgresql://, not postgresql+asyncpg://"""
        return self.DATABASE_URL_BOT or self.DATABASE_URL.replace("+asyncpg", "", 1)


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
            settings.DATABASE_URL_FOR_BOT,
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
                        ORDER BY g.id DESC
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
                    INSERT INTO lessons (group_id, title, date, description, created_by, created_at, visible_to_students, status)
                    VALUES ($1, $2, $3, $4, $5, NOW(), true, 'YANGI')
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

    async def ensure_admin_exists(self) -> bool:
        """Create admin user if not exists"""
        import bcrypt

        async with self.get_connection() as conn:
            # Check if admin already exists
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE phone = $1",
                "+998917897621"
            )

            if existing:
                logger.info("Admin already exists")
                return True

            # Hash password
            password = "Karimoff2007"
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Create admin
            await conn.execute(
                """
                INSERT INTO users (full_name, phone, email, role, hashed_password, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, 'SUPER_ADMIN', $4, true, NOW(), NOW())
                RETURNING id
                """,
                "Amirjon Karimov",
                "+998917897621",
                "amirjon@example.com",
                hashed
            )
            logger.info("✅ Admin created: +998917897621 / Karimoff2007")
            return True

    async def get_all_students_for_broadcast(self) -> List[int]:
        """Hamma o'quvchilarning telegram IDlarini olish (Super Admin uchun)"""
        try:
            async with self.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT tl.telegram_id
                    FROM users u
                    JOIN telegram_links tl ON tl.user_id = u.id
                    WHERE u.role IN ('TEACHER', 'STUDENT')
                      AND tl.telegram_id IS NOT NULL
                    """
                )
                return [int(row["telegram_id"]) for row in rows]
        except Exception as e:
            logger.error(f"Error getting students for broadcast: {e}")
            return []

    async def create_broadcast_homework(
        self,
        teacher_id: int,
        title: str,
        instructions: str,
        due_date: Optional[datetime] = None,
        message: Optional[str] = None,
    ) -> Optional[int]:
        """Broadcast homework yaratish (Super Admin uchun)"""
        try:
            async with self.get_connection() as conn:
                # Bir guruhga homework yaratamiz (yoki "umumiy")
                group_ids = await conn.fetch(
                    "SELECT id FROM groups WHERE is_active = true"
                )

                homework_ids = []
                for group_id in [row["id"] for row in group_ids]:
                    # Har guruhda dars yaratamiz
                    lessons = await conn.fetch(
                        "SELECT id FROM lessons WHERE group_id = $1 ORDER BY id DESC LIMIT 1",
                        group_id,
                    )

                    for lesson in lessons:
                        homework = await conn.fetchrow(
                            "SELECT id FROM homework_tasks WHERE lesson_id = $1",
                            lesson["id"],
                        )

                        if homework:
                            homework_ids.append(homework["id"])

                if not homework_ids:
                    logger.error("Hech qanday dars yoki homework topilmadi.")
                    return 0

                # Notification yaratish
                notification_ids = []
                for hw_id in homework_ids:
                    result = await conn.execute(
                        """
                        INSERT INTO notifications (title, message, role, created_at)
                        VALUES ($1, $2, 'BROADCAST', 'SUPER_ADMIN', NOW())
                        RETURNING id
                        """,
                        f"📢 {title}",
                        message,
                        'SUPER_ADMIN',
                    )
                    notification_ids.append(result)

                # Har o'quvchiga submission yaratamiz
                student_ids = await self.get_all_students_for_broadcast()
                for student_id in student_ids:
                    for hw_id in homework_ids:
                        # Submission allaqachon bormi
                        existing = await conn.fetchrow(
                            "SELECT id FROM homework_submissions WHERE student_id = $1 AND homework_id = $2",
                            student_id,
                            hw_id,
                        )

                        submission_id = existing["id"] if existing else None

                        if submission_id is None:
                            result = await conn.execute(
                                """
                                INSERT INTO homework_submissions
                                (homework_id, student_id, status, text, submitted_at, revision_count)
                                VALUES ($1, $2, 'BROADCAST', '', NOW(), 0)
                                RETURNING id
                                """,
                                hw_id,
                                student_id,
                                'BROADCAST',
                                '',
                            )

                return 0 if not homework_ids else homework_ids[0]
        except Exception as e:
            logger.error(f"Error creating broadcast homework: {e}")
            return None

    async def get_debtors(self) -> List[dict]:
        """Qarzdorlar ro'yxatini olish - hozirda qarzdor bo'lgan o'quvchilar"""
        try:
            async with self.get_connection() as conn:
                # Hozirgi oy va yilni olish
                current_month = datetime.now().month
                current_year = datetime.now().year

                # Qarzdor o'quvchilarni olish
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT
                        u.id AS student_id,
                        u.full_name AS student_name,
                        u.phone AS student_phone,
                        p.month,
                        p.billing_year,
                        p.amount_due,
                        p.amount_paid,
                        p.status AS payment_status,
                        p.due_date,
                        g.name AS group_name
                    FROM payments p
                    JOIN users u ON u.id = p.student_id
                    JOIN groups g ON g.id = p.group_id
                    WHERE p.status IN ('PENDING', 'OVERDUE')
                      AND p.billing_year = $1
                      AND p.billing_month = $2
                    ORDER BY p.due_date ASC, u.full_name
                    """,
                    current_year,
                    current_month,
                )

                debtors = []
                for row in rows:
                    debtors.append({
                        'student_id': row['student_id'],
                        'student_name': row['student_name'],
                        'student_phone': row['student_phone'],
                        'month': row['month'],
                        'billing_year': row['billing_year'],
                        'amount_due': float(row['amount_due']) if row['amount_due'] else 0,
                        'amount_paid': float(row['amount_paid']) if row['amount_paid'] else 0,
                        'payment_status': row['payment_status'],
                        'due_date': row['due_date'],
                        'group_name': row['group_name']
                    })

                logger.info(f"✅ {len(debtors)} ta qarzdor topildi")
                return debtors
        except Exception as e:
            logger.error(f"Error getting debtors: {e}")
            return []

    async def get_debtors_with_telegram_ids(self) -> List[dict]:
        """Qarzdorlar va ularning telegram ID larini olish"""
        try:
            async with self.get_connection() as conn:
                # Hozirgi oy va yilni olish
                current_month = datetime.now().month
                current_year = datetime.now().year

                # Qarzdor o'quvchilarni va ularning telegram ID larini olish
                rows = await conn.fetch(
                    """
                    SELECT DISTINCT
                        u.id AS student_id,
                        u.full_name AS student_name,
                        u.phone AS student_phone,
                        tl.telegram_id,
                        p.month,
                        p.billing_year,
                        p.amount_due,
                        p.amount_paid,
                        p.status AS payment_status,
                        p.due_date,
                        g.name AS group_name
                    FROM payments p
                    JOIN users u ON u.id = p.student_id
                    JOIN groups g ON g.id = p.group_id
                    LEFT JOIN telegram_links tl ON tl.user_id = u.id
                    WHERE p.status IN ('PENDING', 'OVERDUE')
                      AND p.billing_year = $1
                      AND p.billing_month = $2
                    ORDER BY p.due_date ASC, u.full_name
                    """,
                    current_year,
                    current_month,
                )

                debtors = []
                for row in rows:
                    amount_due = float(row['amount_due']) if row['amount_due'] else 0
                    amount_paid = float(row['amount_paid']) if row['amount_paid'] else 0
                    debt = amount_due - amount_paid

                    debtors.append({
                        'student_id': row['student_id'],
                        'student_name': row['student_name'],
                        'student_phone': row['student_phone'],
                        'telegram_id': row['telegram_id'],
                        'month': row['month'],
                        'billing_year': row['billing_year'],
                        'amount_due': amount_due,
                        'amount_paid': amount_paid,
                        'debt': debt,
                        'payment_status': row['payment_status'],
                        'due_date': row['due_date'],
                        'group_name': row['group_name']
                    })

                logger.info(f"✅ {len(debtors)} ta qarzdor (telegram ID bilan) topildi")
                return debtors
        except Exception as e:
            logger.error(f"Error getting debtors with telegram IDs: {e}")
            return []

    async def create_superuser(self, full_name: str, phone: str, password: str, telegram_id: Optional[int] = None) -> bool:
        """Yangi SuperAdmin yaratish"""
        try:
            import bcrypt

            async with self.get_connection() as conn:
                # Telefon raqam allaqachon ishlatilganmi
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE phone = $1", phone
                )
                if existing:
                    logger.warning(f"Telefon raqam {phone} allaqachon ro'yxatdan o'tgan")
                    return False

                # Parolni hash qilish
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

                # User yaratish
                user_result = await conn.fetchrow(
                    """
                    INSERT INTO users (full_name, phone, email, role, hashed_password, is_active, created_at, updated_at)
                    VALUES ($1, $2, $3, 'SUPER_ADMIN', $4, true, NOW(), NOW())
                    RETURNING id
                    """,
                    full_name, phone, f"{phone.replace('+', '')}@example.com", hashed_password
                )

                user_id = user_result["id"]

                # Telegram ID ni biriktirish
                if telegram_id:
                    await conn.execute(
                        """
                        INSERT INTO telegram_links (user_id, telegram_id, linked_at)
                        VALUES ($1, $2, NOW())
                        """,
                        user_id, telegram_id
                    )

                logger.info(f"✅ Yangi SuperAdmin yaratildi: {full_name} (ID: {user_id}, Phone: {phone})")
                return True

        except Exception as e:
            logger.error(f"Error creating superuser: {e}")
            return False

    async def init_database_tables(self) -> bool:
        """Initialize all required database tables"""
        from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, Text, Date, ForeignKey, Float, Enum
        from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
        import enum

        async with self.get_connection() as conn:
            # Create tables using raw SQL for simplicity
            tables_sql = [
                # Users table
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20) UNIQUE NOT NULL,
                    email VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'STUDENT',
                    hashed_password VARCHAR(255),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Telegram links table
                """
                CREATE TABLE IF NOT EXISTS telegram_links (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                    telegram_id BIGINT UNIQUE,
                    username VARCHAR(255),
                    linked_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Courses table
                """
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Groups table
                """
                CREATE TABLE IF NOT EXISTS groups (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    goal_type VARCHAR(100),
                    level_label VARCHAR(50),
                    schedule_time VARCHAR(20),
                    start_date DATE,
                    end_date DATE,
                    duration_months INTEGER,
                    capacity INTEGER,
                    is_active BOOLEAN DEFAULT true,
                    primary_teacher_id INTEGER REFERENCES users(id),
                    monthly_fee FLOAT,
                    payment_day INTEGER DEFAULT 5,
                    grace_days INTEGER DEFAULT 2,
                    is_payment_required BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Group teachers table
                """
                CREATE TABLE IF NOT EXISTS group_teachers (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                    teacher_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Student group enrollments table
                """
                CREATE TABLE IF NOT EXISTS student_group_enrollments (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                    monthly_fee FLOAT,
                    status VARCHAR(50) DEFAULT 'ACTIVE',
                    enrolled_at TIMESTAMP DEFAULT NOW(),
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Lessons table
                """
                CREATE TABLE IF NOT EXISTS lessons (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    date DATE,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'YANGI',
                    visible_to_students BOOLEAN DEFAULT true,
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Attendance table
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    status VARCHAR(50) DEFAULT 'PRESENT',
                    notes TEXT,
                    marked_at TIMESTAMP DEFAULT NOW(),
                    marked_by INTEGER REFERENCES users(id)
                )
                """,

                # Homework tasks table
                """
                CREATE TABLE IF NOT EXISTS homework_tasks (
                    id SERIAL PRIMARY KEY,
                    lesson_id INTEGER REFERENCES lessons(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    instructions TEXT,
                    due_date TIMESTAMP,
                    allow_late_submission BOOLEAN DEFAULT true,
                    max_revision_attempts INTEGER DEFAULT 2,
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Homework submissions table
                """
                CREATE TABLE IF NOT EXISTS homework_submissions (
                    id SERIAL PRIMARY KEY,
                    homework_id INTEGER REFERENCES homework_tasks(id) ON DELETE CASCADE,
                    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    status VARCHAR(50) DEFAULT 'SUBMITTED',
                    text TEXT,
                    file_path VARCHAR(500),
                    revision_count INTEGER DEFAULT 0,
                    submitted_at TIMESTAMP DEFAULT NOW(),
                    reviewed_by INTEGER REFERENCES users(id),
                    reviewed_at TIMESTAMP,
                    feedback TEXT
                )
                """,

                # Payments table
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                    month VARCHAR(20),
                    billing_year INTEGER,
                    billing_month INTEGER,
                    amount_due FLOAT DEFAULT 0,
                    amount_paid FLOAT DEFAULT 0,
                    status VARCHAR(50) DEFAULT 'PENDING',
                    due_date DATE,
                    paid_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Materials table
                """
                CREATE TABLE IF NOT EXISTS materials (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    type VARCHAR(50) NOT NULL,
                    file_path VARCHAR(500),
                    link_url TEXT,
                    created_by INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Material group links table
                """
                CREATE TABLE IF NOT EXISTS material_group_links (
                    id SERIAL PRIMARY KEY,
                    material_id INTEGER REFERENCES materials(id) ON DELETE CASCADE,
                    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Notifications table
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    role VARCHAR(50),
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    is_sent BOOLEAN DEFAULT false,
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # Audit logs table
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(100),
                    entity_id INTEGER,
                    details JSONB,
                    ip_address VARCHAR(50),
                    created_at TIMESTAMP DEFAULT NOW()
                )
                """,

                # System settings table
                """
                CREATE TABLE IF NOT EXISTS system_settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
                """
            ]

            for table_sql in tables_sql:
                try:
                    await conn.execute(table_sql)
                except Exception as e:
                    logger.warning(f"Table creation warning: {e}")

            # Create indexes
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)",
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
                "CREATE INDEX IF NOT EXISTS idx_telegram_links_user_id ON telegram_links(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_telegram_links_telegram_id ON telegram_links(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_groups_primary_teacher ON groups(primary_teacher_id)",
                "CREATE INDEX IF NOT EXISTS idx_lessons_group_id ON lessons(group_id)",
                "CREATE INDEX IF NOT EXISTS idx_lessons_date ON lessons(date)",
                "CREATE INDEX IF NOT EXISTS idx_homework_lesson_id ON homework_tasks(lesson_id)",
                "CREATE INDEX IF NOT EXISTS idx_homework_due_date ON homework_tasks(due_date)",
                "CREATE INDEX IF NOT EXISTS idx_submissions_student ON homework_submissions(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_submissions_homework ON homework_submissions(homework_id)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_lesson ON attendance(lesson_id)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_student ON payments(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_group ON payments(group_id)",
                "CREATE INDEX IF NOT EXISTS idx_enrollments_student ON student_group_enrollments(student_id)",
                "CREATE INDEX IF NOT EXISTS idx_enrollments_group ON student_group_enrollments(group_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_role ON notifications(role)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            ]

            for index_sql in indexes_sql:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")

            # Ensure notifications table has role column (fix for existing tables)
            try:
                await conn.execute(
                    "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS role VARCHAR(50)"
                )
                logger.info("✅ notifications.role column ensured")
            except Exception as e:
                logger.debug(f"Role column already exists or couldn't be added: {e}")

            logger.info("✅ Database tables initialized")
            return True


db = Database()
