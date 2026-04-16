from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, Field
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.models.notification import Notification
from app.models.user import User
from app.models.group import StudentGroupEnrollment, Group
from app.schemas.notification import NotificationOut
from app.services.notification_service import create_notifications_bulk, mark_sent
from app.utils.responses import success
from app.utils.enums import Role, NotificationStatus, NotificationChannel, EnrollmentStatus

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationSend(BaseModel):
    title: str
    body: str | None = None
    role: Role | None = None
    group_id: int | None = None
    user_ids: list[int] | None = Field(default_factory=list)


@router.get("")
async def list_notifications(
    status: NotificationStatus | None = None,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(
        or_(
            Notification.user_id == user.id,
            Notification.role_target == user.role,
        )
    )
    if status is not None:
        stmt = stmt.where(Notification.status == status)
    result = await session.execute(stmt.order_by(Notification.created_at.desc()))
    notifications = result.scalars().all()
    return success([NotificationOut(**n.__dict__) for n in notifications])


@router.post("/send")
async def send_notification(
    payload: NotificationSend,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    targets: list[int] = []

    if payload.role:
        result = await session.execute(select(User.id).where(User.role == payload.role, User.is_active == True))
        targets.extend([row[0] for row in result.all()])

    if payload.group_id:
        grp = await session.execute(select(Group).where(Group.id == payload.group_id))
        if not grp.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Group not found")
        enroll = await session.execute(
            select(StudentGroupEnrollment.student_id).where(
                StudentGroupEnrollment.group_id == payload.group_id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        targets.extend([row[0] for row in enroll.all()])

    if payload.user_ids:
        targets.extend(payload.user_ids)

    targets = list(dict.fromkeys(targets))
    if not targets:
        raise HTTPException(status_code=400, detail="No targets")

    created = await create_notifications_bulk(
        session,
        targets,
        payload.title,
        payload.body,
        channel=NotificationChannel.WEB,
    )
    # Save a copy for sender so admin can see history
    admin_copy = Notification(
        user_id=user.id,
        title=payload.title,
        body=payload.body,
        channel=NotificationChannel.WEB,
        status=NotificationStatus.SENT,
    )
    session.add(admin_copy)
    await session.commit()
    return success({"sent": created})


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    if note.user_id and note.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if note.role_target and note.role_target != user.role:
        raise HTTPException(status_code=403, detail="Forbidden")
    await mark_sent(session, note)
    return success({"read": True})
