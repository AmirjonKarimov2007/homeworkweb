from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from pathlib import Path
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role, HomeworkSubmissionStatus, EnrollmentStatus
from app.models.homework import HomeworkTask, HomeworkSubmission, HomeworkAttachment, SubmissionAttachment
from app.models.lesson import Lesson
from app.models.group import Group, StudentGroupEnrollment
from app.models.user import User
from app.core.config import settings
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkOut,
    SubmissionOut,
    SubmissionUpdate,
    HomeworkAttachmentOut,
)
from app.utils.pagination import paginate
from app.utils.responses import success
from app.utils.files import save_upload_file
from app.services.audit_service import log_action
from app.services.homework_service import submit_homework
from app.services.notification_service import create_notifications_bulk
from app.utils.enums import NotificationChannel

router = APIRouter(prefix="/homework", tags=["homework"])


def _submission_out(submission: HomeworkSubmission) -> SubmissionOut:
    data = submission.__dict__.copy()
    data.pop("attachments", None)
    return SubmissionOut(**data, attachments=submission.attachments)


def _safe_delete_file(path: str | None) -> None:
    if not path:
        return
    base = Path(settings.UPLOAD_DIR).resolve()
    file_path = Path(path).resolve()
    if str(file_path).startswith(str(base)) and file_path.exists():
        file_path.unlink(missing_ok=True)


@router.get("")
async def list_homework(
    group_id: int | None = None,
    lesson_id: int | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(HomeworkTask)
    if lesson_id:
        stmt = stmt.where(HomeworkTask.lesson_id == lesson_id)
    if group_id:
        stmt = stmt.join(Lesson, HomeworkTask.lesson_id == Lesson.id).where(Lesson.group_id == group_id)
    data = await paginate(session, stmt, page, size)
    return success({
        "items": [HomeworkOut(**h.__dict__) for h in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.post("")
async def create_homework(
    payload: HomeworkCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    if user.role == Role.TEACHER:
        lesson_result = await session.execute(select(Lesson).where(Lesson.id == payload.lesson_id))
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    existing_result = await session.execute(
        select(HomeworkTask).where(HomeworkTask.lesson_id == payload.lesson_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        session.add(existing)
        await session.commit()
        await session.refresh(existing)
        await log_action(session, user.id, "update_homework", "homework", existing.id)
        enroll_result = await session.execute(
            select(StudentGroupEnrollment.student_id).where(
                StudentGroupEnrollment.group_id == lesson.group_id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        student_ids = [row[0] for row in enroll_result.all()]
        await create_notifications_bulk(
            session,
            student_ids,
            title=f"Uyga vazifa yangilandi: {existing.title}",
            body=existing.instructions,
            channel=NotificationChannel.WEB,
        )
        return success(HomeworkOut(**existing.__dict__))

    homework = HomeworkTask(**payload.model_dump(), created_by=user.id)
    session.add(homework)
    await session.commit()
    await session.refresh(homework)
    await log_action(session, user.id, "create_homework", "homework", homework.id)
    enroll_result = await session.execute(
        select(StudentGroupEnrollment.student_id).where(
            StudentGroupEnrollment.group_id == lesson.group_id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    student_ids = [row[0] for row in enroll_result.all()]
    await create_notifications_bulk(
        session,
        student_ids,
        title=f"Yangi uyga vazifa: {homework.title}",
        body=homework.instructions,
        channel=NotificationChannel.WEB,
    )
    return success(HomeworkOut(**homework.__dict__))


@router.get("/{homework_id}")
async def get_homework(
    homework_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await session.execute(select(HomeworkTask).where(HomeworkTask.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    return success(HomeworkOut(**homework.__dict__))


@router.get("/{homework_id}/attachments")
async def list_homework_attachments(
    homework_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await session.execute(select(HomeworkAttachment).where(HomeworkAttachment.homework_id == homework_id))
    attachments = result.scalars().all()
    return success([HomeworkAttachmentOut(**a.__dict__) for a in attachments])


@router.post("/{homework_id}/attachments")
async def upload_homework_attachment(
    homework_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(HomeworkTask).where(HomeworkTask.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    if user.role == Role.TEACHER:
        lesson_result = await session.execute(select(Lesson).where(Lesson.id == homework.lesson_id))
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    path = await save_upload_file(file, "homework")
    attachment = HomeworkAttachment(
        homework_id=homework_id,
        file_path=path,
        file_name=file.filename or path.split("/")[-1],
    )
    session.add(attachment)
    await session.commit()
    await session.refresh(attachment)
    await log_action(session, user.id, "attach_homework_file", "homework", homework_id)
    return success(HomeworkAttachmentOut(**attachment.__dict__))


@router.delete("/submissions/{submission_id}/attachments/{attachment_id}")
async def delete_submission_attachment(
    submission_id: int,
    attachment_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await session.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.role == Role.STUDENT and submission.student_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if user.role == Role.TEACHER:
        hw_result = await session.execute(select(HomeworkTask).where(HomeworkTask.id == submission.homework_id))
        homework = hw_result.scalar_one_or_none()
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        lesson_result = await session.execute(select(Lesson).where(Lesson.id == homework.lesson_id))
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    att_result = await session.execute(
        select(SubmissionAttachment).where(
            SubmissionAttachment.id == attachment_id,
            SubmissionAttachment.submission_id == submission_id,
        )
    )
    attachment = att_result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    _safe_delete_file(attachment.file_path)
    await session.delete(attachment)
    await session.commit()
    await log_action(session, user.id, "delete_submission_attachment", "homework_submission", submission_id)
    return success({"deleted": True})


@router.get("/{homework_id}/submissions")
async def list_submissions(
    homework_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(
        select(HomeworkSubmission)
        .where(HomeworkSubmission.homework_id == homework_id)
        .options(selectinload(HomeworkSubmission.attachments))
    )
    submissions = result.scalars().all()
    return success([_submission_out(s) for s in submissions])


@router.get("/{homework_id}/my")
async def my_submission(
    homework_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can view")
    result = await session.execute(
        select(HomeworkSubmission)
        .where(
            HomeworkSubmission.homework_id == homework_id,
            HomeworkSubmission.student_id == user.id,
        )
        .options(selectinload(HomeworkSubmission.attachments))
    )
    submission = result.scalar_one_or_none()
    if not submission:
        return success({"status": HomeworkSubmissionStatus.NOT_SUBMITTED, "submission": None})
    return success({
        "status": submission.status,
        "submission": _submission_out(submission),
    })


@router.patch("/submissions/{submission_id}")
async def update_submission_status(
    submission_id: int,
    payload: SubmissionUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(HomeworkSubmission).where(HomeworkSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.role == Role.TEACHER:
        hw_result = await session.execute(select(HomeworkTask).where(HomeworkTask.id == submission.homework_id))
        homework = hw_result.scalar_one_or_none()
        if not homework:
            raise HTTPException(status_code=404, detail="Homework not found")
        lesson_result = await session.execute(select(Lesson).where(Lesson.id == homework.lesson_id))
        lesson = lesson_result.scalar_one_or_none()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        group_result = await session.execute(select(Group).where(Group.id == lesson.group_id))
        group = group_result.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    submission.status = payload.status
    submission.reviewed_by = user.id
    submission.reviewed_at = datetime.now(timezone.utc)
    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    await log_action(session, user.id, "review_homework", "homework_submission", submission.id)
    return success(SubmissionOut(**submission.__dict__))


@router.post("/{homework_id}/submit")
async def submit_homework_web(
    homework_id: int,
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can submit")
    if not text and not file:
        raise HTTPException(status_code=400, detail="Text or file required")

    result = await session.execute(select(HomeworkTask).where(HomeworkTask.id == homework_id))
    homework = result.scalar_one_or_none()
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")

    lesson_result = await session.execute(select(Lesson).where(Lesson.id == homework.lesson_id))
    lesson = lesson_result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    enrollment = await session.execute(
        select(StudentGroupEnrollment).where(
            StudentGroupEnrollment.student_id == user.id,
            StudentGroupEnrollment.group_id == lesson.group_id,
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    if not enrollment.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Student not in group")

    if homework.due_date:
        now_utc = datetime.now(timezone.utc)
        due = homework.due_date
        is_late = (due.tzinfo is None and datetime.utcnow() > due) or (due.tzinfo is not None and now_utc > due)
        if is_late and not homework.allow_late_submission:
            raise HTTPException(status_code=400, detail="Late submission not allowed")

    attachment_path = None
    if file:
        attachment_path = await save_upload_file(file, "homework")

    submission = await submit_homework(session, homework_id, user.id, text, attachment_path)
    # Determine late
    if homework.due_date:
        now_utc = datetime.now(timezone.utc)
        due = homework.due_date
        if (due.tzinfo is None and datetime.utcnow() > due) or (due.tzinfo is not None and now_utc > due):
            submission.status = HomeworkSubmissionStatus.LATE
            session.add(submission)
            await session.commit()

    refreshed = await session.execute(
        select(HomeworkSubmission)
        .where(HomeworkSubmission.id == submission.id)
        .options(selectinload(HomeworkSubmission.attachments))
    )
    submission = refreshed.scalar_one()

    await log_action(session, user.id, "submit_homework", "homework", homework_id)
    return success(_submission_out(submission))
