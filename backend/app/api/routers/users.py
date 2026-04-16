from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from pydantic import BaseModel, Field
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.core.security import hash_password
from app.utils.pagination import paginate
from app.utils.responses import success
from app.utils.files import save_upload_file

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    password: str | None = Field(default=None, min_length=6)


@router.get("")
async def list_users(
    role: Role | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if search:
        stmt = stmt.where(or_(User.full_name.ilike(f"%{search}%"), User.phone.ilike(f"%{search}%")))
    data = await paginate(session, stmt, page, size)
    return success({
        "items": [
            UserOut(
                id=u.id,
                full_name=u.full_name,
                phone=u.phone,
                email=u.email,
                avatar_path=u.avatar_path,
                role=u.role,
                is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in data["items"]
        ],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.post("")
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    exists = await session.execute(select(User).where(User.phone == payload.phone))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")
    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=payload.role,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        avatar_path=user.avatar_path,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),
):
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        avatar_path=user.avatar_path,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.patch("/me")
async def update_me(
    payload: ProfileUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)

    if user.role == Role.STUDENT:
        blocked = {"phone", "email", "password"}
        if any(k in data for k in blocked):
            raise HTTPException(status_code=403, detail="Students cannot change phone, email, or password")

    if "phone" in data and data["phone"] and data["phone"] != user.phone:
        exists = await session.execute(select(User).where(User.phone == data["phone"]))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")
        user.phone = data["phone"]

    if "email" in data and data["email"] and data["email"] != user.email:
        exists = await session.execute(select(User).where(User.email == data["email"]))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        user.email = data["email"]

    if "full_name" in data and data["full_name"]:
        user.full_name = data["full_name"]

    if "password" in data and data["password"]:
        if user.role == Role.STUDENT:
            raise HTTPException(status_code=403, detail="Students cannot change password")
        user.hashed_password = hash_password(data["password"])

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        avatar_path=user.avatar_path,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    path = await save_upload_file(
        file,
        "avatars",
        allowed_types=["image/png", "image/jpeg", "image/jpg", "image/webp"],
    )
    user.avatar_path = path
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return success({"avatar_path": user.avatar_path})


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        avatar_path=user.avatar_path,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.patch("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        avatar_path=user.avatar_path,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))
