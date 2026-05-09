from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.enums import MaterialType


class MaterialCreate(BaseModel):
    title: str
    description: str | None = None
    type: MaterialType
    link_url: str | None = None
    group_ids: list[int] = []


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    type: MaterialType
    file_path: str | None
    link_url: str | None
    created_by: int
    created_at: datetime
