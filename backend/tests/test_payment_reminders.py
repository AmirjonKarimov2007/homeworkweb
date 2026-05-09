import pytest
from datetime import datetime, timedelta

from app.db.session import engine
from app.db.session import AsyncSessionLocal
from app.models import Base
from app.models.payment import Payment
from app.models.user import User
from app.tasks import jobs
from app.utils.enums import PaymentStatus, Role


@pytest.mark.asyncio
async def test_send_upcoming_payment_reminders_sends_web_and_telegram(monkeypatch):
    calls: dict[str, list] = {"notifications": [], "telegram": []}

    async def fake_create_notification(session, title, body=None, user_id=None, role_target=None, channel=None):
        calls["notifications"].append(
            {
                "title": title,
                "body": body,
                "user_id": user_id,
            }
        )
        return None

    async def fake_send_telegram_messages_to_users(session, user_ids, title, body=None):
        calls["telegram"].append(
            {
                "user_ids": user_ids,
                "title": title,
                "body": body,
            }
        )
        return {"target_count": len(user_ids), "sent_count": len(user_ids)}

    monkeypatch.setattr(jobs, "create_notification", fake_create_notification)
    monkeypatch.setattr(jobs, "send_telegram_messages_to_users", fake_send_telegram_messages_to_users)

    due_date = datetime.utcnow().date() + timedelta(days=2)
    not_upcoming_due_date = datetime.utcnow().date() + timedelta(days=10)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with AsyncSessionLocal() as session:
            student = User(
                full_name="Reminder Student",
                phone="+10000000123",
                email="reminder-student@example.com",
                role=Role.STUDENT,
                hashed_password="hashed",
                is_active=True,
            )
            session.add(student)
            await session.commit()
            await session.refresh(student)

            upcoming_payment = Payment(
                student_id=student.id,
                group_id=None,
                month=f"{due_date.year:04d}-{due_date.month:02d}",
                billing_year=due_date.year,
                billing_month=due_date.month,
                amount_due=500000,
                amount_paid=0,
                status=PaymentStatus.UNPAID,
                due_date=due_date,
            )
            far_payment = Payment(
                student_id=student.id,
                group_id=None,
                month=f"{not_upcoming_due_date.year:04d}-{not_upcoming_due_date.month:02d}",
                billing_year=not_upcoming_due_date.year,
                billing_month=not_upcoming_due_date.month,
                amount_due=500000,
                amount_paid=0,
                status=PaymentStatus.UNPAID,
                due_date=not_upcoming_due_date,
            )
            session.add(upcoming_payment)
            session.add(far_payment)
            await session.commit()

            await jobs.send_upcoming_payment_reminders(session, days_before=3)
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    assert len(calls["notifications"]) == 1
    assert calls["notifications"][0]["user_id"] is not None
    assert "To‘lov muddati yaqin" in calls["notifications"][0]["title"]

    assert len(calls["telegram"]) == 1
    assert len(calls["telegram"][0]["user_ids"]) == 1
    assert "To‘lov muddati yaqin" in calls["telegram"][0]["title"]
