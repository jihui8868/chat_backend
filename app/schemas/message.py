from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    conversation_id: str
    type: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class MessageCreate(BaseModel):
    type: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1)


class MessageOut(MessageBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
