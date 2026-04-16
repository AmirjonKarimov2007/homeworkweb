from sqlalchemy import String, Text, DateTime, func, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.utils.enums import MaterialType


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[MaterialType] = mapped_column(Enum(MaterialType))
    file_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    link_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaterialGroupLink(Base):
    __tablename__ = "material_group_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
