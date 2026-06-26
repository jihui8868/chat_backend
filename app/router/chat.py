from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import crud
from app.schemas.message import MessageCreate, MessageOut
from app.agents import agent_main

router = APIRouter(prefix="/conversations", tags=["chat"])


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


@router.post("/{conv_id}/chat", response_model=ChatResponse)
async def chat(conv_id: str, body: ChatRequest, db: Session = Depends(get_db)):
    conv = crud.conversation.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    user_msg = crud.message.create(db, conv_id, MessageCreate(type="user", content=body.content))

    try:
        reply_content = await agent_main.chat(conv_id, body.content, db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI 回复失败: {e}")

    assistant_msg = crud.message.create(db, conv_id, MessageCreate(type="assistant", content=reply_content))

    return ChatResponse(
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(assistant_msg),
    )
