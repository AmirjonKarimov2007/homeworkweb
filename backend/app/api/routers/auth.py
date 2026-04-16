from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.services.auth_service import authenticate_user
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, ForgotPasswordRequest
from app.schemas.user import UserOut
from app.utils.responses import success
from jose import JWTError
from sqlalchemy import select
from app.models.user import User
from app.models.group import StudentGroupEnrollment
from app.utils.enums import Role, EnrollmentStatus
from app.core.rate_limit import limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limit("10/minute")
async def login(request: Request, payload: LoginRequest, session: AsyncSession = Depends(get_db)):
    user = await authenticate_user(session, payload.login, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.role == Role.STUDENT:
        result = await session.execute(
            select(StudentGroupEnrollment).where(
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if not result.scalars().first():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Guruh biriktirilmagan")
    access = create_access_token(str(user.id), {"role": user.role})
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserOut(
            id=user.id,
            full_name=user.full_name,
            phone=user.phone,
            email=user.email,
            avatar_path=user.avatar_path,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
    )


@router.post("/refresh")
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        data = decode_refresh_token(payload.refresh_token)
        user_id = int(data.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not active")

    access = create_access_token(str(user.id), {"role": user.role})
    return success({"access_token": access, "token_type": "bearer"})


@router.post("/forgot-password")
async def forgot_password(_: ForgotPasswordRequest):
    return success(message="Password reset request received. Admin will contact you.")
