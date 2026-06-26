from datetime import datetime

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: str | None = None
    description: str | None = Field(None, max_length=500)
    sort_order: int = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    parent_id: str | None = None
    description: str | None = Field(None, max_length=500)
    sort_order: int | None = None


class DepartmentOut(DepartmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DepartmentTree(DepartmentOut):
    children: list["DepartmentTree"] = []
