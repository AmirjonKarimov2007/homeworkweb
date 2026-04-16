from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, date
from app.utils.enums import PaymentStatus, PaymentReceiptStatus, PaymentMethod


class PaymentCreate(BaseModel):
    student_id: int
    group_id: int | None = None
    month: str
    amount_due: int


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    group_id: int | None
    month: str
    billing_year: int
    billing_month: int
    amount_due: int
    amount_paid: int
    remaining_amount: int
    status: PaymentStatus
    due_date: date
    created_at: datetime
    updated_at: datetime | None
    student_name: str | None = None
    group_name: str | None = None


class ReceiptCreate(BaseModel):
    payment_id: int
    amount: int | None = None
    note: str | None = None


class ReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    payment_id: int
    student_id: int
    amount: int | None
    status: PaymentReceiptStatus
    receipt_path: str
    note: str | None
    uploaded_at: datetime
    reviewed_by: int | None
    reviewed_at: datetime | None


class PaymentTransactionCreate(BaseModel):
    amount: int = Field(gt=0)
    payment_method: PaymentMethod
    note: str | None = None


class PaymentTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_id: int
    student_id: int
    group_id: int | None
    amount: int
    payment_method: PaymentMethod
    confirmed_by_admin_id: int | None
    note: str | None
    created_at: datetime
