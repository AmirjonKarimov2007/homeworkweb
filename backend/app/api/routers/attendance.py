from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.attendance import AttendanceRecord
from app.models.group import Group
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceOut
from app.utils.responses import success
from app.services.audit_service import log_action

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("")
async def list_attendance(
    lesson_id: int | None = None,
    student_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    stmt = select(AttendanceRecord)
    if lesson_id:
        stmt = stmt.where(AttendanceRecord.lesson_id == lesson_id)
    if student_id:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)
    result = await session.execute(stmt)
    records = result.scalars().all()
    return success([AttendanceOut(**r.__dict__) for r in records])


@router.post("")
async def mark_attendance(
    payload: AttendanceCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    # Verify teacher owns lesson group if teacher
    if user.role == Role.TEACHER:
        lesson_result = await session.execute(select(Lesson).where(Lesson.id == payload.lesson_id))
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    record = AttendanceRecord(
        lesson_id=payload.lesson_id,
        student_id=payload.student_id,
        status=payload.status,
        note=payload.note,
        marked_by=user.id,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    await log_action(session, user.id, "mark_attendance", "attendance", record.id)
    return success(AttendanceOut(**record.__dict__))
