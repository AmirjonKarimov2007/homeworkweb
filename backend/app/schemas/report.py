from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_students: int
    active_groups: int
    today_attendance: int
    pending_homework: int
    pending_payments: int
    pending_payments_count: int = 0
    monthly_income: int
    debtors_count: int
    new_leads_this_month: int
