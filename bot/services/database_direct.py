import asyncio
import sys
import os
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

# Add backend directory to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.db.session import AsyncSessionLocal
from sqlalchemy import text, select, and_, or_, func, desc, asc

class DatabaseService:
    def __init__(self):
        pass

    # User related methods
    async def find_user_by_phone(self, phone: str) -> Optional[Any]:
        """Find user by phone number"""
        async with AsyncSessionLocal() as session:
            try:
                # Try with + prefix first
                result = await session.execute(
                    text("SELECT * FROM users WHERE phone = :phone"),
                    {"phone": phone}
                )
                user = result.fetchone()

                if not user and not phone.startswith('+'):
                    # Try with + prefix if not found
                    phone_with_plus = f"+{phone}"
                    result = await session.execute(
                        text("SELECT * FROM users WHERE phone = :phone"),
                        {"phone": phone_with_plus}
                    )
                    user = result.fetchone()

                return user
            except Exception as e:
                print(f"Error finding user by phone {phone}: {e}")
                return None

    async def get_all_groups(self) -> List[Any]:
        """Get all groups"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text("SELECT * FROM groups ORDER BY name")
                )
                return result.fetchall()
            except Exception as e:
                print(f"Error getting all groups: {e}")
                return []

    async def get_group_by_id(self, group_id: int) -> Optional[Any]:
        """Get group by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text("SELECT * FROM groups WHERE id = :id"),
                    {"id": group_id}
                )
                return result.fetchone()
            except Exception as e:
                print(f"Error getting group by ID: {e}")
                return None

    async def get_users_by_group(self, group_id: int) -> List[Any]:
        """Get users in group"""
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    SELECT u.* FROM users u
                    JOIN student_group_enrollments sge ON u.id = sge.user_id
                    JOIN groups g ON sge.group_id = g.id
                    WHERE g.id = :group_id
                """)
                result = await session.execute(query, {"group_id": group_id})
                return result.fetchall()
            except Exception as e:
                print(f"Error getting users by group: {e}")
                return []

    async def get_group_lessons(
        self,
        group_id: int,
        page: int = 1,
        page_size: int = 10,
        only_upcoming: bool = False
    ) -> Dict[str, Any]:
        """Get lessons for group with pagination"""
        async with AsyncSessionLocal() as session:
            try:
                offset = (page - 1) * page_size

                # Base query
                base_where = "WHERE group_id = :group_id"
                params = {"group_id": group_id}

                if only_upcoming:
                    base_where += " AND date > NOW()"
                    order_by = "ORDER BY date DESC, id DESC"
                else:
                    order_by = "ORDER BY date DESC, id DESC"

                # Get total count
                count_query = text(f"SELECT COUNT(*) FROM lessons {base_where}")
                count_result = await session.execute(count_query, params)
                total_count = count_result.scalar()

                # Get paginated results
                data_query = text(f"""
                    SELECT * FROM lessons {base_where}
                    {order_by}
                    LIMIT :limit OFFSET :offset
                """)
                params["limit"] = page_size
                params["offset"] = offset

                result = await session.execute(data_query, params)
                lessons = result.fetchall()

                return {
                    "lessons": lessons,
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            except Exception as e:
                print(f"Error getting group lessons: {e}")
                return {
                    "lessons": [],
                    "total_count": 0,
                    "page": 1,
                    "page_size": page_size,
                    "total_pages": 0
                }

    async def get_user_homework(self, user_id: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get homework for user"""
        async with AsyncSessionLocal() as session:
            try:
                offset = (page - 1) * page_size

                # Get user's groups
                groups_query = text("""
                    SELECT group_id FROM student_group_enrollments WHERE user_id = :user_id
                """)
                groups_result = await session.execute(groups_query, {"user_id": user_id})
                group_ids = [row[0] for row in groups_result.fetchall()]

                if not group_ids:
                    return {
                        "homework": [],
                        "total_count": 0,
                        "page": 1,
                        "page_size": 10,
                        "total_pages": 0
                    }

                # Get homework for user's groups
                count_query = text("""
                    SELECT COUNT(*) FROM homework_tasks
                    WHERE group_id = ANY(:group_ids)
                """)
                count_result = await session.execute(count_query, {"group_ids": group_ids})
                total_count = count_result.scalar()

                data_query = text("""
                    SELECT * FROM homework_tasks
                    WHERE group_id = ANY(:group_ids)
                    ORDER BY due_date DESC, created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {
                    "group_ids": group_ids,
                    "limit": page_size,
                    "offset": offset
                }

                result = await session.execute(data_query, params)
                homework_list = result.fetchall()

                return {
                    "homework": homework_list,
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            except Exception as e:
                print(f"Error getting user homework: {e}")
                return {
                    "homework": [],
                    "total_count": 0,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 0
                }

    async def get_user_groups(self, user_id: int) -> List[Any]:
        """Get groups for user"""
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    SELECT g.* FROM groups g
                    JOIN student_group_enrollments sge ON g.id = sge.group_id
                    WHERE sge.user_id = :user_id
                    ORDER BY g.created_at DESC
                """)
                result = await session.execute(query, {"user_id": user_id})
                return result.fetchall()
            except Exception as e:
                print(f"Error getting user groups: {e}")
                return []

    async def get_homework_by_id(self, homework_id: int) -> Optional[Any]:
        """Get homework by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    text("SELECT * FROM homework_tasks WHERE id = :id"),
                    {"id": homework_id}
                )
                return result.fetchone()
            except Exception as e:
                print(f"Error getting homework by ID: {e}")
                return None

    async def get_homework_submissions(self, homework_id: int) -> List[Dict]:
        """Get homework submissions"""
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    SELECT hs.*, u.full_name
                    FROM homework_submissions hs
                    JOIN users u ON hs.user_id = u.id
                    WHERE hs.homework_task_id = :homework_id
                    ORDER BY hs.submitted_at DESC
                """)
                result = await session.execute(query, {"homework_id": homework_id})

                submissions = []
                for row in result.fetchall():
                    submissions.append({
                        "id": row.id,
                        "user_id": row.user_id,
                        "user_name": row.full_name,
                        "text": row.text,
                        "submitted_at": row.submitted_at,
                        "status": row.status
                    })

                return submissions
            except Exception as e:
                print(f"Error getting homework submissions: {e}")
                return []

    async def submit_homework(
        self,
        homework_id: int,
        telegram_id: int,
        text: str
    ) -> bool:
        """Submit homework"""
        async with AsyncSessionLocal() as session:
            try:
                # Find user by telegram_id
                user_query = text("""
                    SELECT u.* FROM users u
                    JOIN telegram_links tl ON u.id = tl.user_id
                    WHERE tl.telegram_id = :telegram_id
                """)
                result = await session.execute(user_query, {"telegram_id": telegram_id})
                user = result.fetchone()

                if not user:
                    return False

                # Create submission
                insert_query = text("""
                    INSERT INTO homework_submissions
                    (homework_task_id, user_id, text, status, submitted_at)
                    VALUES (:homework_id, :user_id, :text, 'pending', NOW())
                """)
                await session.execute(insert_query, {
                    "homework_id": homework_id,
                    "user_id": user.id,
                    "text": text
                })
                await session.commit()
                return True
            except Exception as e:
                print(f"Error submitting homework: {e}")
                await session.rollback()
                return False

    async def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """Get group statistics"""
        async with AsyncSessionLocal() as session:
            try:
                # Get group info
                group_result = await session.execute(
                    text("SELECT * FROM groups WHERE id = :id"),
                    {"id": group_id}
                )
                group = group_result.fetchone()

                if not group:
                    return {}

                # Get total students
                students_result = await session.execute(
                    text("SELECT COUNT(*) FROM student_group_enrollments WHERE group_id = :group_id"),
                    {"group_id": group_id}
                )
                total_students = students_result.scalar()

                # Get homework count
                homework_result = await session.execute(
                    text("SELECT COUNT(*) FROM homework_tasks WHERE group_id = :group_id"),
                    {"group_id": group_id}
                )
                homework_count = homework_result.scalar()

                return {
                    "group_name": group.name,
                    "total_students": total_students,
                    "homework_count": homework_count
                }
            except Exception as e:
                print(f"Error getting group statistics: {e}")
                return {}

    async def get_homework_statistics(self, homework_id: int) -> Dict[str, Any]:
        """Get homework statistics"""
        async with AsyncSessionLocal() as session:
            try:
                # Get homework info
                homework_result = await session.execute(
                    text("SELECT * FROM homework_tasks WHERE id = :id"),
                    {"id": homework_id}
                )
                homework = homework_result.fetchone()

                if not homework:
                    return {}

                # Get total submissions
                total_result = await session.execute(
                    text("SELECT COUNT(*) FROM homework_submissions WHERE homework_task_id = :id"),
                    {"id": homework_id}
                )
                total_submissions = total_result.scalar()

                # Get completed submissions
                completed_result = await session.execute(
                    text("SELECT COUNT(*) FROM homework_submissions WHERE homework_task_id = :id AND status = 'completed'"),
                    {"id": homework_id}
                )
                completed_submissions = completed_result.scalar()

                return {
                    "homework_title": homework.title,
                    "total_submissions": total_submissions,
                    "completed_submissions": completed_submissions,
                    "completion_rate": (completed_submissions / total_submissions * 100) if total_submissions > 0 else 0
                }
            except Exception as e:
                print(f"Error getting homework statistics: {e}")
                return {}

    async def get_user_homework_for_group(self, group_id: int) -> Dict[str, Any]:
        """Get all homework for a specific group"""
        async with AsyncSessionLocal() as session:
            try:
                # Get group info
                group_result = await session.execute(
                    text("SELECT * FROM groups WHERE id = :id"),
                    {"id": group_id}
                )
                group = group_result.fetchone()

                if not group:
                    return {}

                # Get homework for this group
                homework_result = await session.execute(
                    text("""
                        SELECT * FROM homework_tasks
                        WHERE group_id = :group_id
                        ORDER BY created_at DESC
                    """),
                    {"group_id": group_id}
                )
                homework_list = homework_result.fetchall()

                return {
                    "group_name": group.name,
                    "homework": homework_list,
                    "total_count": len(homework_list)
                }
            except Exception as e:
                print(f"Error getting user homework for group: {e}")
                return {}

    async def find_user_by_telegram_id(self, telegram_id: int) -> Optional[Any]:
        """Find user by telegram_id"""
        async with AsyncSessionLocal() as session:
            try:
                query = text("""
                    SELECT u.* FROM users u
                    JOIN telegram_links tl ON u.id = tl.user_id
                    WHERE tl.telegram_id = :telegram_id
                """)
                result = await session.execute(query, {"telegram_id": telegram_id})
                return result.fetchone()
            except Exception as e:
                print(f"Error finding user by telegram_id {telegram_id}: {e}")
                return None

    async def link_telegram_to_user(self, user_id: int, telegram_id: int, username: str = None) -> bool:
        """Link telegram to user"""
        async with AsyncSessionLocal() as session:
            try:
                # Check if already linked
                check_query = text("SELECT id FROM telegram_links WHERE telegram_id = :telegram_id")
                result = await session.execute(check_query, {"telegram_id": telegram_id})
                if result.fetchone():
                    return False

                # Create new link
                insert_query = text("""
                    INSERT INTO telegram_links
                    (user_id, telegram_id, username, linked_at)
                    VALUES (:user_id, :telegram_id, :username, NOW())
                """)
                await session.execute(insert_query, {
                    "user_id": user_id,
                    "telegram_id": telegram_id,
                    "username": username
                })
                await session.commit()
                return True
            except Exception as e:
                print(f"Error linking telegram to user: {e}")
                await session.rollback()
                return False


# Global database service instance
db_service = DatabaseService()