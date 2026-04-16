from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.core.permissions import require_roles
from app.utils.enums import Role, MaterialType
from app.models.material import Material, MaterialGroupLink
from app.models.user import User
from app.schemas.material import MaterialOut
from app.utils.responses import success
from app.utils.files import save_upload_file
from app.services.notification_service import create_notification
from app.services.audit_service import log_action

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("")
async def list_materials(
    group_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Material)
    if group_id:
        stmt = stmt.join(MaterialGroupLink, MaterialGroupLink.material_id == Material.id).where(
            MaterialGroupLink.group_id == group_id
        )
    result = await session.execute(stmt)
    materials = result.scalars().all()
    return success([MaterialOut(**m.__dict__) for m in materials])


@router.post("")
async def create_material(
    title: str = Form(...),
    description: str | None = Form(default=None),
    type: MaterialType = Form(...),
    link_url: str | None = Form(default=None),
    group_ids: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    file_path = None
    if type != MaterialType.LINK:
        if not file:
            raise HTTPException(status_code=400, detail="File is required for non-link materials")
        file_path = await save_upload_file(file, "materials")
    else:
        if not link_url:
            raise HTTPException(status_code=400, detail="link_url required for LINK type")

    material = Material(
        title=title,
        description=description,
        type=type,
        file_path=file_path,
        link_url=link_url,
        created_by=user.id,
        is_visible=True,
    )
    session.add(material)
    await session.commit()
    await session.refresh(material)

    if group_ids:
        ids = [int(x) for x in group_ids.split(",") if x.strip()]
        for gid in ids:
            session.add(MaterialGroupLink(material_id=material.id, group_id=gid))
        await session.commit()

    await log_action(session, user.id, "create_material", "material", material.id)
    return success(MaterialOut(**material.__dict__))


@router.post("/{material_id}/send")
async def send_material(
    material_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(Role.SUPER_ADMIN, Role.ADMIN)),
):
    result = await session.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    group_links = await session.execute(
        select(MaterialGroupLink.group_id).where(MaterialGroupLink.material_id == material_id)
    )
    group_ids = [row[0] for row in group_links.all()]

    # Notify all students in those groups
    from app.models.group import StudentGroupEnrollment
    from app.models.user import User as UserModel
    from app.utils.enums import EnrollmentStatus

    for gid in group_ids:
        enrolls = await session.execute(
            select(StudentGroupEnrollment.student_id).where(
                StudentGroupEnrollment.group_id == gid,
                StudentGroupEnrollment.status == EnrollmentStatus.ACTIVE,
            )
        )
        student_ids = [row[0] for row in enrolls.all()]
        for sid in student_ids:
            await create_notification(
                session,
                title="New Material",
                body=f"{material.title}",
                user_id=sid,
            )

    await log_action(session, user.id, "send_material", "material", material_id)
    return success({"sent": True})
