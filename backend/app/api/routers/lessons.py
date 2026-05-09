from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role, EnrollmentStatus
from app.models.lesson import Lesson, LessonAttachment
from app.models.group import Group, StudentGroupEnrollment
from app.models.payment import Payment
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonOut, LessonUpdate, LessonAttachmentOut
from app.utils.pagination import paginate
from app.utils.responses import success
from app.utils.files import save_upload_file
from app.services.audit_service import log_action
from app.services.payment_service import can_student_access_new_lessons

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("")
async def list_lessons(
    group_id: int | None = None,
    page: int = 1,
    size: int = 6,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Lesson)
    if group_id:
        stmt = stmt.where(Lesson.group_id == group_id)
        print(f"Filtering by group_id: {group_id}")

    # Admin and Super Admin can see all lessons
    if user.role in [Role.SUPER_ADMIN, Role.ADMIN]:
        print(f"Admin {user.id} can see all lessons")
        # No filtering needed for admin roles

    # Teacher can only see their own groups' lessons
    elif user.role == Role.TEACHER:
        if group_id is None:
            # Get all groups where teacher is primary teacher
            teacher_groups = await session.execute(
                select(Group.id).where(Group.primary_teacher_id == user.id)
            )
            group_ids = teacher_groups.scalars().all()
            print(f"Teacher {user.id} groups: {group_ids}")
            if not group_ids:
                return success({"items": [], "total": 0, "page": page, "size": size})
            stmt = stmt.where(Lesson.group_id.in_(group_ids))
        else:
            # Check if teacher is primary teacher of this specific group
            group_result = await session.execute(
                select(Group).where(Group.id == group_id)
            )
            group = group_result.scalar_one_or_none()
            if not group or group.primary_teacher_id != user.id:
                raise HTTPException(status_code=403, detail="Forbidden: You are not the primary teacher of this group")

    if user.role == Role.STUDENT:
        if group_id is None:
            stmt = stmt.join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Lesson.group_id).where(
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        else:
            enr = await session.execute(
                select(StudentGroupEnrollment).where(
                    StudentGroupEnrollment.group_id == group_id,
                    StudentGroupEnrollment.student_id == user.id,
                    StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
                )
            )
            if not enr.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Forbidden")

            can_access = await can_student_access_new_lessons(session, user.id, group_id)
            if not can_access:
                latest = await session.execute(
                    select(Payment)
                    .where(Payment.student_id == user.id, Payment.group_id == group_id)
                    .order_by(Payment.billing_year.desc(), Payment.billing_month.desc())
                    .limit(1)
                )
                invoice = latest.scalar_one_or_none()
                if invoice:
                    stmt = stmt.where(Lesson.date <= invoice.due_date)
    # Sort by created_at descending (newest first), then by date
    stmt = stmt.order_by(Lesson.created_at.desc(), Lesson.date.desc())
    print(f"Querying lessons with page={page}, size={size}, total lessons count will be calculated")
    data = await paginate(session, stmt, page, size)
    print(f"Pagination result: {data}")
    return success({
        "items": [LessonOut(**l.__dict__) for l in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.get("/student")
async def list_student_lessons(
    group_id: int | None = None,
    page: int = 1,
    size: int = 6,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can access this endpoint")

    stmt = select(Lesson)

    if group_id:
        enrollment = await session.execute(
            select(StudentGroupEnrollment).where(
                StudentGroupEnrollment.group_id == group_id,
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if not enrollment.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Student not enrolled in this group")
        stmt = stmt.where(Lesson.group_id == group_id)

        can_access = await can_student_access_new_lessons(session, user.id, group_id)
        if not can_access:
            latest = await session.execute(
                select(Payment)
                .where(Payment.student_id == user.id, Payment.group_id == group_id)
                .order_by(Payment.billing_year.desc(), Payment.billing_month.desc())
                .limit(1)
            )
            invoice = latest.scalar_one_or_none()
            if invoice:
                stmt = stmt.where(Lesson.date <= invoice.due_date)
    else:
        enrollment_stmt = select(StudentGroupEnrollment.group_id).where(
            StudentGroupEnrollment.student_id == user.id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
        )
        enrollments = await session.execute(enrollment_stmt)
        active_group_ids = enrollments.scalars().all()

        if not active_group_ids:
            return success({"items": [], "total": 0, "page": 1, "size": size})

        accessible_group_ids: list[int] = []
        restricted_due_dates: dict[int, object] = {}

        for enrolled_group_id in active_group_ids:
            can_access = await can_student_access_new_lessons(session, user.id, enrolled_group_id)
            if can_access:
                accessible_group_ids.append(enrolled_group_id)
                continue

            latest = await session.execute(
                select(Payment)
                .where(Payment.student_id == user.id, Payment.group_id == enrolled_group_id)
                .order_by(Payment.billing_year.desc(), Payment.billing_month.desc())
                .limit(1)
            )
            invoice = latest.scalar_one_or_none()
            if invoice:
                restricted_due_dates[enrolled_group_id] = invoice.due_date

        stmt = stmt.where(Lesson.group_id.in_(active_group_ids))

        if restricted_due_dates:
            from sqlalchemy import or_, and_

            restrictions = [
                and_(Lesson.group_id == restricted_group_id, Lesson.date <= due_date)
                for restricted_group_id, due_date in restricted_due_dates.items()
            ]

            if accessible_group_ids:
                restrictions.append(Lesson.group_id.in_(accessible_group_ids))

            stmt = stmt.where(or_(*restrictions))

    # Sort by created_at descending (newest first), then by date
    stmt = stmt.order_by(Lesson.created_at.desc(), Lesson.date.desc())
    data = await paginate(session, stmt, page, size)
    return success({
        "items": [LessonOut(**l.__dict__) for l in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.post("")
async def create_lesson(
    payload: LessonCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    if user.role == Role.TEACHER:
        result = await session.execute(select(Group).where(Group.id == payload.group_id))
        group = result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    lesson = Lesson(**payload.model_dump(), created_by=user.id)
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    await log_action(session, user.id, "create_lesson", "lesson", lesson.id)
    return success(LessonOut(**lesson.__dict__))


@router.get("/{lesson_id}")
async def get_lesson(
    lesson_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == Role.STUDENT:
        enr = await session.execute(
            select(StudentGroupEnrollment).where(
                StudentGroupEnrollment.group_id == lesson.group_id,
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if not enr.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Forbidden")
        can_access = await can_student_access_new_lessons(session, user.id, lesson.group_id)
        if not can_access:
            latest = await session.execute(
                select(Payment)
                .where(Payment.student_id == user.id, Payment.group_id == lesson.group_id)
                .order_by(Payment.billing_year.desc(), Payment.billing_month.desc())
                .limit(1)
            )
            invoice = latest.scalar_one_or_none()
            if invoice and lesson.date > invoice.due_date:
                raise HTTPException(status_code=403, detail="Payment overdue for new lessons")
    return success(LessonOut(**lesson.__dict__))


@router.patch("/{lesson_id}")
async def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, field, value)
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)
    await log_action(session, user.id, "update_lesson", "lesson", lesson.id)
    return success(LessonOut(**lesson.__dict__))


@router.delete("/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Check permissions for teachers
    if user.role == Role.TEACHER:
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden: You are not the primary teacher of this group")

    # Delete the lesson
    await session.delete(lesson)
    await session.commit()
    await log_action(session, user.id, "delete_lesson", "lesson", lesson_id)
    return success({"message": "Lesson deleted successfully"})


@router.get("/{lesson_id}/attachments")
async def list_lesson_attachments(
    lesson_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await session.execute(select(LessonAttachment).where(LessonAttachment.lesson_id == lesson_id))
    attachments = result.scalars().all()
    return success([LessonAttachmentOut(**a.__dict__) for a in attachments])


@router.post("/{lesson_id}/attachments")
async def upload_lesson_attachment(
    lesson_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == Role.TEACHER:
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    path = await save_upload_file(file, "lessons")
    attachment = LessonAttachment(
        lesson_id=lesson_id,
        file_path=path,
        file_name=file.filename or path.split("/")[-1],
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    await log_action(session, user.id, "attach_lesson_file", "lesson", lesson_id)
    return success(LessonAttachmentOut(**attachment.__dict__))
