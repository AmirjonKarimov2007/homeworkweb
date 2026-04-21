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
from app.models.user import User
from app.models.group import Group, StudentGroupEnrollment
from app.models.lesson import Lesson
from app.models.homework import HomeworkTask, HomeworkSubmission
from app.models.payment import Payment
from app.models.notification import Notification
from app.models.telegram import TelegramLink
from sqlalchemy import select, and_, or_, func, desc, asc, text

class DatabaseService:
    def __init__(self):
        # Database URL - botda ham .env faylda bo'lishi kerak
        self.DATABASE_URL = "postgresql+asyncpg://postgres:12345678@localhost:5432/homeworkbot"
        self.engine = None  # We'll use backend's session

    async def get_session(self) -> AsyncSessionLocal:
        """Get database session from backend"""
        return AsyncSessionLocal()

    # User related methods
    async def find_user_by_phone(self, phone: str) -> Optional[User]:
        """Find user by phone number"""
        async with AsyncSessionLocal() as session:
            try:
                # Try with + prefix first
                result = await session.execute(
                    select(User).where(User.phone == phone)
                )
                user = result.scalar_one_or_none()

                if not user and not phone.startswith('+'):
                    # Try with + prefix if not found
                    phone_with_plus = f"+{phone}"
                    result = await session.execute(
                        select(User).where(User.phone == phone_with_plus)
                    )
                    user = result.scalar_one_or_none()

                return user
            except Exception as e:
                print(f"Error finding user by phone {phone}: {e}")
                return None

    async def find_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Find user by telegram_id"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(User).join(TelegramLink).where(
                        TelegramLink.telegram_id == telegram_id
                    )
                )
                return result.scalar_one_or_none()
            except Exception as e:
                print(f"Error finding user by telegram_id {telegram_id}: {e}")
                return None

    async def link_telegram_to_user(self, user_id: int, telegram_id: int, username: str = None) -> bool:
        """Link telegram to user"""
        async with AsyncSessionLocal() as session:
            try:
                # Check if already linked
                existing = await session.execute(
                    select(TelegramLink).where(TelegramLink.telegram_id == telegram_id)
                )
                if existing.scalar_one_or_none():
                    return False

                # Create new link
                link = TelegramLink(
                    user_id=user_id,
                    telegram_id=telegram_id,
                    username=username
                )
                session.add(link)
                await session.commit()
                return True
            except Exception as e:
                print(f"Error linking telegram to user: {e}")
                await session.rollback()
                return False

    # Group related methods
    async def get_user_groups(self, user_id: int) -> List[Group]:
        """Get groups for user"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Group).join(StudentGroupEnrollment).where(
                        StudentGroupEnrollment.user_id == user_id
                    ).order_by(Group.created_at.desc())
                )
                return result.scalars().all()
            except Exception as e:
                print(f"Error getting user groups: {e}")
                return []

    async def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """Get group by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Group).where(Group.id == group_id)
                )
                return result.scalar_one_or_none()
            except Exception as e:
                print(f"Error getting group by ID: {e}")
                return None

    async def get_users_by_group(self, group_id: int) -> List[User]:
        """Get users in group"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(User).join(StudentGroupEnrollment).join(Group).where(
                        Group.id == group_id
                    )
                )
                return result.scalars().all()
            except Exception as e:
                print(f"Error getting users by group: {e}")
                return []

    # Lesson related methods
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
                query = select(Lesson).where(Lesson.group_id == group_id)

                if only_upcoming:
                    # Show only future lessons, ordered by date (newest first)
                    query = query.where(Lesson.date > datetime.now()).order_by(
                        Lesson.date.desc(), Lesson.id.desc()
                    )
                else:
                    # Show all lessons, with newest first
                    query = query.order_by(Lesson.date.desc(), Lesson.id.desc())

                # Get total count
                count_result = await session.execute(select(func.count(Lesson.id)).where(Lesson.group_id == group_id))
                total_count = count_result.scalar()

                # Get paginated results
                lesson_result = await session.execute(
                    query.offset(offset).limit(page_size)
                )
                lessons = lesson_result.scalars().all()

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

    async def get_lesson_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """Get lesson by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Lesson).where(Lesson.id == lesson_id)
                )
                return result.scalar_one_or_none()
            except Exception as e:
                print(f"Error getting lesson by ID: {e}")
                return None

    # Homework related methods
    async def get_user_homework(self, user_id: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get homework for user"""
        async with AsyncSessionLocal() as session:
            try:
                offset = (page - 1) * page_size

                # Get user's groups
                user_groups = await self.get_user_groups(user_id)
                group_ids = [group.id for group in user_groups]

                if not group_ids:
                    return {
                        "homework": [],
                        "total_count": 0,
                        "page": 1,
                        "page_size": 10,
                        "total_pages": 0
                    }

                # Get homework for user's groups
                count_result = await session.execute(
                    select(func.count(HomeworkTask.id)).where(
                        HomeworkTask.group_id.in_(group_ids)
                    )
                )
                total_count = count_result.scalar()

                homework_result = await session.execute(
                    select(HomeworkTask)
                    .where(HomeworkTask.group_id.in_(group_ids))
                    .order_by(
                        HomeworkTask.due_date.desc(),
                        HomeworkTask.created_at.desc()
                    )
                    .offset(offset)
                    .limit(page_size)
                )
                homework_list = homework_result.scalars().all()

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

    async def get_homework_by_id(self, homework_id: int) -> Optional[HomeworkTask]:
        """Get homework by ID"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(HomeworkTask).where(HomeworkTask.id == homework_id)
                )
                return result.scalar_one_or_none()
            except Exception as e:
                print(f"Error getting homework by ID: {e}")
                return None

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
                user = await self.find_user_by_telegram_id(telegram_id)
                if not user:
                    return False

                # Create submission
                submission = HomeworkSubmission(
                    homework_task_id=homework_id,
                    user_id=user.id,
                    text=text
                )
                session.add(submission)
                await session.commit()
                return True
            except Exception as e:
                print(f"Error submitting homework: {e}")
                await session.rollback()
                return False

    async def get_homework_submissions(self, homework_id: int) -> List[Dict]:
        """Get homework submissions"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(HomeworkSubmission, User)
                    .join(User, HomeworkSubmission.user_id == User.id)
                    .where(HomeworkSubmission.homework_task_id == homework_id)
                    .order_by(HomeworkSubmission.submitted_at.desc())
                )

                submissions = []
                for submission, user in result:
                    submissions.append({
                        "id": submission.id,
                        "user_id": submission.user_id,
                        "user_name": user.full_name,
                        "text": submission.text,
                        "submitted_at": submission.submitted_at,
                        "status": submission.status.value
                    })

                return submissions
            except Exception as e:
                print(f"Error getting homework submissions: {e}")
                return []

    # Payment related methods
    async def get_user_payments(self, user_id: int) -> List[Payment]:
        """Get user payments"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Payment).where(
                        and_(
                            Payment.user_id == user_id,
                            Payment.status.in_(['pending', 'completed'])
                        )
                    ).order_by(Payment.due_date.desc())
                )
                return result.scalars().all()
            except Exception as e:
                print(f"Error getting user payments: {e}")
                return []

    # Notification methods
    async def send_notification(
        self,
        target_type: str,
        target_id: Optional[int],
        title: str,
        body: str,
        notification_type: str = "announcement",
        sent_by: Optional[int] = None
    ) -> bool:
        """Send notification"""
        async with AsyncSessionLocal() as session:
            try:
                # Determine recipients based on target type
                if target_type == "all":
                    # Get all telegram users
                    result = await session.execute(
                        select(User).join(TelegramLink)
                    )
                    users = result.scalars().all()
                elif target_type == "group":
                    # Get all users in specific group
                    result = await session.execute(
                        select(User).join(StudentGroupEnrollment).join(Group).where(
                            Group.id == target_id
                        )
                    )
                    users = result.scalars().all()
                else:
                    users = []

                # Create notifications
                for user in users:
                    notification = Notification(
                        user_id=user.id,
                        title=title,
                        body=body,
                        notification_type=notification_type,
                        target_type=target_type,
                        target_id=target_id,
                        sent_by=sent_by
                    )
                    session.add(notification)

                await session.commit()
                return True
            except Exception as e:
                print(f"Error sending notification: {e}")
                await session.rollback()
                return False

    # Admin methods
    async def get_all_groups(self) -> List[Group]:
        """Get all groups"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Group).order_by(Group.name))
                return result.scalars().all()
            except Exception as e:
                print(f"Error getting all groups: {e}")
                return []

    async def get_group_statistics(self, group_id: int) -> Dict[str, Any]:
        """Get group statistics"""
        async with AsyncSessionLocal() as session:
            try:
                # Get group info
                group_result = await session.execute(
                    select(Group).where(Group.id == group_id)
                )
                group = group_result.scalar_one_or_none()
                if not group:
                    return {}

                # Get total students
                students_result = await session.execute(
                    select(func.count(StudentGroupEnrollment.user_id)).where(
                        StudentGroupEnrollment.group_id == group_id
                    )
                )
                total_students = students_result.scalar()

                # Get homework count
                homework_result = await session.execute(
                    select(func.count(HomeworkTask.id)).where(HomeworkTask.group_id == group_id)
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
                    select(HomeworkTask).where(HomeworkTask.id == homework_id)
                )
                homework = homework_result.scalar_one_or_none()
                if not homework:
                    return {}

                # Get total submissions
                total_submissions_result = await session.execute(
                    select(func.count(HomeworkSubmission.id)).where(
                        HomeworkSubmission.homework_task_id == homework_id
                    )
                )
                total_submissions = total_submissions_result.scalar()

                # Get completed submissions
                completed_result = await session.execute(
                    select(func.count(HomeworkSubmission.id)).where(
                        and_(
                            HomeworkSubmission.homework_task_id == homework_id,
                            HomeworkSubmission.status == 'completed'
                        )
                    )
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
                    select(Group).where(Group.id == group_id)
                )
                group = group_result.scalar_one_or_none()
                if not group:
                    return {}

                # Get homework for this group
                homework_result = await session.execute(
                    select(HomeworkTask).where(HomeworkTask.group_id == group_id)
                    .order_by(HomeworkTask.created_at.desc())
                )
                homework_list = homework_result.scalars().all()

                return {
                    "group_name": group.name,
                    "homework": homework_list,
                    "total_count": len(homework_list)
                }
            except Exception as e:
                print(f"Error getting user homework for group: {e}")
                return {}


# Global database service instance
db_service = DatabaseService()