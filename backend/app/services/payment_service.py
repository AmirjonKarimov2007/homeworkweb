from datetime import datetime, date, timedelta
import calendar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.payment import Payment, PaymentReceipt, PaymentTransaction
from app.models.group import StudentGroupEnrollment, Group
from app.utils.enums import PaymentStatus, PaymentReceiptStatus, EnrollmentStatus, PaymentMethod


def _compute_due_date(year: int, month: int, payment_day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    day = payment_day if payment_day <= last_day else last_day
    return date(year, month, day)


def calculate_status(amount_due: int, amount_paid: int, due_date: date) -> PaymentStatus:
    today = date.today()

    if amount_due <= 0:
        return PaymentStatus.PAID
    if amount_paid >= amount_due:
        return PaymentStatus.PAID
    if amount_paid > 0:
        return PaymentStatus.PARTIAL

    # Muddat o'tganmi?
    if today > due_date:
        return PaymentStatus.OVERDUE

    return PaymentStatus.UNPAID


def _month_str(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


async def ensure_invoice(
    session: AsyncSession,
    student_id: int,
    group: Group,
    month: str | None = None,
    amount_due: int | None = None,
) -> Payment:
    if not month:
        now = datetime.utcnow()
        year, mon = now.year, now.month
        month = _month_str(year, mon)
    else:
        year, mon = map(int, month.split("-"))

    result = await session.execute(
        select(Payment).where(
            Payment.student_id == student_id,
            Payment.group_id == group.id,
            Payment.billing_year == year,
            Payment.billing_month == mon,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    due_date = _compute_due_date(year, mon, group.payment_day or 5)
    amount_due = amount_due if amount_due is not None else (group.monthly_fee or 0)
    status = calculate_status(amount_due, 0, due_date)

    payment = Payment(
        student_id=student_id,
        group_id=group.id,
        month=month,
        billing_year=year,
        billing_month=mon,
        amount_due=amount_due,
        amount_paid=0,
        status=status,
        due_date=due_date,
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def generate_monthly_payments(
    session: AsyncSession,
    month: str | None = None,
) -> int:
    month = month or datetime.utcnow().strftime("%Y-%m")
    year, mon = map(int, month.split("-"))

    result = await session.execute(
        select(StudentGroupEnrollment, Group)
        .join(Group, StudentGroupEnrollment.group_id == Group.id)
        .where(StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE)
    )
    created = 0
    for enrollment, group in result.all():
        if not group.is_payment_required:
            continue
        amount_due = enrollment.monthly_fee if enrollment.monthly_fee is not None else (group.monthly_fee or 0)
        if amount_due <= 0:
            continue
        exists = await session.execute(
            select(Payment.id).where(
                Payment.student_id == enrollment.student_id,
                Payment.group_id == enrollment.group_id,
                Payment.billing_year == year,
                Payment.billing_month == mon,
            )
        )
        if exists.scalar_one_or_none():
            continue
        due_date = _compute_due_date(year, mon, group.payment_day or 5)
        payment = Payment(
            student_id=enrollment.student_id,
            group_id=enrollment.group_id,
            month=month,
            billing_year=year,
            billing_month=mon,
            amount_due=amount_due,
            amount_paid=0,
            status=calculate_status(amount_due, 0, due_date),
            due_date=due_date,
        )
        session.add(payment)
        created += 1
    if created:
        await session.commit()
    return created


async def ensure_student_monthly_payments(
    session: AsyncSession,
    student_id: int,
    month: str | None = None,
) -> None:
    month = month or datetime.utcnow().strftime("%Y-%m")
    year, mon = map(int, month.split("-"))

    result = await session.execute(
        select(StudentGroupEnrollment, Group)
        .join(Group, StudentGroupEnrollment.group_id == Group.id)
        .where(
            StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            StudentGroupEnrollment.student_id == student_id,
        )
    )
    created = False
    for enrollment, group in result.all():
        if not group.is_payment_required:
            continue
        amount_due = enrollment.monthly_fee if enrollment.monthly_fee is not None else (group.monthly_fee or 0)
        if amount_due <= 0:
            continue
        exists = await session.execute(
            select(Payment.id).where(
                Payment.student_id == enrollment.student_id,
                Payment.group_id == enrollment.group_id,
                Payment.billing_year == year,
                Payment.billing_month == mon,
            )
        )
        if exists.scalar_one_or_none():
            continue
        due_date = _compute_due_date(year, mon, group.payment_day or 5)
        payment = Payment(
            student_id=enrollment.student_id,
            group_id=enrollment.group_id,
            month=month,
            billing_year=year,
            billing_month=mon,
            amount_due=amount_due,
            amount_paid=0,
            status=calculate_status(amount_due, 0, due_date),
            due_date=due_date,
        )
        session.add(payment)
        created = True
    if created:
        await session.commit()


async def create_receipt(
    session: AsyncSession,
    payment: Payment,
    student_id: int,
    amount: int | None,
    receipt_path: str,
    note: str | None = None,
) -> PaymentReceipt:
    receipt = PaymentReceipt(
        payment_id=payment.id,
        student_id=student_id,
        amount=amount,
        receipt_path=receipt_path,
        note=note,
        status=PaymentReceiptStatus.PENDING_REVIEW,
    )
    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    return receipt


async def create_payment_transaction(
    session: AsyncSession,
    invoice: Payment,
    amount: int,
    method: PaymentMethod,
    admin_id: int,
    note: str | None = None,
) -> PaymentTransaction:
    if amount <= 0:
        raise ValueError("amount_must_be_positive")
    remaining = max(invoice.amount_due - invoice.amount_paid, 0)
    if remaining <= 0:
        raise ValueError("invoice_already_paid")
    if amount > remaining:
        raise ValueError("amount_exceeds_remaining")

    tx = PaymentTransaction(
        invoice_id=invoice.id,
        student_id=invoice.student_id,
        group_id=invoice.group_id,
        amount=amount,
        payment_method=method,
        confirmed_by_admin_id=admin_id,
        note=note,
    )
    session.add(tx)

    invoice.amount_paid += amount
    invoice.status = calculate_status(invoice.amount_due, invoice.amount_paid, invoice.due_date)
    session.add(invoice)

    await session.commit()
    await session.refresh(tx)
    return tx


async def confirm_receipt(
    session: AsyncSession,
    receipt: PaymentReceipt,
    reviewer_id: int,
    amount_paid: int,
) -> PaymentReceipt:
    if receipt.status == PaymentReceiptStatus.CONFIRMED:
        return receipt
    if receipt.status == PaymentReceiptStatus.REJECTED:
        raise ValueError("receipt_already_rejected")
    if amount_paid <= 0:
        raise ValueError("amount_must_be_positive")

    receipt.status = PaymentReceiptStatus.CONFIRMED
    receipt.reviewed_by = reviewer_id
    receipt.reviewed_at = datetime.utcnow()

    payment_result = await session.execute(select(Payment).where(Payment.id == receipt.payment_id))
    payment = payment_result.scalar_one_or_none()
    if payment:
        remaining = max(payment.amount_due - payment.amount_paid, 0)
        if remaining > 0:
            await create_payment_transaction(
                session,
                payment,
                amount_paid,
                PaymentMethod.TRANSFER,
                reviewer_id,
                note=receipt.note,
            )

    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    return receipt


async def reject_receipt(session: AsyncSession, receipt: PaymentReceipt, reviewer_id: int) -> PaymentReceipt:
    receipt.status = PaymentReceiptStatus.REJECTED
    receipt.reviewed_by = reviewer_id
    receipt.reviewed_at = datetime.utcnow()
    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    return receipt


async def refresh_invoice_status(session: AsyncSession, invoice: Payment) -> Payment:
    due_date = invoice.due_date or date.today()
    new_status = calculate_status(invoice.amount_due, invoice.amount_paid, due_date)
    if invoice.status != new_status:
        invoice.status = new_status
        if invoice.due_date is None:
            invoice.due_date = due_date
        session.add(invoice)
        await session.commit()
        await session.refresh(invoice)
    return invoice


async def can_student_access_new_lessons(
    session: AsyncSession,
    student_id: int,
    group_id: int,
) -> bool:
    group_result = await session.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if not group or not group.is_payment_required:
        return True

    invoice_result = await session.execute(
        select(Payment)
        .where(Payment.student_id == student_id, Payment.group_id == group_id)
        .order_by(Payment.billing_year.desc(), Payment.billing_month.desc())
        .limit(1)
    )
    invoice = invoice_result.scalar_one_or_none()
    if not invoice:
        return True

    await refresh_invoice_status(session, invoice)
    if invoice.status == PaymentStatus.PAID:
        return True

    grace = 0
    due_with_grace = invoice.due_date + timedelta(days=grace)
    today = date.today()
    if today <= due_with_grace:
        return True
    return False
