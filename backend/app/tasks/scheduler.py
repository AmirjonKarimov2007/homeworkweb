import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.tasks.jobs import (
    create_monthly_payments,
    send_payment_reminders,
    send_upcoming_payment_reminders,
    send_debt_reminders,
    send_homework_due_reminders,
    check_absence_threshold,
)


async def _run_with_session(job_func, *args):
    async with AsyncSessionLocal() as session:
        await job_func(session, *args)


def _schedule_async(scheduler: AsyncIOScheduler, job_func, trigger: str, *args, **kwargs):
    scheduler.add_job(_run_with_session, trigger, args=[job_func, *args], **kwargs)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)

    # Monthly auto-create payments and reminders
    _schedule_async(scheduler, create_monthly_payments, "cron", day=1, hour=8, minute=0)
    _schedule_async(scheduler, send_payment_reminders, "cron", day=1, hour=9, minute=0)
    _schedule_async(scheduler, send_upcoming_payment_reminders, "cron", hour=9, minute=30)
    _schedule_async(scheduler, send_debt_reminders, "cron", day=5, hour=9, minute=0)

    # Daily homework reminders (24h and 3h)
    if settings.REMINDER_24H_ENABLED:
        scheduler.add_job(_run_with_session, "cron", hour=8, args=[send_homework_due_reminders, 24])
    if settings.REMINDER_3H_ENABLED:
        scheduler.add_job(_run_with_session, "cron", hour=12, args=[send_homework_due_reminders, 3])

    # Daily absence check
    _schedule_async(scheduler, check_absence_threshold, "cron", hour=18)

    scheduler.start()
    return scheduler
