from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role, EnrollmentStatus
from app.models.group import Group, StudentGroupEnrollment
from app.models.user import User
from app.schemas.group import GroupCreate, GroupOut, GroupUpdate, EnrollmentCreate, EnrollmentOut
from app.utils.pagination import paginate
from app.utils.responses import success
from app.services.audit_service import log_action
from app.services.payment_service import ensure_invoice

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("")
async def list_groups(
    search: str | None = None,
    active: bool | None = None,
    include_inactive: bool = False,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    from app.models.course import Course
    from app.schemas.group import CourseInfo

    stmt = select(Group)
    if search:
        stmt = stmt.where(Group.name.ilike(f"%{search}%"))
    if active is not None:
        stmt = stmt.where(Group.is_active == active)
    elif not include_inactive:
        stmt = stmt.where(Group.is_active == True)

    data = await paginate(session, stmt, page, size)

    # Fetch courses for groups
    group_ids = [g.id for g in data["items"]]
    courses_result = await session.execute(
        select(Course.id, Course.name, Course.monthly_fee, Course.duration_months).where(Course.id.in_([g.course_id for g in data["items"]]))
    )
    courses_by_id = {c[0]: CourseInfo(id=c[0], name=c[1], monthly_fee=c[2], duration_months=c[3]) for c in courses_result.all()}

    items = []
    for g in data["items"]:
        group_dict = g.__dict__.copy()
        group_dict["course"] = courses_by_id.get(g.course_id)
        items.append(GroupOut(**group_dict))

    return success({
        "items": items,
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.get("/mine")
async def my_groups(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.course import Course
    from app.schemas.group import CourseInfo

    if user.role == Role.TEACHER:
        result = await session.execute(select(Group).where(Group.primary_teacher_id == user.id))
        groups = result.scalars().all()
    elif user.role == Role.STUDENT:
        result = await session.execute(
            select(Group)
            .join(StudentGroupEnrollment, StudentGroupEnrollment.group_id == Group.id)
            .where(StudentGroupEnrollment.student_id == user.id)
        )
        groups = result.scalars().all()
    else:
        result = await session.execute(select(Group))
        groups = result.scalars().all()

    # Fetch courses for groups
    course_ids = [g.course_id for g in groups if g.course_id]
    courses_by_id = {}
    if course_ids:
        courses_result = await session.execute(
            select(Course.id, Course.name, Course.monthly_fee, Course.duration_months).where(Course.id.in_(course_ids))
        )
        courses_by_id = {c[0]: CourseInfo(id=c[0], name=c[1], monthly_fee=c[2], duration_months=c[3]) for c in courses_result.all()}

    items = []
    for g in groups:
        group_dict = g.__dict__.copy()
        group_dict["course"] = courses_by_id.get(g.course_id)
        items.append(GroupOut(**group_dict))

    return success(items)


@router.post("")
async def create_group(
    payload: GroupCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    if not payload.course_id:
        raise HTTPException(status_code=400, detail="course_id is required")
    if payload.start_date is None or payload.end_date is None or payload.duration_months is None:
        raise HTTPException(status_code=400, detail="start_date, end_date, duration_months required")
    if payload.payment_day < 1 or payload.payment_day > 31:
        raise HTTPException(status_code=400, detail="payment_day must be between 1 and 31")
    if payload.grace_days < 0:
        raise HTTPException(status_code=400, detail="grace_days must be >= 0")

    # Verify course exists
    from app.models.course import Course
    course_result = await session.execute(select(Course).where(Course.id == payload.course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")

    # Auto-fill from course if not provided
    if not payload.monthly_fee and course.monthly_fee:
        payload.monthly_fee = course.monthly_fee
    if not payload.duration_months and course.duration_months:
        payload.duration_months = course.duration_months

    group = Group(**payload.model_dump())
    session.add(group)
    await session.commit()
    await session.refresh(group)
    await log_action(session, user.id, "create_group", "group", group.id)
    return success(GroupOut(**group.__dict__))


@router.get("/{group_id}")
async def get_group(
    group_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.course import Course
    from app.schemas.group import CourseInfo

    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if user.role == Role.TEACHER and group.primary_teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if user.role == Role.STUDENT:
        enr = await session.execute(
            select(StudentGroupEnrollment).where(
                StudentGroupEnrollment.group_id == group_id,
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        if not enr.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Forbidden")

    # Fetch course info
    course = None
    if group.course_id:
        course_result = await session.execute(select(Course).where(Course.id == group.course_id))
        course_obj = course_result.scalar_one_or_none()
        if course_obj:
            course = CourseInfo(id=course_obj.id, name=course_obj.name, monthly_fee=course_obj.monthly_fee, duration_months=course_obj.duration_months)

    group_dict = group.__dict__.copy()
    group_dict["course"] = course
    return success(GroupOut(**group_dict))


@router.patch("/{group_id}")
async def update_group(
    group_id: int,
    payload: GroupUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    data = payload.model_dump(exclude_unset=True)
    if "payment_day" in data and (data["payment_day"] < 1 or data["payment_day"] > 31):
        raise HTTPException(status_code=400, detail="payment_day must be between 1 and 31")
    if "grace_days" in data and data["grace_days"] < 0:
        raise HTTPException(status_code=400, detail="grace_days must be >= 0")
    for field, value in data.items():
        setattr(group, field, value)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    await log_action(session, user.id, "update_group", "group", group.id)
    return success(GroupOut(**group.__dict__))


@router.post("/{group_id}/enroll")
async def enroll_student(
    group_id: int,
    payload: EnrollmentCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    if payload.group_id != group_id:
        raise HTTPException(status_code=400, detail="Group id mismatch")
    existing = await session.execute(
        select(StudentGroupEnrollment).where(
            StudentGroupEnrollment.group_id == group_id,
            StudentGroupEnrollment.student_id == payload.student_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Student already enrolled")
    enrollment = StudentGroupEnrollment(
        student_id=payload.student_id,
        group_id=group_id,
        monthly_fee=payload.monthly_fee,
        status=EnrollmentStatus.ACTIVE,
    )
    session.add(enrollment)
    await session.commit()
    await session.refresh(enrollment)
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group and group.is_payment_required:
        await ensure_invoice(session, payload.student_id, group, amount_due=payload.monthly_fee)
    await log_action(session, user.id, "assign_group", "group", group_id, {"student_id": payload.student_id})
    return success(EnrollmentOut(**enrollment.__dict__))


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    group.is_active = False
    session.add(group)

    enrollments = await session.execute(
        select(StudentGroupEnrollment).where(StudentGroupEnrollment.group_id == group_id)
    )
    for enr in enrollments.scalars().all():
        enr.status = EnrollmentStatus.INACTIVE
        session.add(enr)

    await session.commit()
    return success(message="Group deleted")


@router.get("/{group_id}/students")
async def group_students(
    group_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == Role.TEACHER:
        grp = await session.execute(select(Group).where(Group.id == group_id))
        group = grp.scalar_one_or_none()
        if not group or group.primary_teacher_id != user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

    result = await session.execute(
        select(User)
        .join(StudentGroupEnrollment, StudentGroupEnrollment.student_id == User.id)
        .where(StudentGroupEnrollment.group_id == group_id)
    )
    students = result.scalars().all()
    return success([
        {"id": s.id, "full_name": s.full_name, "phone": s.phone, "email": s.email}
        for s in students
    ])


@router.get("/{group_id}/enrollment")
async def check_enrollment(
    group_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check if current user is enrolled in the group"""
    if user.role == Role.STUDENT:
        result = await session.execute(
            select(StudentGroupEnrollment)
            .where(
                StudentGroupEnrollment.group_id == group_id,
                StudentGroupEnrollment.student_id == user.id,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        is_enrolled = result.scalar_one_or_none() is not None
        return success({"is_enrolled": is_enrolled, "user_id": user.id, "group_id": group_id})
    else:
        # For teachers and admins, they can access any group
        return success({"is_enrolled": True, "user_id": user.id, "group_id": group_id})
