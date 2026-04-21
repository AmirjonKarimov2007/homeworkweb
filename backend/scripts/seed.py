import asyncio
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Ensure backend root is on sys.path so `app` can be imported when running as a script
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.session import AsyncSessionLocal
from app.db.init import init_db
from app.core.security import hash_password
from app.utils.enums import Role, MaterialType, PaymentStatus
from app.models.user import User
from app.models.group import Group, StudentGroupEnrollment
from app.models.lesson import Lesson
from app.models.homework import HomeworkTask
from app.models.payment import Payment
from app.models.material import Material, MaterialGroupLink


async def seed():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(User))
        if result.first():
            print("Seed already applied")
            return

        super_admin = User(
            full_name="Super Admin",
            phone="+998900000001",
            email="superadmin@example.com",
            role=Role.SUPER_ADMIN,
            hashed_password=hash_password("Admin123!@#"),
            is_active=True,
        )
        admin = User(
            full_name="Admin",
            phone="+998900000002",
            email="admin@example.com",
            role=Role.ADMIN,
            hashed_password=hash_password("Admin123!@#"),
            is_active=True,
        )
        teacher = User(
            full_name="Teacher",
            phone="+998900000003",
            email="teacher@example.com",
            role=Role.TEACHER,
            hashed_password=hash_password("Teacher123!@#"),
            is_active=True,
        )
        student1 = User(
            full_name="Student One",
            phone="+998900000004",
            email=None,
            role=Role.STUDENT,
            hashed_password=hash_password("Student123!@#"),
            is_active=True,
        )
        student2 = User(
            full_name="Student Two",
            phone="+998900000005",
            email=None,
            role=Role.STUDENT,
            hashed_password=hash_password("Student123!@#"),
            is_active=True,
        )
        student3 = User(
            full_name="Student Three",
            phone="+998900000006",
            email=None,
            role=Role.STUDENT,
            hashed_password=hash_password("Student123!@#"),
            is_active=True,
        )

        session.add_all([super_admin, admin, teacher, student1, student2, student3])
        await session.commit()
        await session.refresh(teacher)
        await session.refresh(student1)
        await session.refresh(student2)
        await session.refresh(student3)

        start = date.today()
        end = start + timedelta(days=90)

        group1 = Group(
            name="Sarf-Nahv 20:00",
            goal_type="Sarf-Nahv",
            level_label="Beginner",
            schedule_time="20:00",
            start_date=start,
            end_date=end,
            duration_months=3,
            capacity=20,
            is_active=True,
            primary_teacher_id=teacher.id,
            monthly_fee=500000,
            payment_day=5,
            grace_days=2,
            is_payment_required=True,
        )
        group2 = Group(
            name="CEFR Evening",
            goal_type="CEFR",
            level_label="A1",
            schedule_time="18:00",
            start_date=start,
            end_date=end,
            duration_months=3,
            capacity=15,
            is_active=True,
            primary_teacher_id=teacher.id,
            monthly_fee=600000,
            payment_day=5,
            grace_days=2,
            is_payment_required=True,
        )
        session.add_all([group1, group2])
        await session.commit()
        await session.refresh(group1)
        await session.refresh(group2)

        enrollments = [
            StudentGroupEnrollment(student_id=student1.id, group_id=group1.id, monthly_fee=500000),
            StudentGroupEnrollment(student_id=student1.id, group_id=group2.id, monthly_fee=600000),
            StudentGroupEnrollment(student_id=student2.id, group_id=group1.id, monthly_fee=500000),
            StudentGroupEnrollment(student_id=student3.id, group_id=group2.id, monthly_fee=600000),
        ]
        session.add_all(enrollments)
        await session.commit()

        lesson1 = Lesson(group_id=group1.id, title="Intro to Nahv", date=date.today(), description="Basics", created_by=teacher.id)
        lesson2 = Lesson(group_id=group2.id, title="CEFR A1 Unit 1", date=date.today(), description="Greetings", created_by=teacher.id)
        session.add_all([lesson1, lesson2])
        await session.commit()
        await session.refresh(lesson1)
        await session.refresh(lesson2)

        hw1 = HomeworkTask(
            lesson_id=lesson1.id,
            title="Write 5 sentences",
            instructions="Write 5 sentences using new grammar.",
            due_date=datetime.utcnow(),
            allow_late_submission=True,
            max_revision_attempts=2,
            created_by=teacher.id,
        )
        hw2 = HomeworkTask(
            lesson_id=lesson2.id,
            title="Vocabulary practice",
            instructions="Practice greetings vocab.",
            due_date=datetime.utcnow(),
            allow_late_submission=True,
            max_revision_attempts=2,
            created_by=teacher.id,
        )
        session.add_all([hw1, hw2])

        now = datetime.utcnow()
        month_str = now.strftime("%Y-%m")
        payment1 = Payment(
            student_id=student1.id,
            group_id=group1.id,
            month=month_str,
            billing_year=now.year,
            billing_month=now.month,
            amount_due=500000,
            amount_paid=0,
            status=PaymentStatus.PENDING,
            due_date=now.date(),
        )
        payment2 = Payment(
            student_id=student2.id,
            group_id=group1.id,
            month=month_str,
            billing_year=now.year,
            billing_month=now.month,
            amount_due=500000,
            amount_paid=500000,
            status=PaymentStatus.PAID,
            due_date=now.date(),
        )
        session.add_all([payment1, payment2])

        material1 = Material(
            title="Nahv PDF",
            description="PDF for basics",
            type=MaterialType.PDF,
            file_path=None,
            created_by=admin.id,
        )
        material2 = Material(
            title="CEFR Link",
            description="External resource",
            type=MaterialType.LINK,
            link_url="https://example.com",
            created_by=admin.id,
        )
        session.add_all([material1, material2])
        await session.commit()
        await session.refresh(material1)
        await session.refresh(material2)

        session.add_all([
            MaterialGroupLink(material_id=material1.id, group_id=group1.id),
            MaterialGroupLink(material_id=material2.id, group_id=group2.id),
        ])

        lead1 = Lead(
            full_name="Lead One",
            phone="+998900000010",
            study_duration="3 months",
            current_level="A1",
            goal_type="CEFR",
            notes="Interested in evening group",
            status=LeadStatus.NEW,
        )
        lead2 = Lead(
            full_name="Lead Two",
            phone="+998900000011",
            study_duration="0",
            current_level="Beginner",
            goal_type="Zero level",
            notes="Morning group",
            status=LeadStatus.WARM,
        )
        session.add_all([lead1, lead2])

        await session.commit()
        print("Seed completed")


if __name__ == "__main__":
    asyncio.run(seed())
