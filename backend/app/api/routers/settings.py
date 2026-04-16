from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.system_setting import SystemSetting
from app.utils.responses import success

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingPayload(BaseModel):
    key: str
    value: str | None = None


@router.get("")
async def list_settings(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(SystemSetting))
    items = result.scalars().all()
    return success([{ "key": s.key, "value": s.value } for s in items])


@router.post("")
async def set_setting(
    payload: SettingPayload,
    session: AsyncSession = Depends(get_db),
    _: object = Depends(require_roles(Role.SUPER_ADMIN)),
):
    result = await session.execute(select(SystemSetting).where(SystemSetting.key == payload.key))
    setting = result.scalar_one_or_none()
    if not setting:
        setting = SystemSetting(key=payload.key, value=payload.value)
    else:
        setting.value = payload.value
    session.add(setting)
    await session.commit()
    return success({"key": setting.key, "value": setting.value})
