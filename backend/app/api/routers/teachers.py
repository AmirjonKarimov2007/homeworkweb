from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.user import User
from app.models.group import Group
from app.schemas.user import UserOut, UserUpdate
from app.core.security import hash_password
from app.utils.pagination import paginate
from app.utils.responses import success
from pydantic import BaseModel, Field, conlist

router = APIRouter(prefix="/teachers", tags=["teachers"])


class TeacherCreate(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    password: str = Field(min_length=6)
    group_ids: conlist(int, min_length=1)


class TeacherUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None


@router.get("")
async def list_teachers(
    search: str | None = None,
    include_inactive: bool = False,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    from app.models.group import Group

    stmt = select(User).where(User.role == Role.TEACHER)
    if not include_inactive:
        stmt = stmt.where(User.is_active == True)
    if search:
        stmt = stmt.where(or_(User.full_name.ilike(f"%{search}%"), User.phone.ilike(f"%{search}%")))
    data = await paginate(session, stmt, page, size)

    # Get groups for each teacher
    teacher_ids = [u.id for u in data["items"]]
    groups_stmt = select(Group).where(Group.primary_teacher_id.in_(teacher_ids))
    groups_result = await session.execute(groups_stmt)
    groups = groups_result.scalars().all()

    # Organize groups by teacher
    teacher_groups = {}
    for group in groups:
        if group.primary_teacher_id not in teacher_groups:
            teacher_groups[group.primary_teacher_id] = []
        teacher_groups[group.primary_teacher_id].append({
            "id": group.id,
            "name": group.name
        })

    return success({
        "items": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "phone": u.phone,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
                "teacher_groups": teacher_groups.get(u.id, [])
            }
            for u in data["items"]
        ],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.post("")
async def create_teacher(
    payload: TeacherCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    from app.models.group import Group

    exists = await session.execute(select(User).where(User.phone == payload.phone))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")
    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=Role.TEACHER,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    group_ids = list(dict.fromkeys(payload.group_ids))
    groups_result = await session.execute(select(Group).where(Group.id.in_(group_ids)))
    groups = groups_result.scalars().all()
    found = {g.id for g in groups}
    if len(found) != len(group_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group ids")

    for group in groups:
        group.primary_teacher_id = user.id
        session.add(group)
    await session.commit()

    # Fetch assigned groups to return
    teacher_groups = [
        {"id": group.id, "name": group.name}
        for group in groups
    ]

    return success({
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "teacher_groups": teacher_groups
    })


@router.delete("/{teacher_id}")
async def delete_teacher(
    teacher_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == teacher_id, User.role == Role.TEACHER))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")

    user.is_active = False
    session.add(user)

    group_result = await session.execute(select(Group).where(Group.primary_teacher_id == teacher_id))
    for group in group_result.scalars().all():
        group.primary_teacher_id = None
        session.add(group)

    await session.commit()
    return success(message="Teacher deleted")


@router.get("/{teacher_id}")
async def get_teacher(
    teacher_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    from app.models.group import Group

    result = await session.execute(select(User).where(User.id == teacher_id, User.role == Role.TEACHER))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Get groups for this teacher
    groups_result = await session.execute(select(Group).where(Group.primary_teacher_id == teacher_id))
    groups = groups_result.scalars().all()

    teacher_groups = [
        {"id": group.id, "name": group.name}
        for group in groups
    ]

    return success({
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "teacher_groups": teacher_groups
    })


@router.patch("/{teacher_id}")
async def update_teacher(
    teacher_id: int,
    payload: TeacherUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == teacher_id, User.role == Role.TEACHER))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Only SUPER_ADMIN can change password and is_active
    if current_user.role != Role.SUPER_ADMIN and (payload.password is not None or payload.is_active is not None):
        raise HTTPException(status_code=403, detail="Only super admin can change password or active status")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "password" and value:
            setattr(user, "hashed_password", hash_password(value))
        elif field != "password":
            setattr(user, field, value)

    session.add(user)
    await session.commit()

    # Get groups for this teacher
    groups_result = await session.execute(select(Group).where(Group.primary_teacher_id == teacher_id))
    groups = groups_result.scalars().all()

    teacher_groups = [
        {"id": group.id, "name": group.name}
        for group in groups
    ]

    return success({
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "teacher_groups": teacher_groups
    })


@router.patch("/{teacher_id}/groups")
async def update_teacher_groups(
    teacher_id: int,
    group_ids: list[int],
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == teacher_id, User.role == Role.TEACHER))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if not group_ids:
        raise HTTPException(status_code=400, detail="At least one group is required")

    # Get all groups with this teacher
    groups_result = await session.execute(select(Group).where(Group.primary_teacher_id == teacher_id))
    existing_groups = groups_result.scalars().all()
    existing_group_ids = {g.id for g in existing_groups}

    # Get selected groups
    selected_groups_result = await session.execute(select(Group).where(Group.id.in_(group_ids)))
    selected_groups = selected_groups_result.scalars().all()

    # Remove teacher from groups not in the new list
    for group in existing_groups:
        if group.id not in group_ids:
            group.primary_teacher_id = None
            session.add(group)

    # Add teacher to new groups
    found = {g.id for g in selected_groups}
    if len(found) != len(group_ids):
        raise HTTPException(status_code=400, detail="Invalid group ids")

    for group in selected_groups:
        if group.id not in existing_group_ids:
            group.primary_teacher_id = user.id
            session.add(group)

    await session.commit()
    return success(message="Teacher groups updated")
