from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db
from app.core.permissions import require_roles
from app.utils.enums import Role
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate, CourseOut
from app.utils.pagination import paginate
from app.utils.responses import success
from app.services.audit_service import log_action

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
async def list_courses(
    search: str | None = None,
    active: bool | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    stmt = select(Course)
    if search:
        stmt = stmt.where(Course.name.ilike(f"%{search}%"))
    if active is not None:
        stmt = stmt.where(Course.is_active == active)
    data = await paginate(session, stmt, page, size)
    return success({
        "items": [CourseOut(**c.__dict__) for c in data["items"]],
        "total": data["total"],
        "page": data["page"],
        "size": data["size"],
    })


@router.get("/active")
async def list_active_courses(
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(Course).where(Course.is_active == True))
    courses = result.scalars().all()
    return success([CourseOut(**c.__dict__) for c in courses])


@router.post("")
async def create_course(
    payload: CourseCreate,
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    course = Course(**payload.model_dump())
    session.add(course)
    await session.commit()
    await session.refresh(course)
    await log_action(session, user.id, "create_course", "course", course.id)
    return success(CourseOut(**course.__dict__))


@router.get("/{course_id}")
async def get_course(
    course_id: int,
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN, Role.TEACHER)),
):
    result = await session.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")
    return success(CourseOut(**course.__dict__))


@router.patch("/{course_id}")
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(course, field, value)
    session.add(course)
    await session.commit()
    await session.refresh(course)
    await log_action(session, user.id, "update_course", "course", course.id)
    return success(CourseOut(**course.__dict__))


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_db),
    user=Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Kurs topilmadi")
    course.is_active = False
    session.add(course)
    await session.commit()
    await log_action(session, user.id, "delete_course", "course", course_id)
    return success(message="Kurs o'chirildi")
