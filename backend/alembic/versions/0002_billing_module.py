"""billing_module

Revision ID: 0002_billing_module
Revises: 0001_init
Create Date: 2026-04-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_billing_module"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # groups
    op.add_column("groups", sa.Column("payment_day", sa.Integer(), server_default="5", nullable=False))
    op.add_column("groups", sa.Column("grace_days", sa.Integer(), server_default="2", nullable=False))
    op.add_column("groups", sa.Column("is_payment_required", sa.Boolean(), server_default=sa.true(), nullable=False))

    # payments (invoices)
    op.add_column("payments", sa.Column("billing_year", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("billing_month", sa.Integer(), nullable=True))
    op.add_column("payments", sa.Column("due_date", sa.Date(), nullable=True))
    op.add_column("payments", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))

    # backfill year/month from existing month column
    op.execute("UPDATE payments SET billing_year = CAST(split_part(month, '-', 1) AS INTEGER) WHERE billing_year IS NULL")
    op.execute("UPDATE payments SET billing_month = CAST(split_part(month, '-', 2) AS INTEGER) WHERE billing_month IS NULL")
    # set default due_date to day 5 of billing month
    op.execute("UPDATE payments SET due_date = make_date(billing_year, billing_month, 5) WHERE due_date IS NULL")

    op.alter_column("payments", "billing_year", nullable=False)
    op.alter_column("payments", "billing_month", nullable=False)
    op.alter_column("payments", "due_date", nullable=False)

    op.create_unique_constraint(
        "uq_invoice_student_group_month",
        "payments",
        ["student_id", "group_id", "billing_year", "billing_month"],
    )

    # extend paymentstatus enum
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'OVERDUE'")

    # payment method enum + transactions
    payment_method_enum = sa.Enum("cash", "card", "transfer", name="paymentmethod")
    payment_method_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("confirmed_by_admin_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payment_transactions")
    op.drop_constraint("uq_invoice_student_group_month", "payments", type_="unique")
    op.drop_column("payments", "updated_at")
    op.drop_column("payments", "due_date")
    op.drop_column("payments", "billing_month")
    op.drop_column("payments", "billing_year")
    op.drop_column("groups", "is_payment_required")
    op.drop_column("groups", "grace_days")
    op.drop_column("groups", "payment_day")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
