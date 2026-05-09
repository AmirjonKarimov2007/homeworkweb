from sqlalchemy import String, Integer, DateTime, Date, func, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.utils.enums import PaymentStatus, PaymentReceiptStatus, PaymentMethod


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("student_id", "group_id", "billing_year", "billing_month", name="uq_invoice_student_group_month"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    month: Mapped[str] = mapped_column(String(7))  # YYYY-MM
    billing_year: Mapped[int] = mapped_column(Integer)
    billing_month: Mapped[int] = mapped_column(Integer)
    amount_due: Mapped[int] = mapped_column(Integer, default=0)
    amount_paid: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    due_date: Mapped[Date] = mapped_column(Date)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    receipts = relationship("PaymentReceipt", back_populates="payment")
    transactions = relationship("PaymentTransaction", back_populates="invoice")


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[PaymentReceiptStatus] = mapped_column(Enum(PaymentReceiptStatus), default=PaymentReceiptStatus.PENDING_REVIEW)
    receipt_path: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payment = relationship("Payment", back_populates="receipts")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    confirmed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Payment", back_populates="transactions")
