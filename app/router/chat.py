import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app import crud
from app.schemas.message import MessageCreate, MessageOut
from app.agents import agent_main

router = APIRouter(prefix="/conversations", tags=["chat"])


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


def _msg_dict(msg) -> dict:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "type": msg.type,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{conv_id}/chat", response_model=ChatResponse)
async def chat(conv_id: str, body: ChatRequest, db: Session = Depends(get_db)):
    conv = crud.conversation.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    prior = agent_main.load_history(conv_id, db)
    user_msg = crud.message.create(db, conv_id, MessageCreate(type="user", content=body.content))

    try:
        reply_content = await agent_main.chat(conv_id, body.content, prior)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI 回复失败: {e}")

    assistant_msg = crud.message.create(db, conv_id, MessageCreate(type="assistant", content=reply_content))

    return ChatResponse(
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(assistant_msg),
    )


@router.post("/{conv_id}/chat/stream")
async def chat_stream(conv_id: str, body: ChatRequest, db: Session = Depends(get_db)):
    conv = crud.conversation.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    # Load history before saving user message to avoid duplication
    prior = agent_main.load_history(conv_id, db)
    content = body.content

    async def generate():
        gen_db = SessionLocal()
        try:
            user_msg = crud.message.create(gen_db, conv_id, MessageCreate(type="user", content=content))
            yield _sse({"type": "user_message", "message": _msg_dict(user_msg)})

            full_content = ""
            async for chunk in agent_main.agent_stream(conv_id, content, prior):
                full_content += chunk
                yield _sse({"type": "chunk", "content": chunk})

            assistant_msg = crud.message.create(
                gen_db, conv_id, MessageCreate(type="assistant", content=full_content)
            )
            yield _sse({"type": "done", "message": _msg_dict(assistant_msg)})
        except Exception as e:
            yield _sse({"type": "error", "detail": str(e)})
        finally:
            gen_db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
