from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ConversationBase(BaseModel):
    title: str = Field(default="新对话", max_length=200)
    user_id: str
    status: Literal["active", "closed"] = "active"


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=200)
    user_id: str


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    status: Literal["active", "closed"] | None = None


class ConversationOut(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
