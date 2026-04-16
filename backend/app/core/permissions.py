from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.utils.enums import Role
from app.models.user import User


def require_roles(*roles: Role):
    async def _role_dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _role_dep
