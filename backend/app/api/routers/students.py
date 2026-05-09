from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role, EnrollmentStatus
from app.models.user import User
from app.models.group import Group, StudentGroupEnrollment
from app.schemas.user import UserOut, UserUpdate
from app.core.security import hash_password
from app.utils.pagination import paginate
from app.utils.responses import success
from app.services.payment_service import ensure_invoice
from pydantic import BaseModel, Field, conlist

router = APIRouter(prefix="/students", tags=["students"])


class StudentCreate(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    password: str = Field(min_length=6)
    group_ids: conlist(int, min_length=1)


class StudentGroupsUpdate(BaseModel):
    group_ids: list[int] = Field(default_factory=list)


@router.get("")
async def list_students(
    search: str | None = None,
    include_inactive: bool = False,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(User).where(User.role == Role.STUDENT)
    if not include_inactive:
        stmt = stmt.where(User.is_active == True)
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
async def create_student(
    payload: StudentCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    exists = await session.execute(select(User).where(User.phone == payload.phone))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")

    group_ids = list(dict.fromkeys(payload.group_ids))
    groups_result = await session.execute(select(Group).where(Group.id.in_(group_ids)))
    groups = groups_result.scalars().all()
    found = {g.id for g in groups}
    if len(found) != len(group_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group ids")

    user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=Role.STUDENT,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    group_map = {g.id: g for g in groups}
    enrollments = []
    for gid in group_ids:
        fee = group_map.get(gid).monthly_fee if group_map.get(gid) else None
        enrollments.append(StudentGroupEnrollment(
            student_id=user.id,
            group_id=gid,
            monthly_fee=fee,
            status=EnrollmentStatus.ACTIVE,
        ))
    session.add_all(enrollments)
    await session.commit()

    for group in groups:
        if group.is_payment_required:
            await ensure_invoice(session, user.id, group)

    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.get("/{student_id}")
async def get_student(
    student_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(User).where(User.id == student_id, User.role == Role.STUDENT))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.patch("/{student_id}")
async def update_student(
    student_id: int,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == student_id, User.role == Role.STUDENT))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "password" and value:
            setattr(user, "hashed_password", hash_password(value))
        elif field != "password":
            setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return success(UserOut(
        id=user.id,
        full_name=user.full_name,
        phone=user.phone,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    ))


@router.get("/{student_id}/groups")
async def get_student_groups(
    student_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(
        select(Group, StudentGroupEnrollment)
        .join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Group.id)
        .where(StudentGroupEnrollment.student_id == student_id)
    )
    rows = result.all()
    data = [
        {
            "group_id": g.id,
            "group_name": g.name,
            "status": enr.status,
        }
        for g, enr in rows
    ]
    return success(data)


@router.put("/{student_id}/groups")
async def update_student_groups(
    student_id: int,
    payload: StudentGroupsUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    # Ensure student exists
    result = await session.execute(select(User).where(User.id == student_id, User.role == Role.STUDENT))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")

    group_ids = list(dict.fromkeys(payload.group_ids))
    if group_ids:
        groups_result = await session.execute(select(Group).where(Group.id.in_(group_ids)))
        groups = groups_result.scalars().all()
        found = {g.id for g in groups}
        if len(found) != len(group_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group ids")
    else:
        groups = []

    existing_result = await session.execute(
        select(StudentGroupEnrollment).where(StudentGroupEnrollment.student_id == student_id)
    )
    existing = existing_result.scalars().all()
    existing_map = {e.group_id: e for e in existing}

    # Activate or create
    for gid in group_ids:
        if gid in existing_map:
            existing_map[gid].status = EnrollmentStatus.ACTIVE
            session.add(existing_map[gid])
        else:
            fee = None
            for g in groups:
                if g.id == gid:
                    fee = g.monthly_fee
                    break
            session.add(StudentGroupEnrollment(student_id=student_id, group_id=gid, monthly_fee=fee, status=EnrollmentStatus.ACTIVE))

    await session.commit()

    # Create invoices for newly added groups
    if groups:
        for group in groups:
            if group.is_payment_required:
                await ensure_invoice(session, student_id, group)

    # Deactivate removed
    for gid, enr in existing_map.items():
        if gid not in group_ids:
            enr.status = EnrollmentStatus.INACTIVE
            session.add(enr)

    await session.commit()
    return success(message="Student groups updated")


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(User).where(User.id == student_id, User.role == Role.STUDENT))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    user.is_active = False
    session.add(user)

    enroll_result = await session.execute(
        select(StudentGroupEnrollment).where(StudentGroupEnrollment.student_id == student_id)
    )
    for enr in enroll_result.scalars().all():
        enr.status = EnrollmentStatus.INACTIVE
        session.add(enr)

    await session.commit()
    return success(message="Student deleted")
