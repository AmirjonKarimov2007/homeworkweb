from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.payment import Payment
from app.models.attendance import AttendanceRecord
from app.models.homework import HomeworkTask, HomeworkSubmission
from app.models.lesson import Lesson
from app.models.group import StudentGroupEnrollment
from app.services.notification_service import create_notification, send_telegram_messages_to_users
from app.services.payment_service import generate_monthly_payments
from app.utils.enums import Role, PaymentStatus, AttendanceStatus, EnrollmentStatus


async def create_monthly_payments(session: AsyncSession) -> None:
    await generate_monthly_payments(session)


async def send_payment_reminders(session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.role == Role.STUDENT, User.is_active == True))
    students = result.scalars().all()
    for student in students:
        await create_notification(
            session,
            title="Payment Reminder",
            body="Please submit your monthly tuition payment receipt.",
            user_id=student.id,
        )


async def send_upcoming_payment_reminders(session: AsyncSession, days_before: int = 3) -> None:
    today = datetime.utcnow().date()
    upcoming = today + timedelta(days=days_before)
    result = await session.execute(
        select(Payment).where(
            Payment.due_date >= today,
            Payment.due_date <= upcoming,
            Payment.status != PaymentStatus.PAID,
        )
    )
    for payment in result.scalars().all():
        title = "To‘lov muddati yaqin"
        body = f"{payment.month} oy uchun to‘lov muddati {payment.due_date} kuni."
        await create_notification(
            session,
            title=title,
            body=body,
            user_id=payment.student_id,
        )
        await send_telegram_messages_to_users(
            session,
            user_ids=[payment.student_id],
            title=title,
            body=body,
        )


async def send_debt_reminders(session: AsyncSession) -> None:
    result = await session.execute(
        select(Payment).where(Payment.status.in_([PaymentStatus.OVERDUE, PaymentStatus.PARTIAL, PaymentStatus.UNPAID]))
    )
    payments = result.scalars().all()
    for payment in payments:
        await create_notification(
            session,
            title="Payment Due",
            body=f"Your payment for {payment.month} is still due.",
            user_id=payment.student_id,
        )


async def send_homework_due_reminders(session: AsyncSession, hours_before: int) -> None:
    target = datetime.utcnow() + timedelta(hours=hours_before)
    result = await session.execute(
        select(HomeworkTask, Lesson.group_id)
        .join(Lesson, HomeworkTask.lesson_id == Lesson.id)
        .where(HomeworkTask.due_date != None, HomeworkTask.due_date <= target)
    )
    for task, group_id in result.all():
        submitted_result = await session.execute(
            select(HomeworkSubmission.student_id).where(HomeworkSubmission.homework_id == task.id)
        )
        submitted_ids = {row[0] for row in submitted_result.all()}

        enroll_result = await session.execute(
            select(StudentGroupEnrollment.student_id)
            .where(
                StudentGroupEnrollment.group_id == group_id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        for (student_id,) in enroll_result.all():
            if student_id not in submitted_ids:
                await create_notification(
                    session,
                    title="Homework Reminder",
                    body=f"Homework '{task.title}' is due soon.",
                    user_id=student_id,
                )


async def check_absence_threshold(session: AsyncSession) -> None:
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(AttendanceRecord.student_id, func.count(AttendanceRecord.id))
        .where(
            AttendanceRecord.created_at >= start_of_month,
            AttendanceRecord.status == AttendanceStatus.ABSENT,
        )
        .group_by(AttendanceRecord.student_id)
    )
    for student_id, count in result.all():
        if count >= 3:
            await create_notification(
                session,
                title="Absence Warning",
                body=f"Student {student_id} has {count} absences this month.",
                role_target=Role.SUPER_ADMIN.value,
            )
