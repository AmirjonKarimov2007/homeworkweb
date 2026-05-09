from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date
import asyncio
import json
import urllib.request
import urllib.error
import logging
from app.core.deps import get_db, verify_bot_token
from app.core.config import settings
from app.models.telegram import TelegramLink
from app.models.user import User
from app.models.group import StudentGroupEnrollment, Group
from app.models.lesson import Lesson
from app.models.homework import HomeworkTask, HomeworkSubmission
from app.models.payment import Payment, PaymentReceipt
from app.models.material import Material, MaterialGroupLink
from app.models.notification import Notification
from app.models.homework import HomeworkSubmissionStatus
from app.models.payment import Payment, PaymentReceiptStatus
from app.utils.enums import Role, NotificationStatus, EnrollmentStatus, NotificationChannel
from app.utils.responses import success
from app.utils.files import save_upload_file
from app.services.payment_service import ensure_invoice, create_receipt
from app.services.homework_service import submit_homework, create_homework_task
from app.services.notification_service import mark_sent, create_notifications_bulk

router = APIRouter(prefix="/bot", tags=["bot"], dependencies=[Depends(verify_bot_token)])
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class LinkTelegramRequest(BaseModel):
    telegram_id: int
    phone: str
    username: Optional[str] = None


class SendNotificationRequest(BaseModel):
    sent_by: int  # Telegram ID who sends
    target_type: str = Field(..., description="all | group | user")
    target_id: Optional[int] = None  # group_id or user_id
    title: str
    body: str
    notification_type: str = "announcement"  # announcement, homework, payment, lesson


class CreateHomeworkRequest(BaseModel):
    sent_by: int  # Telegram ID who creates
    title: str
    description: str
    due_date: str  # ISO format date-time
    group_id: int
    lesson_id: Optional[int] = None


class StatsResponse(BaseModel):
    today_homework_submitted: int
    today_homework_not_submitted: int
    today_payment_received: int  # amount in sum
    total_students: int


# ==================== HELPER FUNCTIONS ====================

async def _get_user_by_telegram(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .join(TelegramLink, TelegramLink.user_id == User.id)
        .where(TelegramLink.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def _get_telegram_ids_by_group(session: AsyncSession, group_id: int) -> List[int]:
    """Get telegram IDs of students in a group (active enrollment only)"""
    result = await session.execute(
        select(TelegramLink.telegram_id)
        .join(User, TelegramLink.user_id == User.id)
        .join(StudentGroupEnrollment, StudentGroupEnrollment.student_id == User.id)
        .where(
            StudentGroupEnrollment.group_id == group_id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE
        )
    )
    return [row[0] for row in result.all()]


async def _get_all_telegram_ids(session: AsyncSession, role: Optional[Role] = None) -> List[int]:
    """Get all telegram IDs (optionally filtered by role)"""
    query = select(TelegramLink.telegram_id).join(User, TelegramLink.user_id == User.id)
    if role:
        query = query.where(User.role == role)
    result = await session.execute(query)
    return [row[0] for row in result.all()]


async def _send_telegram_message(chat_id: int, text: str) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("Telegram bot token is missing in backend settings")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url=url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _post() -> bool:
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return 200 <= response.status < 300
        except urllib.error.URLError:
            return False

    return await asyncio.to_thread(_post)


# ==================== LINK & AUTH ====================

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +998XXXXXXXXX format"""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    # Remove leading +
    if phone.startswith("+"):
        phone = phone[1:]
    # Remove leading 998 if followed by 998 (double prefix)
    if phone.startswith("998998"):
        phone = phone[3:]
    # Add +998 prefix if needed
    if not phone.startswith("998"):
        if phone.startswith("9") and len(phone) == 9:
            phone = "998" + phone
        else:
            # Invalid format, return as is
            return "+" + phone
    return "+" + phone


@router.post("/link")
async def link_telegram(
    telegram_id: int = Form(...),
    phone: str = Form(...),
    username: str | None = Form(default=None),
    session: AsyncSession = Depends(get_db),
):
    # Normalize phone number
    normalized_phone = normalize_phone(phone)

    # Try to find user by phone (try multiple formats)
    # Try with +998 prefix
    result = await session.execute(select(User).where(User.phone == normalized_phone))
    user = result.scalar_one_or_none()

    # Try without + prefix
    if not user and normalized_phone.startswith("+"):
        result = await session.execute(select(User).where(User.phone == normalized_phone[1:]))
        user = result.scalar_one_or_none()

    # Try with spaces (format: +998 90 123 45 67)
    if not user and len(normalized_phone) >= 12:
        try:
            spaced_phone = f"{normalized_phone[:4]} {normalized_phone[4:6]} {normalized_phone[6:8]} {normalized_phone[8:10]} {normalized_phone[10:]}"
            result = await session.execute(select(User).where(User.phone == spaced_phone))
            user = result.scalar_one_or_none()
        except Exception:
            pass

    # Try format with 2-digit groups: +998 90 123 45 67
    if not user and len(normalized_phone) >= 12:
        try:
            spaced_phone2 = f"{normalized_phone[:4]} {normalized_phone[4:6]} {normalized_phone[6:9]} {normalized_phone[9:11]} {normalized_phone[11:]}"
            result = await session.execute(select(User).where(User.phone == spaced_phone2))
            user = result.scalar_one_or_none()
        except Exception:
            pass

    # Debug log
    import logging
    logger = logging.getLogger(__name__)
    if not user:
        logger.warning(f"User not found with phone: {phone} (normalized: {normalized_phone})")

    if not user:
        raise HTTPException(status_code=404, detail="User not found with this phone number")

    # Check if user has any active enrollment (for students)
    if user.role == Role.STUDENT:
        enroll_result = await session.execute(
            select(StudentGroupEnrollment).where(
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE
            )
        )
        enrollment = enroll_result.scalar_one_or_none()
        if not enrollment:
            raise HTTPException(status_code=400, detail="User is not enrolled in any active group")

    # Check or create telegram link
    existing = await session.execute(select(TelegramLink).where(TelegramLink.user_id == user.id))
    link = existing.scalar_one_or_none()
    if link:
        link.telegram_id = telegram_id
        link.username = username
    else:
        link = TelegramLink(user_id=user.id, telegram_id=telegram_id, username=username)
        session.add(link)
    await session.commit()

    # Get user's groups if student
    groups = []
    if user.role == Role.STUDENT:
        enroll = await session.execute(
            select(Group)
            .join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Group.id)
            .where(StudentGroupEnrollment.student_id == user.id)
        )
        groups = [{"id": g.id, "name": g.name} for g in enroll.scalars().all()]

    return success({
        "linked": True,
        "user_id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "groups": groups
    })


@router.get("/me")
async def bot_me(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")
    return success({
        "id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone
    })


@router.get("/webapp-data")
async def bot_webapp_data(telegram_id: int, session: AsyncSession = Depends(get_db)):
    """Get user data for webapp"""
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    groups = []
    if user.role == Role.STUDENT:
        enroll = await session.execute(
            select(Group)
            .join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Group.id)
            .where(StudentGroupEnrollment.student_id == user.id)
        )
        groups = [{"id": g.id, "name": g.name} for g in enroll.scalars().all()]
    elif user.role in [Role.ADMIN, Role.SUPER_ADMIN, Role.TEACHER]:
        # Admins/teachers see all groups
        groups_result = await session.execute(select(Group))
        groups = [{"id": g.id, "name": g.name} for g in groups_result.scalars().all()]

    return success({
        "id": user.id,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "groups": groups,
        "is_admin": user.role in [Role.ADMIN, Role.SUPER_ADMIN, Role.TEACHER]
    })


# ==================== GROUPS ====================

@router.get("/groups")
async def bot_groups(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    if user.role == Role.STUDENT:
        enroll = await session.execute(
            select(Group)
            .join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Group.id)
            .where(StudentGroupEnrollment.student_id == user.id)
        )
        groups = enroll.scalars().all()
    else:
        # Admins/teachers see all groups
        groups_result = await session.execute(select(Group))
        groups = groups_result.scalars().all()

    return success([
        {"id": g.id, "name": g.name, "schedule_time": g.schedule_time}
        for g in groups
    ])


@router.get("/groups-for-admin")
async def bot_groups_for_admin(session: AsyncSession = Depends(get_db)):
    """Get all groups for admin to select"""
    result = await session.execute(
        select(Group).order_by(Group.name)
    )
    groups = result.scalars().all()
    return success([
        {
            "id": g.id,
            "name": g.name,
            "schedule_time": g.schedule_time,
            "student_count": g.student_count if hasattr(g, 'student_count') else 0
        }
        for g in groups
    ])


@router.get("/users-by-group")
async def bot_users_by_group(
    group_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Get students in a group with their telegram IDs"""
    result = await session.execute(
        select(User, TelegramLink.telegram_id)
        .join(StudentGroupEnrollment, StudentGroupEnrollment.student_id == User.id)
        .outerjoin(TelegramLink, TelegramLink.user_id == User.id)
        .where(
            StudentGroupEnrollment.group_id == group_id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE
        )
    )
    users = []
    for user, tg_id in result.all():
        users.append({
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "telegram_id": tg_id,
            "has_telegram": tg_id is not None
        })
    return success(users)


# ==================== HOMEWORK ====================

@router.get("/homework")
async def bot_homework(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    enroll = await session.execute(
        select(StudentGroupEnrollment.group_id).where(StudentGroupEnrollment.student_id == user.id)
    )
    group_ids = [row[0] for row in enroll.all()]
    if not group_ids:
        return success([])

    result = await session.execute(
        select(HomeworkTask, Lesson)
        .join(Lesson, HomeworkTask.lesson_id == Lesson.id)
        .where(Lesson.group_id.in_(group_ids))
        .order_by(HomeworkTask.due_date.desc())
    )
    items = []
    for task, lesson in result.all():
        items.append({
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date,
            "lesson_title": lesson.title,
            "group_id": lesson.group_id,
        })
    return success(items)


@router.post("/homework/create")
async def bot_create_homework(
    data: CreateHomeworkRequest,
    session: AsyncSession = Depends(get_db),
):
    """Admin creates homework via bot/webapp"""
    # Verify user is admin/teacher
    user = await _get_user_by_telegram(session, data.sent_by)
    if not user or user.role not in [Role.ADMIN, Role.SUPER_ADMIN, Role.TEACHER]:
        raise HTTPException(status_code=403, detail="Only admins and teachers can create homework")

    try:
        due_date = datetime.fromisoformat(data.due_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid due_date format")

    # Create homework task
    task = await create_homework_task(
        session,
        title=data.title,
        description=data.description,
        lesson_id=data.lesson_id,
        due_date=due_date,
        group_id=data.group_id
    )

    enroll_result = await session.execute(
        select(StudentGroupEnrollment.student_id).where(
            StudentGroupEnrollment.group_id == data.group_id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    student_ids = [row[0] for row in enroll_result.all()]
    title = f"Yangi uyga vazifa: {task.title}"
    body = task.instructions or "Sizga yangi uyga vazifa berildi."
    await create_notifications_bulk(
        session,
        student_ids,
        title=title,
        body=body,
        channel=NotificationChannel.WEB,
    )
    await create_notifications_bulk(
        session,
        student_ids,
        title=title,
        body=body,
        channel=NotificationChannel.TELEGRAM,
    )

    tg_result = await session.execute(
        select(TelegramLink.telegram_id).where(
            TelegramLink.user_id.in_(student_ids),
            TelegramLink.telegram_id.is_not(None),
        )
    )
    telegram_ids = [row[0] for row in tg_result.all()]

    message_text = (
        f"📚 Sizda yangi homework bor!\n\n"
        f"📝 {task.title}\n"
        f"⏰ Deadline: {task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else '-'}"
    )
    sent_count = 0
    for telegram_id in telegram_ids:
        if await _send_telegram_message(telegram_id, message_text):
            sent_count += 1

    return success({
        "id": task.id,
        "title": task.title,
        "due_date": task.due_date,
        "telegram_target_count": len(telegram_ids),
        "telegram_sent_count": sent_count,
    })


@router.post("/homework/{homework_id}/submit")
async def bot_submit_homework(
    homework_id: int,
    telegram_id: int = Form(...),
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_db),
):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    attachment_path = None
    if file:
        attachment_path = await save_upload_file(file, "homework")

    submission = await submit_homework(session, homework_id, user.id, text, attachment_path)
    return success({"submission_id": submission.id})


# ==================== PAYMENTS ====================

@router.get("/payments")
async def bot_payments(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")
    result = await session.execute(select(Payment).where(Payment.student_id == user.id))
    payments = result.scalars().all()
    return success([
        {
            "id": p.id,
            "month": p.month,
            "amount_due": p.amount_due,
            "amount_paid": p.amount_paid,
            "status": p.status,
        }
        for p in payments
    ])


@router.post("/payments/receipt")
async def bot_upload_receipt(
    telegram_id: int = Form(...),
    payment_id: int | None = Form(default=None),
    amount: int | None = Form(default=None),
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    if payment_id:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
    else:
        enroll = await session.execute(
            select(StudentGroupEnrollment, Group)
            .join(Group, StudentGroupEnrollment.group_id == Group.id)
            .where(StudentGroupEnrollment.student_id == user.id, StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE)
        )
        row = enroll.first()
        if not row:
            raise HTTPException(status_code=404, detail="No active group for student")
        enrollment, group = row
        payment = await ensure_invoice(session, user.id, group)

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    path = await save_upload_file(file, "payments")
    receipt = await create_receipt(session, payment, user.id, amount, path, note)
    return success({"receipt_id": receipt.id})


# ==================== MATERIALS ====================

@router.get("/materials")
async def bot_materials(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")

    enroll = await session.execute(
        select(StudentGroupEnrollment.group_id).where(StudentGroupEnrollment.student_id == user.id)
    )
    group_ids = [row[0] for row in enroll.all()]
    if not group_ids:
        return success([])

    result = await session.execute(
        select(Material)
        .join(MaterialGroupLink, MaterialGroupLink.material_id == Material.id)
        .where(MaterialGroupLink.group_id.in_(group_ids))
    )
    materials = result.scalars().all()
    return success([
        {
            "id": m.id,
            "title": m.title,
            "type": m.type,
            "file_path": m.file_path,
            "link_url": m.link_url,
        }
        for m in materials
    ])


# ==================== NOTIFICATIONS ====================

@router.get("/notifications")
async def bot_notifications(telegram_id: int, session: AsyncSession = Depends(get_db)):
    user = await _get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not linked")
    result = await session.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.status == NotificationStatus.PENDING)
    )
    notes = result.scalars().all()
    return success([
        {"id": n.id, "title": n.title, "body": n.body}
        for n in notes
    ])


@router.get("/admin-notifications")
async def bot_admin_notifications(session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(Notification).where(
            Notification.status == NotificationStatus.PENDING,
            Notification.role_target.in_([Role.ADMIN.value, Role.SUPER_ADMIN.value])
        )
    )
    notes = result.scalars().all()
    return success([
        {"id": n.id, "title": n.title, "body": n.body, "user_id": n.user_id}
        for n in notes
    ])


@router.post("/notifications/{notification_id}/sent")
async def bot_mark_sent(notification_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    await mark_sent(session, note)
    return success({"sent": True})


@router.post("/send-notification")
async def bot_send_notification(
    data: SendNotificationRequest,
    session: AsyncSession = Depends(get_db),
):
    """Admin sends notification to users"""
    # Verify sender is admin
    sender = await _get_user_by_telegram(session, data.sent_by)
    if not sender or sender.role not in [Role.ADMIN, Role.SUPER_ADMIN, Role.TEACHER]:
        raise HTTPException(status_code=403, detail="Only admins and teachers can send notifications")

    # Get target telegram IDs
    telegram_ids = []
    if data.target_type == "all":
        telegram_ids = await _get_all_telegram_ids(session)
    elif data.target_type == "group":
        if not data.target_id:
            raise HTTPException(status_code=400, detail="group_id required for group target")
        telegram_ids = await _get_telegram_ids_by_group(session, data.target_id)
    elif data.target_type == "user":
        if not data.target_id:
            raise HTTPException(status_code=400, detail="user_id required for user target")
        result = await session.execute(
            select(TelegramLink.telegram_id).where(TelegramLink.user_id == data.target_id)
        )
        row = result.first()
        if row:
            telegram_ids = [row[0]]

    # Note: This endpoint returns the telegram IDs that should receive the notification.
    # The bot will handle the actual sending using these IDs.
    return success({
        "success": True,
        "telegram_ids": telegram_ids,
        "count": len(telegram_ids)
    })


# ==================== STATISTICS ====================

@router.get("/stats")
async def bot_stats(session: AsyncSession = Depends(get_db)):
    """Get today's statistics for admin"""
    today = date.today()

    # Today's homework submissions
    submitted_today = await session.execute(
        select(func.count(HomeworkSubmission.id))
        .where(HomeworkSubmission.created_at >= today)
        .where(HomeworkSubmission.status == HomeworkSubmissionStatus.SUBMITTED)
    )
    today_homework_submitted = submitted_today.scalar() or 0

    # Students who haven't submitted today (active students)
    active_students_result = await session.execute(
        select(func.count(func.distinct(StudentGroupEnrollment.student_id)))
        .where(StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE)
    )
    total_active_students = active_students_result.scalar() or 0

    students_submitted_today = await session.execute(
        select(func.count(func.distinct(HomeworkSubmission.student_id)))
        .where(HomeworkSubmission.created_at >= today)
        .where(HomeworkSubmission.status == HomeworkSubmissionStatus.SUBMITTED)
    )
    students_submitted_today_count = students_submitted_today.scalar() or 0

    today_homework_not_submitted = max(0, total_active_students - students_submitted_today_count)

    # Today's payments received
    today_payments = await session.execute(
        select(func.sum(PaymentReceipt.amount))
        .join(Payment, PaymentReceipt.payment_id == Payment.id)
        .where(PaymentReceipt.created_at >= today)
    )
    today_payment_received = today_payments.scalar() or 0

    # Total students
    total_students = await session.execute(
        select(func.count(User.id)).where(User.role == Role.STUDENT)
    )
    total_students_count = total_students.scalar() or 0

    return success({
        "today_homework_submitted": today_homework_submitted,
        "today_homework_not_submitted": today_homework_not_submitted,
        "today_payment_received": today_payment_received,
        "total_students": total_students_count
    })
