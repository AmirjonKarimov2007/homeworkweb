"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from app.utils.enums import Role, LeadStatus, AttendanceStatus, HomeworkSubmissionStatus, PaymentStatus, PaymentReceiptStatus, MaterialType, NotificationChannel, NotificationStatus, EnrollmentStatus

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role", sa.Enum(Role), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("avatar_path", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("study_duration", sa.String(128), nullable=True),
        sa.Column("current_level", sa.String(128), nullable=True),
        sa.Column("goal_type", sa.String(128), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(128), nullable=True),
        sa.Column("status", sa.Enum(LeadStatus), default=LeadStatus.NEW),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("converted_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("converted_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("goal_type", sa.String(128), nullable=True),
        sa.Column("level_label", sa.String(128), nullable=True),
        sa.Column("schedule_time", sa.String(128), nullable=True),
        sa.Column("capacity", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("primary_teacher_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("curator_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("monthly_fee", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "group_teachers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id")),
        sa.Column("teacher_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "student_group_enrollments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id")),
        sa.Column("monthly_fee", sa.Integer, nullable=True),
        sa.Column("status", sa.Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("visible_to_students", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "lesson_attachments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id")),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id")),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("status", sa.Enum(AttendanceStatus), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("marked_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "homework_tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lesson_id", sa.Integer, sa.ForeignKey("lessons.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("allow_late_submission", sa.Boolean, default=True),
        sa.Column("max_revision_attempts", sa.Integer, default=2),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "homework_attachments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("homework_id", sa.Integer, sa.ForeignKey("homework_tasks.id")),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "homework_submissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("homework_id", sa.Integer, sa.ForeignKey("homework_tasks.id")),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("status", sa.Enum(HomeworkSubmissionStatus), default=HomeworkSubmissionStatus.SUBMITTED),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision_count", sa.Integer, default=0),
    )

    op.create_table(
        "submission_attachments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("submission_id", sa.Integer, sa.ForeignKey("homework_submissions.id")),
        sa.Column("file_path", sa.String(255), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id"), nullable=True),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("amount_due", sa.Integer, default=0),
        sa.Column("amount_paid", sa.Integer, default=0),
        sa.Column("status", sa.Enum(PaymentStatus), default=PaymentStatus.UNPAID),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "payment_receipts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("payment_id", sa.Integer, sa.ForeignKey("payments.id")),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("amount", sa.Integer, nullable=True),
        sa.Column("status", sa.Enum(PaymentReceiptStatus), default=PaymentReceiptStatus.PENDING_REVIEW),
        sa.Column("receipt_path", sa.String(255), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "materials",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.Enum(MaterialType), nullable=False),
        sa.Column("file_path", sa.String(255), nullable=True),
        sa.Column("link_url", sa.String(512), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("is_visible", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "material_group_links",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("material_id", sa.Integer, sa.ForeignKey("materials.id")),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("role_target", sa.String(32), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("channel", sa.Enum(NotificationChannel), default=NotificationChannel.TELEGRAM),
        sa.Column("status", sa.Enum(NotificationStatus), default=NotificationStatus.PENDING),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "telegram_links",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), unique=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, index=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(128), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("meta", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(128), unique=True),
        sa.Column("value", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("audit_logs")
    op.drop_table("telegram_links")
    op.drop_table("notifications")
    op.drop_table("material_group_links")
    op.drop_table("materials")
    op.drop_table("payment_receipts")
    op.drop_table("payments")
    op.drop_table("submission_attachments")
    op.drop_table("homework_submissions")
    op.drop_table("homework_attachments")
    op.drop_table("homework_tasks")
    op.drop_table("attendance_records")
    op.drop_table("lesson_attachments")
    op.drop_table("lessons")
    op.drop_table("student_group_enrollments")
    op.drop_table("group_teachers")
    op.drop_table("groups")
    op.drop_table("leads")
    op.drop_table("users")
