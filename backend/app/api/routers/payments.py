from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sqlalchemy as sa
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role, PaymentStatus
from app.models.payment import Payment, PaymentReceipt, PaymentTransaction
from app.models.user import User
from app.models.group import Group
from app.schemas.payment import PaymentCreate, PaymentOut, ReceiptOut, PaymentTransactionCreate, PaymentTransactionOut
from app.utils.pagination import paginate
from app.utils.responses import success
from app.utils.files import save_upload_file
from app.services.payment_service import (
    ensure_invoice,
    create_receipt,
    confirm_receipt,
    reject_receipt,
    generate_monthly_payments,
    ensure_student_monthly_payments,
    create_payment_transaction,
    refresh_invoice_status,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/payments", tags=["payments"])


def _to_payment_out(payment: Payment, student_name: str | None = None, group_name: str | None = None) -> PaymentOut:
    remaining = max(payment.amount_due - payment.amount_paid, 0)
    updated_at = payment.updated_at or payment.created_at
    billing_year = payment.billing_year
    billing_month = payment.billing_month
    due_date = payment.due_date
    if (billing_year is None or billing_month is None) and payment.month:
        try:
            y, m = map(int, payment.month.split("-"))
            billing_year = billing_year or y
            billing_month = billing_month or m
        except Exception:
            pass
    if due_date is None and billing_year and billing_month:
        due_date = datetime(billing_year, billing_month, 1).date()
    return PaymentOut(
        id=payment.id,
        student_id=payment.student_id,
        group_id=payment.group_id,
        month=payment.month,
        billing_year=billing_year or datetime.utcnow().year,
        billing_month=billing_month or datetime.utcnow().month,
        amount_due=payment.amount_due,
        amount_paid=payment.amount_paid,
        remaining_amount=remaining,
        status=payment.status,
        due_date=due_date or datetime.utcnow().date(),
        created_at=payment.created_at,
        updated_at=updated_at,
        student_name=student_name,
        group_name=group_name,
    )


@router.get("")
async def list_payments(
    student_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(Payment, User.full_name, Group.name)
    stmt = stmt.join(User, Payment.student_id == User.id)
    stmt = stmt.outerjoin(Group, Payment.group_id == Group.id)
    if student_id:
        stmt = stmt.where(Payment.student_id == student_id)
    if status:
        if status == PaymentStatus.OVERDUE or status == "OVERDUE":
            stmt = stmt.where(Payment.status.in_([PaymentStatus.OVERDUE, PaymentStatus.UNPAID, PaymentStatus.PENDING]))
        else:
            stmt = stmt.where(Payment.status == status)
    total = await session.scalar(select(sa.func.count()).select_from(stmt.subquery()))
    result = await session.execute(stmt.limit(size).offset((page - 1) * size))
    rows = result.all()
    items = []
    for payment, student_name, group_name in rows:
        await refresh_invoice_status(session, payment)
        items.append(_to_payment_out(payment, student_name, group_name))

    return success({
        "items": items,
        "total": total or 0,
        "page": page,
        "size": size,
    })


@router.get("/receipts")
async def list_receipts(
    status: str | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(PaymentReceipt)
    if status:
        stmt = stmt.where(PaymentReceipt.status == status)
    data = await paginate(session, stmt, page, size)
    return success({
        "items": [ReceiptOut(**r.__dict__) for r in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.get("/transactions")
async def list_transactions(
    invoice_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(PaymentTransaction)
    if invoice_id:
        stmt = stmt.where(PaymentTransaction.invoice_id == invoice_id)
    result = await session.execute(stmt)
    items = result.scalars().all()
    return success([PaymentTransactionOut(**t.__dict__) for t in items])


@router.get("/mine")
async def my_payments(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Forbidden")
    await ensure_student_monthly_payments(session, user.id)
    result = await session.execute(select(Payment).where(Payment.student_id == user.id))
    payments = result.scalars().all()
    items = []
    for p in payments:
        await refresh_invoice_status(session, p)
        items.append(_to_payment_out(p))
    return success(items)


@router.post("")
async def create_payment(
    payload: PaymentCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Group).where(Group.id == payload.group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    payment = await ensure_invoice(session, payload.student_id, group, payload.month, payload.amount_due)
    await log_action(session, user.id, "create_invoice", "payment", payment.id)
    return success(_to_payment_out(payment))


@router.post("/generate-monthly")
async def generate_monthly(
    month: str | None = None,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    created = await generate_monthly_payments(session, month)
    await log_action(session, user.id, "generate_monthly_invoices", "payment", None, {"month": month})
    return success({"created": created, "month": month or datetime.utcnow().strftime("%Y-%m")})


@router.post("/{payment_id}/receipt")
async def upload_receipt(
    payment_id: int,
    amount: int | None = Form(default=None),
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != Role.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can upload receipts")

    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Invoice not found")

    path = await save_upload_file(file, "payments")
    receipt = await create_receipt(session, payment, user.id, amount, path, note)
    await log_action(session, user.id, "upload_receipt", "payment", payment_id)
    return success(ReceiptOut(**receipt.__dict__))


@router.post("/{payment_id}/pay")
async def admin_pay_invoice(
    payment_id: int,
    payload: PaymentTransactionCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        tx = await create_payment_transaction(session, invoice, payload.amount, payload.payment_method, user.id, payload.note)
    except ValueError as e:
        if str(e) == "amount_must_be_positive":
            raise HTTPException(status_code=400, detail="Amount must be positive")
        if str(e) == "invoice_already_paid":
            raise HTTPException(status_code=400, detail="Invoice already paid")
        if str(e) == "amount_exceeds_remaining":
            raise HTTPException(status_code=400, detail="Amount exceeds remaining")
        raise

    await log_action(session, user.id, "create_payment", "payment", invoice.id)
    return success(PaymentTransactionOut(**tx.__dict__))


@router.post("/receipts/{receipt_id}/confirm")
async def confirm_payment_receipt(
    receipt_id: int,
    amount_paid: int = Form(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(PaymentReceipt).where(PaymentReceipt.id == receipt_id))
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    try:
        receipt = await confirm_receipt(session, receipt, user.id, amount_paid)
    except ValueError as e:
        if str(e) == "amount_must_be_positive":
            raise HTTPException(status_code=400, detail="Amount must be positive")
        if str(e) == "amount_exceeds_remaining":
            raise HTTPException(status_code=400, detail="Amount exceeds remaining")
        if str(e) == "invoice_already_paid":
            raise HTTPException(status_code=400, detail="Invoice already paid")
        if str(e) == "receipt_already_rejected":
            raise HTTPException(status_code=400, detail="Receipt already rejected")
        raise
    await log_action(session, user.id, "confirm_payment", "payment_receipt", receipt_id)
    return success(ReceiptOut(**receipt.__dict__))


@router.post("/receipts/{receipt_id}/reject")
async def reject_payment_receipt(
    receipt_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(PaymentReceipt).where(PaymentReceipt.id == receipt_id))
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    receipt = await reject_receipt(session, receipt, user.id)
    await log_action(session, user.id, "reject_payment", "payment_receipt", receipt_id)
    return success(ReceiptOut(**receipt.__dict__))
