from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role, PaymentReceiptStatus, PaymentStatus, HomeworkSubmissionStatus
from app.models.user import User
from app.models.group import Group
from app.models.attendance import AttendanceRecord
from app.models.homework import HomeworkSubmission
from app.models.payment import Payment, PaymentReceipt
from app.schemas.report import DashboardSummary
from app.utils.responses import success

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
async def dashboard_summary(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    total_students = await session.scalar(select(func.count()).select_from(User).where(User.role == Role.STUDENT))
    active_groups = await session.scalar(select(func.count()).select_from(Group).where(Group.is_active == True))

    today = datetime.utcnow().date()
    today_attendance = await session.scalar(
        select(func.count()).select_from(AttendanceRecord).where(func.date(AttendanceRecord.created_at) == today)
    )

    pending_homework = await session.scalar(
        select(func.count()).select_from(HomeworkSubmission).where(HomeworkSubmission.status == HomeworkSubmissionStatus.SUBMITTED)
    )

    # Calculate total pending payments from invoices
    pending_payments_query = select(Payment).where(
        Payment.status.in_([PaymentStatus.OVERDUE, PaymentStatus.UNPAID, PaymentStatus.PARTIAL])
    )
    pending_payments_result = await session.execute(pending_payments_query)
    pending_payments = pending_payments_result.scalars().all()
    total_pending_amount = sum(max(p.amount_due - p.amount_paid, 0) for p in pending_payments)

    pending_receipts = await session.scalar(
        select(func.count()).select_from(PaymentReceipt).where(PaymentReceipt.status == PaymentReceiptStatus.PENDING_REVIEW)
    )

    start_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_income = await session.scalar(
        select(func.coalesce(func.sum(Payment.amount_paid), 0)).select_from(Payment).where(Payment.created_at >= start_month)
    )

    debtors_count = await session.scalar(
        select(func.count()).select_from(Payment).where(Payment.status == PaymentStatus.OVERDUE)
    )

    summary = DashboardSummary(
        total_students=total_students or 0,
        active_groups=active_groups or 0,
        today_attendance=today_attendance or 0,
        pending_homework=pending_homework or 0,
        pending_payments=total_pending_amount or 0,  # Use total amount instead of count
        pending_payments_count=pending_receipts or 0,  # Add count of pending receipts
        monthly_income=monthly_income or 0,
        debtors_count=debtors_count or 0,
        new_leads_this_month=0,
    )
    return success(summary.model_dump())
