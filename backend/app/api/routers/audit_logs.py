from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.audit_log import AuditLog
from app.utils.responses import success

router = APIRouter(prefix="/audit-logs", tags=["audit_logs"])


@router.get("")
async def list_audit_logs(
    page: int = 1,
    size: int = 50,
    session: AsyncSession = Depends(get_db),
    _: object = Depends(require_roles(Role.SUPER_ADMIN)),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(size).offset((page - 1) * size)
    result = await session.execute(stmt)
    logs = result.scalars().all()
    return success([{
        "id": l.id,
        "user_id": l.user_id,
        "action": l.action,
        "entity_type": l.entity_type,
        "entity_id": l.entity_id,
        "meta": l.meta,
        "created_at": l.created_at,
    } for l in logs])
