from app.db.session import engine
from app.db.base import Base
from app import models  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.exec_driver_sql(
            "ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'PENDING'"
        )
        await conn.exec_driver_sql(
            "ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'OVERDUE'"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'YANGI'"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS start_date DATE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS end_date DATE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS duration_months INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS payment_day INTEGER DEFAULT 5"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS grace_days INTEGER DEFAULT 2"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ALTER COLUMN grace_days SET DEFAULT 0"
        )
        await conn.exec_driver_sql(
            "UPDATE groups SET grace_days = 0 WHERE grace_days IS NULL OR grace_days <> 0"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE groups ADD COLUMN IF NOT EXISTS is_payment_required BOOLEAN DEFAULT TRUE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS billing_year INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS billing_month INTEGER"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS due_date DATE"
        )
        await conn.exec_driver_sql(
            "ALTER TABLE payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
        )
        await conn.exec_driver_sql(
            "UPDATE payments SET billing_year = CAST(split_part(month, '-', 1) AS INTEGER) WHERE billing_year IS NULL AND month IS NOT NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE payments SET billing_month = CAST(split_part(month, '-', 2) AS INTEGER) WHERE billing_month IS NULL AND month IS NOT NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE payments SET due_date = make_date(billing_year, billing_month, 1) WHERE due_date IS NULL AND billing_year IS NOT NULL AND billing_month IS NOT NULL"
        )
        await conn.exec_driver_sql(
            "UPDATE payments SET updated_at = created_at WHERE updated_at IS NULL"
        )
