from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.homework import HomeworkTask, HomeworkSubmission, SubmissionAttachment
from app.utils.enums import HomeworkSubmissionStatus


async def create_homework_task(
    session: AsyncSession,
    title: str,
    description: str,
    lesson_id: int | None,
    due_date: datetime,
    group_id: int | None = None,
    created_by: int | None = None,
) -> HomeworkTask:
    """Create a new homework task"""
    task = HomeworkTask(
        title=title,
        instructions=description,
        lesson_id=lesson_id,
        due_date=due_date,
        created_by=created_by or 1,  # Default to admin user if not provided
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def submit_homework(
    session: AsyncSession,
    homework_id: int,
    student_id: int,
    text: str | None,
    attachment_path: str | None,
) -> HomeworkSubmission:
    result = await session.execute(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id,
            HomeworkSubmission.student_id == student_id,
        )
    )
    submission = result.scalar_one_or_none()

    status = HomeworkSubmissionStatus.SUBMITTED
    if submission:
        submission.text = text
        submission.status = status
        submission.reviewed_by = None
        submission.reviewed_at = None
        submission.revision_count = (submission.revision_count or 0) + 1
        submission.submitted_at = datetime.now(timezone.utc)
    else:
        submission = HomeworkSubmission(
            homework_id=homework_id,
            student_id=student_id,
            status=status,
            text=text,
        )
        session.add(submission)
        await session.commit()
        await session.refresh(submission)

    if attachment_path:
        attachment = SubmissionAttachment(
            submission_id=submission.id,
            file_path=attachment_path,
            file_name=Path(attachment_path).name,
        )
        session.add(attachment)

    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    return submission
