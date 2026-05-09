from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.utils.enums import Role


class UserBase(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None
    avatar_path: str | None = None
    role: Role
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    full_name: str
    phone: str
    email: str | None = None
    password: str = Field(min_length=6)
    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
