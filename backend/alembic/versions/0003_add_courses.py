"""add_courses

Revision ID: 0003_add_courses
Revises: 0002_billing_module
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_add_courses"
down_revision = "0002_billing_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create courses table
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("monthly_fee", sa.Integer(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Add missing columns to groups table
    op.add_column("groups", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("groups", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column("groups", sa.Column("duration_months", sa.Integer(), nullable=True))

    # Add course_id to groups table (nullable first for existing groups)
    op.add_column("groups", sa.Column("course_id", sa.Integer(), nullable=True))

    # Create a default course for existing groups
    op.execute("""
        INSERT INTO courses (name, monthly_fee, duration_months, is_active)
        VALUES ('Default Course', 0, NULL, true)
        ON CONFLICT DO NOTHING
    """)

    # Set default course_id for existing groups
    op.execute("""
        UPDATE groups
        SET course_id = (SELECT id FROM courses WHERE name = 'Default Course' LIMIT 1)
        WHERE course_id IS NULL
    """)

    # Make course_id NOT NULL
    op.alter_column("groups", "course_id", nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_groups_course_id",
        "groups",
        "courses",
        ["course_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_groups_course_id", "groups", type_="foreignkey")
    op.drop_column("groups", "course_id")
    op.drop_column("groups", "duration_months")
    op.drop_column("groups", "end_date")
    op.drop_column("groups", "start_date")
    op.drop_table("courses")
